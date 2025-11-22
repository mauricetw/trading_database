# --- FILE: routers/orders.py ---
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload, contains_eager
from typing import List, Optional
from datetime import datetime

# 來自 SQLAlchemy 的 flag_modified，用於更新 JSON 欄位
from sqlalchemy.orm.attributes import flag_modified

from database.db import get_db
from models.user import User
from models.product import Product
from models.address import Address
from models.order import Order, OrderItem
from schemas.order_schema import OrderResponse, SellerOrderStatusUpdate
from models.user_interactions import CartItem
from schemas.order_schema import OrderCreate, OrderResponse
from utils.token import get_current_user

router_orders = APIRouter(
    prefix="/orders",
    tags=["訂單 (Orders)"]
)

# ... (get_my_orders 和 get_order_details 函式保持不變) ...
@router_orders.get("", response_model=List[OrderResponse])
def get_my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """獲取當前登入使用者的所有訂單列表。"""
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .options(
            joinedload(Order.items).joinedload(OrderItem.product)
        )
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders

@router_orders.get("/{order_id}", response_model=OrderResponse)
def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取單一訂單的詳細資訊，包含商品和狀態歷史。
    - 只有訂單的擁有者才能查看。
    """
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .options(
            joinedload(Order.items).joinedload(OrderItem.product)
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="找不到訂單或您沒有權限查看")
    return order


@router_orders.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. 檢查地址 (不需要鎖定)
    address = db.query(Address).filter(Address.id == order_data.address_id, Address.user_id == current_user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="找不到指定的地址或地址不屬於您")

    # --- [BUG 修正：防止超賣] ---

    # 2. 找出所有購物車中的商品 ID
    cart_items_query = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.id.in_(order_data.cart_item_ids)
    )
    cart_items = cart_items_query.all()
    
    if not cart_items or len(cart_items) != len(order_data.cart_item_ids):
        raise HTTPException(status_code=404, detail="購物車項目不匹配或找不到")

    product_ids_to_lock = [item.product_id for item in cart_items]

    # 3. [關鍵] 鎖定商品：
    #    在 "事務 (Transaction)" 中鎖定所有相關商品，防止其他請求同時修改它們。
    #    with_for_update() 會鎖定這些資料列，直到 db.commit()
    try:
        locked_products = db.query(Product).filter(
            Product.id.in_(product_ids_to_lock)
        ).with_for_update().all()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"鎖定商品庫存時發生錯誤: {e}")

    locked_product_map = {p.id: p for p in locked_products}

    # 4. 在鎖定狀態下，安全地檢查庫存並計算總價
    items_subtotal = 0
    for item in cart_items:
        locked_product = locked_product_map.get(item.product_id)
        if not locked_product:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"找不到商品 ID: {item.product_id}")

        if item.quantity > locked_product.stock_quantity:
            db.rollback() # 釋放鎖
            raise HTTPException(status_code=400, detail=f"商品 '{locked_product.name}' 庫存不足 (可能剛被搶購)")
        
        items_subtotal += item.quantity * locked_product.price

    # 5. 建立訂單 (此時商品仍被鎖定)
    shipping_cost = 60.0 
    discount = 0.0
    total_amount = items_subtotal + shipping_cost - discount

    initial_status_history = [{
        "status": "pending",
        "timestamp": datetime.utcnow().isoformat(),
        "description": "訂單已建立，正在等待賣家確認。"
    }]

    new_order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        shipping_address={
            "recipient_name": address.recipient_name,
            "phone_number": address.phone_number,
            "full_address": address.displayAddress
        },
        shipping_method={"id": order_data.shipping_option_id, "name": "標準配送", "cost": shipping_cost},
        status="pending",
        payment_status="unpaid",
        status_history=initial_status_history
    )
    db.add(new_order)
    db.flush() # 獲取 new_order.id

    # 6. 建立訂單項目，並正式更新庫存和商品狀態
    for item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=locked_product_map[item.product_id].price
        )
        
        # 更新被鎖定的商品
        locked_product = locked_product_map[item.product_id]
        locked_product.stock_quantity -= item.quantity
        
        # --- [新功能] 更新商品狀態 ---
        # 如果庫存歸零，將商品狀態設為 "sold"
        if locked_product.stock_quantity <= 0:
            locked_product.status = "sold"

        db.add(order_item)
        db.delete(item) # 從購物車刪除

    # 7. 提交事務 (Transaction)，釋放所有鎖
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"建立訂單時發生錯誤: {e}")

    db.refresh(new_order)
    return new_order


# --- 買家確認完成訂單 (保持不變) ---
@router_orders.patch("/{order_id}/complete", response_model=OrderResponse)
def complete_order_by_buyer(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ... (此函式保持不變) ...
    # 1. 查找訂單並驗證擁有者
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="找不到訂單或您沒有權限")

    # 2. 驗證狀態是否為 'delivering'
    if order.status != "delivering":
        raise HTTPException(
            status_code=400, 
            detail=f"無法完成此訂單，因為訂單狀態為 '{order.status}'，而非 'delivering'"
        )

    # 3. 更新狀態
    order.status = "completed"
    order.payment_status = "paid" # 貨到付款完成，標記為已付款
    
    new_history_entry = {
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat(),
        "description": "買家已確認收到商品並完成訂單。"
    }
    
    if order.status_history:
        order.status_history.append(new_history_entry)
    else:
        order.status_history = [new_history_entry]
    
    # 標記 JSON 欄位已修改
    flag_modified(order, "status_history")

    db.commit()
    db.refresh(order)
    return order

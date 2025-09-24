# --- FILE: routers/orders.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List

from database.db import get_db
from models.user import User
from models.product import Product
from models.order import Order, OrderItem
from models.cart import CartItem
from models.address import Address
from models.user_interactions import ShippingOption # 假設運送選項模型在此
from schemas.order_schema import OrderCreate, OrderResponse
from utils.token import get_current_user

router_orders = APIRouter

# 模擬優惠券驗證
def validate_coupon(code: str, total: float):
    if code == "SALE50":
        return {"discount_amount": 50.0, "message": "已折抵 NT$50"}
    return {"discount_amount": 0.0, "message": "無效的優惠券"}

# --- 關鍵新增：獲取當前使用者的訂單列表 ---
@router_orders.get("", response_model=List[OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取當前登入使用者的所有訂單列表。
    - 訂單會依照建立時間由新到舊排序。
    - 使用 joinedload 預先載入訂單項目和商品資訊，提升效能。
    """
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

@router_orders.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """建立一筆新訂單。"""
    # --- 1. 開始資料庫交易 ---
    with db.begin_nested():
        # --- 2. 驗證輸入資料 ---
        address = db.query(Address).filter(Address.id == order_data.address_id, Address.user_id == current_user.id).first()
        if not address:
            raise HTTPException(status_code=404, detail="找不到指定的地址")

        shipping_option = db.query(ShippingOption).filter(ShippingOption.id == order_data.shipping_option_id).first()
        if not shipping_option:
            raise HTTPException(status_code=404, detail="找不到指定的運送方式")

        # --- 3. 從購物車獲取商品並驗證庫存 ---
        cart_items = db.query(CartItem).filter(
            CartItem.user_id == current_user.id,
            CartItem.product_id.in_(order_data.product_ids)
        ).options(joinedload(CartItem.product)).all()

        if len(cart_items) != len(order_data.product_ids):
            raise HTTPException(status_code=400, detail="部分商品不在您的購物車中")

        items_subtotal = 0
        for item in cart_items:
            if item.quantity > item.product.stock_quantity:
                raise HTTPException(status_code=400, detail=f"商品 '{item.product.name}' 庫存不足")
            items_subtotal += item.quantity * item.product.price

        # --- 4. 計算總金額 ---
        shipping_cost = shipping_option.cost
        discount = 0
        if order_data.coupon_code:
            discount_info = validate_coupon(order_data.coupon_code, items_subtotal)
            discount = discount_info["discount_amount"]
        
        total_amount = items_subtotal + shipping_cost - discount
        if total_amount < 0: total_amount = 0

        # --- 5. 建立訂單 ---
        new_order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            shipping_address=AddressResponse.from_orm(address).dict(), # 儲存地址快照
            shipping_method={"name": shipping_option.name, "cost": shipping_option.cost} # 儲存運送方式快照
        )
        db.add(new_order)

        # --- 6. 處理訂單項目、庫存和購物車 ---
        for item in cart_items:
            # 建立訂單項目
            order_item = OrderItem(
                order=new_order,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=item.product.price
            )
            db.add(order_item)
            # 扣除庫存
            item.product.stock_quantity -= item.quantity
            # 從購物車刪除
            db.delete(item)
        
        # --- 7. 提交交易 ---
        db.commit()
    
    db.refresh(new_order)
    return new_order

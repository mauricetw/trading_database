# --- FILE: routers/orders.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime

from database.db import get_db
from models.user import User
from models.address import Address
from models.order import Order, OrderItem
from models.user_interactions import CartItem
from schemas.order_schema import OrderCreate, OrderResponse
from utils.token import get_current_user

router_orders = APIRouter

# 模擬優惠券驗證
def validate_coupon(code: str, total: float):
    if code == "SALE50":
        return {"discount_amount": 50.0, "message": "已折抵 NT$50"}
    return {"discount_amount": 0.0, "message": "無效的優惠券"}

@router_orders.get("", response_model=List[OrderResponse])
def get_my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """獲取當前登入使用者的所有訂單列表。"""
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .options(
            # 為了效能，列表頁只載入訂單本身
            # 詳情讓使用者點進去看
            joinedload(Order.items).joinedload(OrderItem.product)
        )
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders

# --- 關鍵新增：獲取單一訂單的詳細資訊 ---
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
    address = db.query(Address).filter(Address.id == order_data.address_id, Address.user_id == current_user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="找不到指定的地址或地址不屬於您")

    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.id.in_(order_data.cart_item_ids)
    ).all()

    if not cart_items or len(cart_items) != len(order_data.cart_item_ids):
        raise HTTPException(status_code=404, detail="購物車項目不匹配或找不到")

    items_subtotal = 0
    for item in cart_items:
        if item.quantity > item.product.stock_quantity:
            raise HTTPException(status_code=400, detail=f"商品 '{item.product.name}' 庫存不足")
        items_subtotal += item.quantity * item.product.price

    shipping_cost = 60.0 
    discount = 0.0
    # TODO: 根據 coupon_code 計算折扣
    total_amount = items_subtotal + shipping_cost - discount

    # 建立初始的狀態歷史
    initial_status_history = [{
        "status": "established",
        "timestamp": datetime.utcnow().isoformat(),
        "description": "訂單已成功建立，等待賣家確認。"
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
        status="established",
        status_history=initial_status_history
    )
    db.add(new_order)
    db.flush()

    for item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=item.product.price
        )
        item.product.stock_quantity -= item.quantity
        db.add(order_item)
        db.delete(item)

    db.commit()
    db.refresh(new_order)
    return new_order


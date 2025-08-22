# --- FILE: routers/seller.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from database.db import get_db
from models.user import User
from models.product import Product
from schemas.product_schema import ProductResponse
from utils.token import get_current_user

from schemas.order_schema import OrderResponse, OrderStatusUpdate # 引入 schema
from models.order import Order # 引入 model

router = APIRouter()

@router.get("/products", response_model=List[ProductResponse])
async def get_my_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取當前登入賣家自己上架的所有商品。
    """
    # 檢查使用者是否真的是賣家 (可選，但建議)
    if not current_user.is_seller:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有賣家權限"
        )

    # 查詢只屬於該賣家的商品，並預先載入賣家資訊
    seller_products = (
        db.query(Product)
        .options(joinedload(Product.seller))
        .filter(Product.seller_id == current_user.id)
        .order_by(Product.created_at.desc())
        .all()
    )
    
    return seller_products

@router.get("/orders", response_model=List[OrderResponse])
async def get_my_orders_as_seller(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """獲取當前登入賣家收到的所有訂單。"""
    # 這是一個較複雜的查詢，需要找到所有包含該賣家商品的訂單
    # 假設一個訂單只會來自一個賣家
    orders = db.query(Order).join(OrderItem).filter(OrderItem.product.has(seller_id=current_user.id)).distinct().all()
    return orders

@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order_status_by_seller(order_id: int, status_update: OrderStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """賣家更新訂單狀態。"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到訂單")
    
    # TODO: 安全性檢查，確保 current_user 是這個訂單中任何一個商品的賣家
    
    order.status = status_update.status
    db.commit()
    db.refresh(order)
    return order

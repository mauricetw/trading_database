# --- FILE: routers/orders.py (新檔案) ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.db import get_db
from models.user import User
from models.order import Order, OrderItem
from schemas.order_schema import OrderResponse
from utils.token import get_current_user

router = APIRouter()

@router.get("", response_model=List[OrderResponse])
async def get_my_orders_as_buyer(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """獲取當前登入買家的所有訂單。"""
    orders = db.query(Order).filter(Order.buyer_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders

# TODO: 建立訂單的 API (POST /orders) 會更複雜，需要從購物車轉換，暫時先建立骨架

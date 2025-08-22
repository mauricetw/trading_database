# --- FILE: routers/shipping.py (新檔案) ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.db import get_db
from models.user import User, ShippingOption
from schemas.shipping_schema import ShippingOptionCreate, ShippingOptionUpdate, ShippingOptionResponse
from utils.token import get_current_user

router = APIRouter()

@router.get("/options", response_model=List[ShippingOptionResponse])
async def get_my_shipping_options(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """獲取當前賣家的所有運送方式。"""
    return db.query(ShippingOption).filter(ShippingOption.seller_id == current_user.id).all()

# TODO: 新增、更新、刪除運送方式的 API

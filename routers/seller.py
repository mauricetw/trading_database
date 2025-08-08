# --- FILE: routers/seller.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from database.db import get_db
from models.user import User
from models.product import Product
from schemas.product_schema import ProductResponse
from utils.token import get_current_user

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

# TODO: 未來可以在這裡新增其他賣家專屬的 API，例如：
# @router.get("/orders") -> 獲取賣家的訂單
# @router.put("/orders/{order_id}") -> 更新訂單狀態

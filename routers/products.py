from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from database.db import get_db
from models.product import Product, Category
from schemas.product_schema import ProductResponse, CategorySchema

# 初始化 API Router
router = APIRouter(
    prefix="/products",
    tags=["商品 (Products)"]
)

@router.get("/categories", response_model=List[CategorySchema])
def get_categories(db: Session = Depends(get_db)):
    """
    獲取所有商品分類列表。
    """
    return db.query(Category).order_by(Category.id).all()

@router.get("", response_model=List[ProductResponse])
def get_products(
    category_id: Optional[int] = None, 
    db: Session = Depends(get_db)
):
    """
    獲取公開的商品列表，支援分類篩選。
    - 只會回傳狀態為 'available' (銷售中) 的商品。
    """
    query = db.query(Product).filter(Product.status == "available")
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # 使用 joinedload 預先載入關聯的資料，避免 N+1 查詢問題
    return query.options(
        joinedload(Product.seller),
        joinedload(Product.category), 
        joinedload(Product.images)
    ).order_by(Product.created_at.desc()).all()


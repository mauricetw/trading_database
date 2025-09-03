# --- FILE: routers/products.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional

from database.db import get_db
from models.product import Product, Category
from schemas.product_schema import ProductResponse, CategorySchema

# 初始化 API Router
router_products = APIRouter(
    prefix="/products",
    tags=["公開商品 API (Public Products)"]
)

@router_products.get("/categories", response_model=List[CategorySchema])
def get_categories(db: Session = Depends(get_db)):
    """
    獲取所有商品分類列表。
    """
    return db.query(Category).order_by(Category.id).all()

@router_products.get("", response_model=List[ProductResponse])
def get_products(
    # --- 關鍵修正：新增支援分頁與搜尋的參數 ---
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    獲取公開的商品列表，支援分類篩選、關鍵字搜尋和分頁。
    - 只會回傳狀態為 'available' (銷售中) 的商品。
    """
    query = db.query(Product).filter(Product.status == "available")
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # --- 應用搜尋條件 ---
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )
    
    # --- 應用分頁並執行查詢 ---
    products = query.options(
        joinedload(Product.seller),
        joinedload(Product.category), 
        joinedload(Product.images)
    ).order_by(Product.created_at.desc()).offset(skip).limit(limit).all()

    return products

@router_products.get("/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    """
    根據 ID 獲取單一商品的詳細資訊。
    """
    product = db.query(Product).options(
        joinedload(Product.seller),
        joinedload(Product.category),
        joinedload(Product.images)
    ).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到此商品")
        
    return product

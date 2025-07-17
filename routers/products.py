from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from models.product import Product
from schemas.product_schema import ProductCreate, ProductResponse
from typing import List

router = APIRouter()


@router.post("/products", response_model=ProductResponse)
async def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    # 轉成 dict 後轉 JSON
    try:
        db_product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            original_price=product_data.original_price,
            category_id=product_data.category_id,
            stock_quantity=product_data.stock_quantity,
            image_urls=product_data.image_urls,
            category=product_data.category,
            status=product_data.status,
            tags=product_data.tags,
            shipping_info=product_data.shipping_info.dict() if product_data.shipping_info else None,
            seller_id=product_data.seller_id,
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500,detail=f"建立商品失敗:{str(e)}")


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/products", response_model=List[ProductResponse])
async def get_all_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.created_at.desc()).all()

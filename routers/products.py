from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from models import product
from schemas.product_schema import ProductCreate, ProductResponse

router = APIRouter()

@router.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

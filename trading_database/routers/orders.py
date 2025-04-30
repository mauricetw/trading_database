from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from models import order
from schemas.order_schema import OrderCreate, OrderResponse

router = APIRouter()

@router.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

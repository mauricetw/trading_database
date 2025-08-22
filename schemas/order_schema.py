# --- FILE: schemas/order_schema.py (新檔案) ---
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .product_schema import ProductResponse # 引入商品資訊以在訂單中顯示

class OrderItemResponse(BaseModel):
    id: int
    quantity: int
    price_at_purchase: float
    product: ProductResponse

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    total_amount: float
    status: str
    shipping_info: dict
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str # 期望前端傳來新的狀態字串

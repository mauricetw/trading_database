# --- FILE: schemas/order_schema.py ---
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .product_schema import ProductResponse # 引入 ProductResponse

# --- 新建：用於 API 回應的 OrderStatusUpdate 模型 ---
class OrderStatusUpdateSchema(BaseModel):
    status: str
    timestamp: datetime
    description: Optional[str] = None

    class Config:
        from_attributes = True

class OrderItemSchema(BaseModel):
    product_id: int
    quantity: int
    price_at_purchase: float
    product: ProductResponse # 巢狀嵌入完整的商品資訊

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_amount: float
    shipping_address: dict
    shipping_method: dict
    created_at: datetime
    items: List[OrderItemSchema]

    # --- 加入 status_history 欄位 ---
    status_history: List[OrderStatusUpdateSchema] = []

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    address_id: int
    shipping_option_id: int
    # 前端傳入的是 product_id 列表，而不是 cart_item_id
    product_ids: List[int] 
    coupon_code: Optional[str] = None

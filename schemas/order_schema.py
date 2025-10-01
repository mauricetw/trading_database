# --- FILE: schemas/order_schema.py ---
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .product_schema import ProductResponse

# (OrderItemSchema, OrderStatusUpdateSchema, 和 OrderResponse 保持不變)
class OrderStatusUpdateSchema(BaseModel):
    status: str
    timestamp: datetime
    description: Optional[str] = None
    class Config: from_attributes = True

class OrderItemSchema(BaseModel):
    product_id: int
    quantity: int
    price_at_purchase: float
    product: ProductResponse
    class Config: from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_amount: float
    shipping_address: Dict[str, Any]
    shipping_method: Dict[str, Any]
    created_at: datetime
    items: List[OrderItemSchema]
    status_history: List[OrderStatusUpdateSchema] = []
    class Config: from_attributes = True

# --- 用於「建立」訂單的 Schema ---
class OrderCreate(BaseModel):
    address_id: int
    shipping_option_id: int
    
    # --- 關鍵修正：將 product_ids 更名為 cart_item_ids ---
    # 這將使其與前端 OrderService 中發送的請求 body 完全匹配
    cart_item_ids: List[int] = Field(..., min_length=1)
    
    coupon_code: Optional[str] = None

# --- FILE: schemas/order_schema.py ---
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
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
    
    # --- [BUG 修正] ---
    # 2. 在 API 回應的 Pydantic Schema 中加入 payment_status
    #    FastAPI 會自動從我們在 models/order.py 中新增的欄位讀取
    payment_status: str 

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
    
    # --- 將 product_ids 更名為 cart_item_ids ---
    # 這將使其與前端 OrderService 中發送的請求 body 完全匹配
    cart_item_ids: List[int] = Field(..., min_length=1)
    
    coupon_code: Optional[str] = None


# --- 定義一個只接受特定狀態字串的 Literal 型別 ---
OrderStatusEnum = Literal["pending", "preparing", "delivering", "completed", "failed", "cancelled", "rejected"]

class SellerOrderStatusUpdate(BaseModel):
    # 2. 將 status 欄位的類型改為我們定義的 Literal
    # 這會讓 FastAPI 自動驗證傳入的值是否為這四者之一
    status: OrderStatusEnum 
    description: Optional[str] = Field(None, description="更新狀態時的備註，例如物流單號")

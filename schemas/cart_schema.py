# --- FILE: schemas/cart_schema.py ---
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
# 引入 ProductResponse 以便在回傳時嵌入商品詳情
from .product_schema import ProductResponse

class CartItemBase(BaseModel):
    product_id: int
    quantity: int

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    user_id: int
    quantity: int
    added_at: datetime
    # 為了讓前端能直接顯示商品資訊，我們嵌入完整的 ProductResponse
    product: ProductResponse

    class Config:
        from_attributes = True

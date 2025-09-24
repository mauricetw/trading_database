# --- FILE: schemas/cart_schema.py ---
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

# 引入我們已經定義好的 ProductResponse，以便在購物車中巢狀使用
from .product_schema import ProductResponse

# --- 用於「新增」購物車項目的 Schema ---
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, gt=0) # 數量必須大於 0

# --- 用於「更新」購物車項目數量的 Schema ---
class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0) # 更新時數量也必須大於 0

# --- 最終回傳給前端的、結構完整的購物車項目模型 ---
class CartItemResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    added_at: datetime
    
    # --- 關鍵：巢狀嵌入完整的 ProductResponse ---
    # 這確保了回傳的 JSON 結構與前端 CartItem.fromJson 的期望完全匹配
    product: ProductResponse

    class Config:
        from_attributes = True # 啟用 ORM 模式

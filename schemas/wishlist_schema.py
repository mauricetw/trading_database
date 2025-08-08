# --- FILE: schemas/wishlist_schema.py ---
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .product_schema import ProductResponse

class WishlistItemCreate(BaseModel):
    product_id: int

class WishlistItemResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    added_at: datetime
    # 同樣，嵌入完整的 ProductResponse
    product: ProductResponse

    class Config:
        from_attributes = True

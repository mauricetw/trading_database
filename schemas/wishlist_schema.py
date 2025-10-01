# --- FILE: schemas/wishlist_schema.py ---
from pydantic import BaseModel
from datetime import datetime
from .product_schema import ProductResponse # 引入 ProductResponse

# --- 用於「新增」收藏項目的 Schema ---
class WishlistItemCreate(BaseModel):
    product_id: int

# --- 最終回傳給前端的、結構完整的收藏項目模型 ---
class WishlistItemResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    added_at: datetime
    
    # --- 關鍵：巢狀嵌入完整的 ProductResponse ---
    # 這確保了回傳的 JSON 結構與前端的期望完全匹配
    product: ProductResponse

    class Config:
        from_attributes = True # 啟用 ORM 模式

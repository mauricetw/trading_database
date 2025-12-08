# --- FILE: schemas/wishpool_schema.py ---
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .user_schema import UserPublicProfile
from .product_schema import ProductResponse

# --- 許願池 (Wishpool) ---

class WishpoolBase(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    photo_url: Optional[str] = None
    price: int
    quantity: int = 1
    
    # --- [修改] ---
    # 建立時不需要傳 address_id (後端自動抓預設)，但回應時會包含 shipping_address
    # shipping_address 在 Response 中定義
    
    shipping_name: str = "標準配送"
    shipping_cost: float = 60.0
    
    location: Optional[str] = None
    course_code: Optional[str] = None

class WishpoolCreate(WishpoolBase):
    pass # 不需要額外欄位，address 由後端自動抓取

class WishpoolUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    photo_url: Optional[str] = None
    price: Optional[int] = None
    quantity: Optional[int] = None
    
    shipping_name: Optional[str] = None
    shipping_cost: Optional[float] = None
    
    location: Optional[str] = None
    course_code: Optional[str] = None

class WishpoolResponse(WishpoolBase):
    id: int
    user_id: int
    status: str
    matched_item_id: Optional[int] = None
    like_count: int = 0
    
    # [新增] 回傳地址快照
    shipping_address: Dict[str, Any]
    
    created_at: datetime
    updated_at: datetime

    user: Optional[UserPublicProfile] = None
    matched_item: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

# (Invite 相關 Schema 保持不變)
class WishpoolFulfillRequest(BaseModel):
    product_id: Optional[int] = None
    new_product_name: Optional[str] = None 
    new_product_image_url: Optional[str] = None

class WishpoolInviteCreate(BaseModel):
    product_id: Optional[int] = None
    message: Optional[str] = None

class WishpoolInviteResponse(BaseModel):
    id: int
    wishpool_id: int
    seller_id: int
    product_id: Optional[int] = None
    message: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    seller: Optional[UserPublicProfile] = None
    product: Optional[ProductResponse] = None
    wishpool: Optional[WishpoolResponse] = None 

    class Config:
        from_attributes = True

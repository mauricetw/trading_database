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
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    location: Optional[str] = None
    course_code: Optional[str] = None

class WishpoolCreate(WishpoolBase):
    pass

class WishpoolUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    photo_url: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    location: Optional[str] = None
    course_code: Optional[str] = None

class WishpoolResponse(WishpoolBase):
    id: int
    user_id: int
    status: str
    matched_item_id: Optional[int] = None
    like_count: int = 0
    created_at: datetime
    updated_at: datetime

    user: Optional[UserPublicProfile] = None
    matched_item: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

# --- 許願池邀請 (Invite / Offer) ---

class WishpoolInviteCreate(BaseModel):
    # --- [修改] 移除強制關聯商品 ---
    # product_id 現在是可選的，甚至可以不傳
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

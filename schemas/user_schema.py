# --- FILE: schemas/user_schema.py ---
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# --- 用於回傳給前端的、精簡的公開個人資料 ---
class UserPublicProfile(BaseModel):
    id: int
    # --- 關鍵修正：從 nickname 讀取，但在 JSON 中顯示為 username ---
    username: str = Field(validation_alias='nickname')
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- 用於回傳給前端的、更完整的個人資料 ---
class UserProfileResponse(BaseModel):
    id: int
    # --- 同步修正 ---
    username: str = Field(validation_alias='nickname')
    email: EmailStr
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    registered_at: datetime
    last_login_at: Optional[datetime] = None
    bio: Optional[str] = None
    school_name: Optional[str] = None
    is_verified: bool
    roles: List[str]
    is_seller: bool
    
    class Config:
        from_attributes = True

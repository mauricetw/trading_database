# --- FILE: schemas/auth_schema.py (重構版) ---
# 說明：
# 1. 結構完全對齊前端的 AuthResponse 和 User 模型。
# 2. `orm_mode` 已更新為 `from_attributes`。
# 3. `UserCreate` 中的 `username` 欄位已更名為 `nickname` 以匹配資料庫模型。
# 4. 新增了 `TokenSchema` 來更好地組織 Token 結構。

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime

# --- Request Schemas ---

class SendVerificationCodeRequest(BaseModel):
    email: EmailStr

class UserCreate(BaseModel):
    nickname: str = Field(..., alias='username') # 接收前端的 'username'，但在後端作為 'nickname'
    email: EmailStr
    password: str = Field(..., min_length=8)
    code: str

class UserLogin(BaseModel):
    login: str
    password: str

class ForgotPasswordRequest(BaseModel):
    login: str

class VerifyCodeRequest(BaseModel):
    login: str
    code: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

# --- Response Schemas ---

class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponseSchema(BaseModel):
    id: int
    nickname: str = Field(..., alias='username') # 回傳給前端時，將 nickname 轉為 username
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
    seller_name: Optional[str] = None
    seller_description: Optional[str] = None
    seller_rating: Optional[float] = None
    buyer_rating: Optional[float] = None
    product_count: int

    class Config:
        from_attributes = True
        populate_by_name = True # 允許使用 alias

# 最終的登入/註冊成功回應，完全匹配前端 AuthResponse 模型
class AuthSuccessResponse(BaseModel):
    token: TokenSchema
    user: UserResponseSchema

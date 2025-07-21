from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=8, description="密碼長度必須至少 8 個字元")
    email: EmailStr

    @validator('email')
    def email_must_be_ntust(cls, v):
        if not v.endswith('@mail.ntust.edu.tw'):
            raise ValueError('僅接受 NTUST 的信箱')
        return v
    
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    school_name: Optional[str] = None

class UserLogin(BaseModel):
    login: str
    password: str

class ForgotPasswordRequest(BaseModel):
    login: str

    @validator('login')
    def email_must_be_ntust_if_email(cls, v):
        if "@" in v:
            if not v.endswith('@mail.ntust.edu.tw'):
                raise ValueError('若使用 email，僅接受 @mail.ntust.edu.tw 網域')
        return v

class VerifyCodeRequest(BaseModel):
    login: str 
    code: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, description="密碼長度必須至少 8 個字元")

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserDataForAuth(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    registered_at: datetime
    last_login_at: Optional[datetime] = None
    bio: Optional[str] = None
    school_name: Optional[str] = None
    is_verified: bool
    roles: Optional[List[str]] = None
    is_seller: bool
    seller_name: Optional[str] = None
    seller_description: Optional[str] = None
    seller_rating: Optional[float] = None
    product_count: int

    class Config:
        # --- 錯誤修正：將 orm_mode = True 改為 from_attributes = True ---
        from_attributes = True

# 最終的登入/註冊回應結構
class LoginResponse(BaseModel):
    token: AuthResponse
    user: UserDataForAuth

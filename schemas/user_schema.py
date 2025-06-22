from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
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
    login: str  # 可以是 username 或 email
    password: str


class ForgotPasswordRequest(BaseModel):
    login: str

    @validator('login')
    def email_must_be_ntust_if_email(cls, v):
        # 如果是 email 格式才做網域驗證
        if "@" in v:
            if not v.endswith('@mail.ntust.edu.tw'):
                raise ValueError('若使用 email，僅接受 @mail.ntust.edu.tw 網域')
        return v



class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    token: str

    # 以下為補充欄位（皆為 optional 對應 Dart 的 nullable 屬性）
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    registered_at: datetime
    last_login_at: Optional[datetime] = None
    bio: Optional[str] = None
    school_name: Optional[str] = None
    is_verified: Optional[bool] = None
    roles: Optional[List[str]] = None

    # 賣家資料
    is_seller: Optional[bool] = False
    seller_name: Optional[str] = None
    seller_description: Optional[str] = None
    seller_rating: Optional[float] = None
    product_count: Optional[int] = 0

    class Config:
        orm_mode = True

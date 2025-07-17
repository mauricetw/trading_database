from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime


# --- 最佳實踐建議 ---
# 為了避免和 user_schema.py 中的 UserResponse 命名衝突，
# 建議將與認證流程相關的回應模型重新命名，例如 AuthResponse。
# 這樣可以讓每個檔案的職責更清晰。

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=8, description="密碼長度必須至少 8 個字元")
    email: EmailStr

    # 自訂驗證器
    @validator('email')
    def email_must_be_ntust(cls, v):
        if not v.endswith('@mail.ntust.edu.tw'):
            raise ValueError('僅接受 NTUST 的信箱')
        return v
    
    # 註冊時可以選擇性提供的欄位
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    school_name: Optional[str] = None

class UserLogin(BaseModel):
    login: str  # 可以是 username 或 email
    password: str

class ForgotPasswordRequest(BaseModel):
    login: str

    # 驗證器
    @validator('login')
    def email_must_be_ntust_if_email(cls, v):
        if "@" in v:
            if not v.endswith('@mail.ntust.edu.tw'):
                raise ValueError('若使用 email，僅接受 @mail.ntust.edu.tw 網域')
        return v

class VerifyCodeRequest(BaseModel):
    # 讓前端傳送 email 或 username，後端來查找 user_id，這樣更安全。
    login: str 
    code: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, description="密碼長度必須至少 8 個字元")

# --- 重構後的回應模型 ---
# 這個模型現在專門用於登入和註冊成功後的回應。
# 我們不再需要手動建立字典，Pydantic 會自動從 User ORM 物件填充資料。
class AuthResponse(BaseModel):
    # 我們需要一個欄位來接收 token，但 User 模型本身沒有 token 欄位。
    # 所以我們定義一個 TokenData 模型，然後在路由中組合它們。
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
        orm_mode = True

# 最終的登入/註冊回應結構
class LoginResponse(BaseModel):
    token: AuthResponse
    user: UserDataForAuth


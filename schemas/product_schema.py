from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- 用於在商品回應中顯示的賣家公開資訊 ---
# 避免洩漏使用者 email、密碼等敏感資訊
class UserInProductResponse(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None

    class Config:
        orm_mode = True

# --- 用於前端建立商品時傳入的資料模型 ---
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    original_price: Optional[float] = None
    category_id: int
    category: str
    stock_quantity: int = 1
    image_urls: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    # 注意：seller_id 不應該由前端提供，將從 token 中獲取

# --- 用於 API 回應的商品資料模型 ---
class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    original_price: Optional[float] = None
    category_id: int
    category: str
    stock_quantity: int
    status: str
    image_urls: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime
    
    # 關聯的賣家資訊
    seller_id: int
    seller: UserInProductResponse # 巢狀顯示賣家公開資訊

    class Config:
        orm_mode = True # 允許 Pydantic 從 ORM 物件自動轉換

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserInProductResponse(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

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
    
    # --- 錯誤修正 ---
    # 將 created_at 和 updated_at 的類型改為 Optional[datetime]
    # 這允許它們的值可以是 datetime 物件，也可以是 None (對應資料庫中的 NULL)
    # 這樣即使手動新增的資料沒有時間戳，API 也不會因驗證失敗而崩潰。
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    seller_id: int
    seller: UserInProductResponse

    class Config:
        from_attributes = True

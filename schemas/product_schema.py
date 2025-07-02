from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# --- 嵌套物件：ShippingInformation ---
class ShippingInformation(BaseModel):
    cost: float
    region: str
    carrier: Optional[str] = None


# --- 商品建立用模型 ---
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    original_price: Optional[float] = None
    category_id: int
    stock_quantity: int
    image_urls: List[str]
    category: str
    status: str = "available"

    tags: Optional[List[str]] = None
    shipping_info: Optional[ShippingInformation] = None
    seller_id: int  # 必要：來自前端登入使用者

    class Config:
        orm_mode = True


# --- 商品回傳用模型 ---
class ProductResponse(ProductCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    sales_count: int = 0
    average_rating: Optional[float]
    review_count: Optional[int]
    is_favorite: bool = False
    is_sold: bool = False

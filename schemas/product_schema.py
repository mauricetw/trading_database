# --- FILE: schemas/product_schema.py ---
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import datetime

# --- 用於回傳給前端的、輕量的分類模型 ---
class CategorySchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# --- 用於回傳給前端的、輕量的賣家模型 ---
class SellerInProductResponse(BaseModel):
    id: int
    # 修正：從 nickname 讀取，但在 JSON 中顯示為 username
    username: str = Field(validation_alias='nickname') 
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True
        
# --- 用於回傳給前端的、輕量的圖片模型 ---
class ProductImageSchema(BaseModel):
    image_url: str
    display_order: int

    class Config:
        from_attributes = True

# --- 用於「建立」商品的 Schema，只包含前端需要提供的資料 ---
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=5)
    description: Optional[str] = Field(None)
    price: float = Field(..., gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    stock_quantity: int = Field(..., ge=0)
    category_id: int
    tags: Optional[List[str]] = None
    image_urls: List[str] = Field(..., min_items=1, max_items=5)

# --- 用於「更新」商品的 Schema，所有欄位都是可選的 ---
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=5)
    description: Optional[str] = Field(None, min_length=10)
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    image_urls: Optional[List[str]] = Field(None, min_items=1, max_items=5)

# --- 用於更新商品狀態的 Schema ---
class ProductStatusUpdate(BaseModel):
    status: str

# --- 最終回傳給前端的、結構完整的商品模型 ---
class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    original_price: Optional[float] = None
    stock_quantity: int
    status: str
    sales_count: int
    average_rating: Optional[float] = None
    review_count: int
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    seller_id: int
    
    # --- 關鍵修正：直接從 SQLAlchemy 的 relationship 讀取關聯物件 ---
    seller: SellerInProductResponse
    category: CategorySchema
    
    # 並且回傳排序後的圖片物件列表
    images: List[ProductImageSchema]

    class Config:
        from_attributes = True


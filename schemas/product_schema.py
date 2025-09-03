# --- FILE: schemas/product_schema.py ---
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import datetime

# --- 基礎 Schema ---

class CategorySchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ProductImageSchema(BaseModel):
    id: int
    image_url: str
    display_order: int

    class Config:
        from_attributes = True

class SellerInProductResponse(BaseModel):
    id: int
    # --- 關鍵修正：使用 alias 來對應 model 的 nickname ---
    # 從 model 的 nickname 讀取，但在轉為 JSON 時 key 會是 username
    nickname: str = Field(..., alias='username')
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True # 允許 alias 生效

# --- 輸入 (Input) Schemas ---

class ProductBase(BaseModel):
    name: str = Field(..., min_length=5, description="商品名稱")
    description: Optional[str] = Field(None, min_length=10, description="商品描述")
    price: float = Field(..., gt=0, description="價格必須大於 0")
    original_price: Optional[float] = Field(None, gt=0, description="原價必須大於 0")
    stock_quantity: int = Field(..., ge=0, description="庫存數量不能為負數")
    category_id: int
    tags: Optional[List[str]] = []
    image_urls: List[str] = Field(..., min_length=1, max_length=5, description="至少需要 1 張圖片，最多 5 張")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    # 在更新時，所有欄位都是可選的
    name: Optional[str] = Field(None, min_length=5)
    description: Optional[str] = Field(None, min_length=10)
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    image_urls: Optional[List[str]] = Field(None, min_length=1, max_length=5)

class ProductStatusUpdate(BaseModel):
    status: str

# --- 輸出 (Output) Schema ---

class ProductResponse(BaseModel):
    # 直接從 Product model 讀取的欄位
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
    shipping_info: Optional[dict] = None

    # --- REFACTORED: 使用 @computed_field 處理關聯資料，更清晰高效 ---
    
    # 處理關聯的 Category
    @computed_field
    @property
    def category(self, product: "Product") -> CategorySchema:
        return product.category

    # 處理關聯的 Seller
    @computed_field
    @property
    def seller(self, product: "Product") -> SellerInProductResponse:
        return product.seller

    # 處理關聯的 Images，並確保正確排序
    @computed_field(return_type=List[ProductImageSchema])
    @property
    def images(self, product: "Product") -> List[ProductImageSchema]:
        # 關鍵修正：根據 display_order 排序
        return sorted(product.images, key=lambda img: img.display_order)

    class Config:
        from_attributes = True

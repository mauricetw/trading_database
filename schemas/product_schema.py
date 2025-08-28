from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Any
from datetime import datetime
from models.product import Product as ProductModel

class CategorySchema(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class SellerInProductResponse(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str = Field(..., min_length=5)
    description: Optional[str] = Field(None, min_length=10)
    price: float = Field(..., gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    stock_quantity: int = Field(..., ge=0)
    category_id: int
    tags: Optional[List[str]] = None
    image_urls: List[str] = Field(..., min_items=1, max_items=5)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=5)
    description: Optional[str] = Field(None, min_length=10)
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    image_urls: Optional[List[str]] = Field(None, min_items=1, max_items=5)

class ProductStatusUpdate(BaseModel):
    status: str

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    original_price: Optional[float] = None
    category_id: int
    category: str
    stock_quantity: int
    status: str
    image_urls: List[str]
    sales_count: int
    average_rating: Optional[float] = None
    review_count: int
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    seller_id: int
    seller: SellerInProductResponse
    shipping_info: Optional[dict] = None

    @model_validator(mode='before')
    @classmethod
    def transform_from_orm(cls, data: Any) -> Any:
        if isinstance(data, ProductModel):
            return {
                **{column.name: getattr(data, column.name) for column in data.__table__.columns},
                "seller": data.seller,
                "category": data.category.name if data.category else None,
                "image_urls": sorted([img.image_url for img in data.images], key=lambda x: x.split("/")[-1]) if data.images else []
            }
        return data

    class Config:
        from_attributes = True

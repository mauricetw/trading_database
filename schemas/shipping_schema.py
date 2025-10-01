# --- FILE: schemas/shipping_schema.py ---
from pydantic import BaseModel, Field
from typing import Optional

# --- 用於「新增」運送方式的 Schema ---
# 賣家 ID 會從 Token 獲取，所以這裡不需要
class ShippingOptionCreate(BaseModel):
    name: str = Field(..., min_length=1, description="運送方式名稱")
    description: Optional[str] = Field(None, description="運送方式的詳細描述")
    cost: float = Field(..., ge=0, description="運費")
    is_enabled: bool = Field(True, description="是否啟用此運送方式")

# --- 用於「更新」運送方式的 Schema ---
# 所有欄位都是可選的，允許前端只傳送有變更的資料
class ShippingOptionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    cost: Optional[float] = Field(None, ge=0)
    is_enabled: Optional[bool] = None


class ShippingOptionSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    cost: float
    is_enabled: bool
    seller_id: int

    class Config:
        from_attributes = True

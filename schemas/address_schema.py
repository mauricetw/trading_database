# --- FILE: schemas/address_schema.py ---
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# --- 用於API回應的基礎模型 ---
class AddressBase(BaseModel):
    recipient_name: str
    phone_number: str
    city: str
    postal_code: str
    street_address_1: str
    country: Optional[str] = "台灣"
    province: Optional[str] = None
    district: Optional[str] = None
    street_address_2: Optional[str] = None
    is_default: bool = False

# --- 用於「建立」新地址的Schema ---
# 所有欄位都是必填的
class AddressCreate(AddressBase):
    pass

# --- 用於「更新」地址的Schema ---
# 所有欄位都是可選的，允許部分更新
class AddressUpdate(BaseModel):
    recipient_name: Optional[str] = None
    phone_number: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    street_address_1: Optional[str] = None
    country: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    street_address_2: Optional[str] = None
    is_default: Optional[bool] = None

# --- 用於 API「回應」的Schema ---
# 包含了資料庫產生的 id 和 user_id
class AddressResponse(AddressBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

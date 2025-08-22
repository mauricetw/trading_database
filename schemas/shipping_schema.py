# --- FILE: schemas/shipping_schema.py (新檔案) ---
from pydantic import BaseModel
from typing import Optional

class ShippingOptionBase(BaseModel):
    name: str
    description: Optional[str] = None
    cost: float
    is_enabled: bool = True

class ShippingOptionCreate(ShippingOptionBase):
    pass

class ShippingOptionUpdate(ShippingOptionBase):
    pass

class ShippingOptionResponse(ShippingOptionBase):
    id: int
    seller_id: int

    class Config:
        from_attributes = True

# --- FILE: schemas/address_schema.py ---
from pydantic import BaseModel, Field
from typing import Optional

class AddressBase(BaseModel):
    recipient_name: str
    phone_number: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    postal_code: str
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressUpdate(BaseModel):
    recipient_name: Optional[str] = None
    phone_number: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    is_default: Optional[bool] = None

class AddressResponse(AddressBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

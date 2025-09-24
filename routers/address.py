# --- FILE: routers/address.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.db import get_db
from models.user import User
from models.address import Address
from schemas.address_schema import AddressResponse, AddressCreate, AddressUpdate
from utils.token import get_current_user

router_address = APIRouter(
    prefix="/addresses",
    tags=["地址管理 (Addresses)"]
)

@router_address.get("", response_model=List[AddressResponse])
def get_my_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取當前登入使用者的所有地址。"""
    return db.query(Address).filter(Address.user_id == current_user.id).all()

# (此處可擴充 POST, PUT, DELETE 等地址管理 API)

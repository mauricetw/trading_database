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

# --- [新功能] 新增一筆地址 ---
@router_address.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(
    address_data: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """為當前登入的使用者新增一筆新地址。"""
    
    # 1. 將 Pydantic schema 轉換為 SQLAlchemy 模型
    new_address = Address(
        **address_data.model_dump(),
        user_id=current_user.id  # 確保地址與當前使用者綁定
    )
    
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address

# --- [新功能] 更新一筆地址 ---
@router_address.put("/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address_data: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新一筆屬於當前使用者的地址。"""
    
    # 1. 查詢地址，同時驗證擁有者 (安全性)
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="找不到地址或您沒有權限")
        
    # 2. 更新資料
    # exclude_unset=True 確保只有「有被傳送」的欄位才會被更新
    update_data = address_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(address, key, value)

    db.commit()
    db.refresh(address)
    return address

# --- [新功能] 刪除一筆地址 ---
@router_address.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """刪除一筆屬於當前使用者的地址。"""
    
    # 1. 查詢地址，同時驗證擁有者 (安全性)
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(status_code=404, detail="找不到地址或您沒有權限")

    # 2. 刪除
    db.delete(address)
    db.commit()
    
    # 刪除成功，回傳 204 No Content
    return None

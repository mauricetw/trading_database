# --- FILE: routers/shipping.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.db import get_db
from models.user import User, ShippingOption
from schemas.shipping_schema import ShippingOptionSchema, ShippingOptionCreate, ShippingOptionUpdate
from utils.token import get_current_user

router_shipping = APIRouter(
    prefix="/shipping-options",
    tags=["運送方式 (Shipping Options)"]
)

# --- 受保護的 /me 路由，專門給賣家獲取自己的運送選項 ---
@router_shipping.get("/me", response_model=List[ShippingOptionSchema])
def get_my_shipping_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取當前登入賣家自己設定的所有運送方式。"""
    # 直接使用 current_user.id 進行查詢，更安全
    return db.query(ShippingOption).filter(ShippingOption.seller_id == current_user.id).all()


# --- GET (查詢) ---
@router_shipping.get("", response_model=List[ShippingOptionSchema])
def get_shipping_options_for_seller(
    seller_id: int, # 根據賣家 ID 查詢
    db: Session = Depends(get_db),
    # 這個 API 需要登入才能呼叫
    current_user: User = Depends(get_current_user) 
):
    """
    獲取指定賣家的所有可用運送方式。
    """
    options = db.query(ShippingOption).filter(
        ShippingOption.seller_id == seller_id,
        ShippingOption.is_enabled == True # 只回傳啟用的選項
    ).all()
    return options

# --- POST (新增) ---
@router_shipping.post("", response_model=ShippingOptionSchema, status_code=status.HTTP_201_CREATED)
def add_shipping_option(
    option_data: ShippingOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """為當前登入的賣家新增一個運送方式。"""
    new_option = ShippingOption(
        **option_data.dict(),
        seller_id=current_user.id
    )
    db.add(new_option)
    db.commit()
    db.refresh(new_option)
    return new_option

# --- PUT (更新) ---
@router_shipping.put("/{option_id}", response_model=ShippingOptionSchema)
def update_shipping_option(
    option_id: int,
    option_data: ShippingOptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新一個已存在的運送方式。只有擁有者才能修改。"""
    db_option = db.query(ShippingOption).filter(
        ShippingOption.id == option_id,
        ShippingOption.seller_id == current_user.id # 確保只能修改自己的
    ).first()

    if not db_option:
        raise HTTPException(status_code=404, detail="找不到運送方式或沒有權限")

    update_data = option_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_option, key, value)
    
    db.commit()
    db.refresh(db_option)
    return db_option

# --- DELETE (刪除) ---
@router_shipping.delete("/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shipping_option(
    option_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """刪除一個運送方式。只有擁有者才能刪除。"""
    db_option = db.query(ShippingOption).filter(
        ShippingOption.id == option_id,
        ShippingOption.seller_id == current_user.id
    ).first()

    if db_option:
        db.delete(db_option)
        db.commit()
    
    # 即使找不到也回傳成功，避免攻擊者猜測 ID
    return None

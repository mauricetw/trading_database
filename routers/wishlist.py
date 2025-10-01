# --- FILE: routers/wishlist.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from database.db import get_db
from models.user import User
from models.user_interactions import WishlistItem
from schemas.wishlist_schema import WishlistItemCreate, WishlistItemResponse
from utils.token import get_current_user

router_wishlist = APIRouter(
    prefix="/wishlist",
    tags=["收藏清單 (Wishlist)"]
)

@router_wishlist.get("", response_model=List[WishlistItemResponse])
def get_my_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取當前登入使用者的完整收藏清單。"""
    return db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).all()

@router_wishlist.post("/items", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_item_to_wishlist(
    item_data: WishlistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """將一個商品加入收藏清單。"""
    try:
        new_item = WishlistItem(
            user_id=current_user.id,
            product_id=item_data.product_id
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item
    except IntegrityError:
        # 捕獲違反唯一性約束的錯誤
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="此商品已在您的收藏清單中"
        )

@router_wishlist.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """從收藏清單中移除指定的商品。"""
    item_to_delete = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == product_id
    ).first()

    if item_to_delete:
        db.delete(item_to_delete)
        db.commit()
    
    return None

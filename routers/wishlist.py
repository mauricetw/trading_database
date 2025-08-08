# --- FILE: routers/wishlist.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from database.db import get_db
from models.user import User
from models.product import Product
from models.user_interactions import WishlistItem
from schemas.wishlist_schema import WishlistItemCreate, WishlistItemResponse
from utils.token import get_current_user

router = APIRouter()

@router.get("", response_model=List[WishlistItemResponse])
async def get_my_wishlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """獲取當前登入使用者的收藏清單。"""
    wishlist_items = (
        db.query(WishlistItem)
        .options(joinedload(WishlistItem.product).joinedload(Product.seller))
        .filter(WishlistItem.user_id == current_user.id)
        .order_by(WishlistItem.added_at.desc())
        .all()
    )
    return wishlist_items

@router.post("", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(item_data: WishlistItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """將商品加入收藏清單。"""
    # 檢查商品是否存在
    product = db.query(Product).filter(Product.id == item_data.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到此商品")

    # 檢查是否已收藏
    existing_item = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == item_data.product_id
    ).first()
    if existing_item:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="此商品已在您的收藏清單中")

    new_item = WishlistItem(**item_data.dict(), user_id=current_user.id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wishlist(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """從收藏清單中移除一項商品。"""
    item_to_delete = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == product_id
    ).first()

    if item_to_delete:
        db.delete(item_to_delete)
        db.commit()
        
    return None

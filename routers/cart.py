# --- FILE: routers/cart.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from database.db import get_db
from models.user import User
from models.product import Product
from models.user_interactions import CartItem
from schemas.cart_schema import CartItemCreate, CartItemUpdate, CartItemResponse
from utils.token import get_current_user

router = APIRouter()

@router.get("", response_model=List[CartItemResponse])
async def get_my_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """獲取當前登入使用者的購物車內容。"""
    cart_items = (
        db.query(CartItem)
        .options(joinedload(CartItem.product).joinedload(Product.seller)) # 預先載入商品及其賣家資訊
        .filter(CartItem.user_id == current_user.id)
        .order_by(CartItem.added_at.desc())
        .all()
    )
    return cart_items

@router.post("", response_model=CartItemResponse)
async def add_item_to_cart(item_data: CartItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """將商品加入購物車。如果已存在，則增加數量。"""
    # 檢查商品是否存在
    product = db.query(Product).filter(Product.id == item_data.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到此商品")

    # 檢查購物車中是否已有此商品
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item_data.product_id
    ).first()

    if cart_item:
        # 如果已存在，更新數量
        cart_item.quantity += item_data.quantity
    else:
        # 如果不存在，建立新項目
        cart_item = CartItem(**item_data.dict(), user_id=current_user.id)
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart_item)
    return cart_item

@router.put("/{product_id}", response_model=CartItemResponse)
async def update_cart_item_quantity(product_id: int, item_data: CartItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新購物車中特定商品的數量。"""
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).first()

    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="購物車中找不到此商品")

    if item_data.quantity <= 0:
        # 如果數量小於等於 0，則刪除該項目
        db.delete(cart_item)
    else:
        cart_item.quantity = item_data.quantity
    
    db.commit()
    # 如果項目被刪除，cart_item 會過期，所以我們回傳更新後的項目或一個確認訊息
    if item_data.quantity > 0:
        db.refresh(cart_item)
        return cart_item
    return {"detail": "Item removed"} # 或者直接回傳 204

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_cart(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """從購物車中移除一項商品。"""
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).first()

    if cart_item:
        db.delete(cart_item)
        db.commit()
    
    return None # 回傳 204 No Content

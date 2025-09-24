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

# Prefix 和 Tags 由 main.py 統一管理
router = APIRouter()

@router.get("", response_model=List[CartItemResponse])
def get_my_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """獲取當前登入使用者的購物車內容。"""
    cart_items = (
        db.query(CartItem)
        .options(
            joinedload(CartItem.product).joinedload(Product.seller), # 預先載入商品及其賣家
            joinedload(CartItem.product).joinedload(Product.images), # 同時載入商品圖片
            joinedload(CartItem.product).joinedload(Product.category) # 同時載入商品分類
        )
        .filter(CartItem.user_id == current_user.id)
        .order_by(CartItem.added_at.desc())
        .all()
    )
    return cart_items

# --- 路徑修正為 /items ---
@router.post("/items", response_model=CartItemResponse)
def add_item_to_cart(item_data: CartItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """將商品加入購物車。如果已存在，則增加數量。"""
    product = db.query(Product).filter(Product.id == item_data.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到此商品")
    if product.status != "available":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="此商品目前無法購買")

    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item_data.product_id
    ).first()

    if cart_item:
        # 如果已存在，更新數量
        new_quantity = cart_item.quantity + item_data.quantity
        # --- 關鍵：加入庫存檢查 ---
        if new_quantity > product.stock_quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"庫存不足，剩餘 {product.stock_quantity} 件")
        cart_item.quantity = new_quantity
    else:
        # 如果不存在，建立新項目
        # --- 關鍵：加入庫存檢查 ---
        if item_data.quantity > product.stock_quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"庫存不足，剩餘 {product.stock_quantity} 件")
        cart_item = CartItem(**item_data.dict(), user_id=current_user.id)
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart_item)
    return cart_item

# --- 路徑修正為 /items/{product_id} ---
@router.put("/items/{product_id}", response_model=CartItemResponse)
def update_cart_item_quantity(product_id: int, item_data: CartItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新購物車中特定商品的數量。"""
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).first()

    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="購物車中找不到此商品")

    # --- 關鍵：加入庫存檢查 ---
    if item_data.quantity > cart_item.product.stock_quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"庫存不足，剩餘 {cart_item.product.stock_quantity} 件")

    cart_item.quantity = item_data.quantity
    
    db.commit()
    db.refresh(cart_item)
    return cart_item

# --- 路徑修正為 /items/{product_id} ---
@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item_from_cart(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """從購物車中移除一項商品。"""
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).first()

    if cart_item:
        db.delete(cart_item)
        db.commit()
    
    return None

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_my_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """清空當前登入使用者的整個購物車。"""
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return None

# ---FILE: routers/wishpool.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List
from datetime import datetime

from database.db import get_db
from models.user import User
from models.product import Product
from models.order import Order, OrderItem
from models.address import Address
from models.wishpool import Wishpool, WishpoolFavorite, WishpoolInvite
from schemas.wishpool_schema import (
    WishpoolCreate, WishpoolUpdate, WishpoolResponse, 
    WishpoolInviteCreate, WishpoolInviteResponse, WishpoolFulfillRequest
)
from utils.token import get_current_user

router_wishpool = APIRouter(
    prefix="/wishpool",
    tags=["許願池 (Wishpool)"]
)

@router_wishpool.post("", response_model=WishpoolResponse, status_code=status.HTTP_201_CREATED)
def create_wish(
    wish_data: WishpoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # --- [修改] 強制尋找預設地址並建立快照 ---
    default_address = db.query(Address).filter(
        Address.user_id == current_user.id,
        Address.is_default == True
    ).first()
    
    if not default_address:
        # 如果沒有預設地址，嘗試找任何一個地址
        default_address = db.query(Address).filter(Address.user_id == current_user.id).first()
        
    if not default_address:
        raise HTTPException(status_code=400, detail="請先至個人中心設定收貨地址")

    # 建立地址快照 JSON
    address_snapshot = {
        "recipient_name": default_address.recipient_name,
        "phone_number": default_address.phone_number,
        "full_address": default_address.displayAddress
    }

    new_wish = Wishpool(
        **wish_data.model_dump(),
        user_id=current_user.id,
        shipping_address=address_snapshot # 儲存快照
    )
    db.add(new_wish)
    db.commit()
    db.refresh(new_wish)
    return WishpoolResponse.from_orm(new_wish)

# ... (get_all_wishes, get_wish_by_id, update_wish, delete_wish, favorite, unfavorite 保持不變) ...
# ... (請保留原本的程式碼，這裡省略) ...

@router_wishpool.get("", response_model=List[WishpoolResponse])
def get_all_wishes(db: Session = Depends(get_db)):
    wishes = db.query(Wishpool).filter(Wishpool.status == 'open').options(
        joinedload(Wishpool.user), joinedload(Wishpool.matched_item) 
    ).order_by(desc(Wishpool.created_at)).all()
    
    response = []
    for wish in wishes:
        wish_response = WishpoolResponse.from_orm(wish)
        wish_response.like_count = db.query(WishpoolFavorite).filter(WishpoolFavorite.wishpool_id == wish.id).count()
        response.append(wish_response)
    return response

@router_wishpool.get("/{wish_id}", response_model=WishpoolResponse)
def get_wish_by_id(wish_id: int, db: Session = Depends(get_db)):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).options(
        joinedload(Wishpool.user), joinedload(Wishpool.matched_item)
    ).first()
    
    if not wish: raise HTTPException(status_code=404, detail="找不到此許願單")
    wish_response = WishpoolResponse.from_orm(wish)
    wish_response.like_count = db.query(WishpoolFavorite).filter(WishpoolFavorite.wishpool_id == wish.id).count()
    return wish_response

@router_wishpool.put("/{wish_id}", response_model=WishpoolResponse)
def update_wish(wish_id: int, wish_data: WishpoolUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).first()
    if not wish: raise HTTPException(status_code=404, detail="找不到此許願單")
    if wish.user_id != current_user.id: raise HTTPException(status_code=403, detail="您沒有權限修改此許願單")
    update_data = wish_data.model_dump(exclude_unset=True)
    for key, value in update_data.items(): setattr(wish, key, value)
    db.commit()
    db.refresh(wish)
    return WishpoolResponse.from_orm(wish)

@router_wishpool.delete("/{wish_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wish(wish_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).first()
    if not wish: raise HTTPException(status_code=404, detail="找不到此許願單")
    if wish.user_id != current_user.id: raise HTTPException(status_code=403, detail="您沒有權限刪除此許願單")
    db.delete(wish)
    db.commit()
    return None

@router_wishpool.post("/{wish_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def favorite_wish(wish_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).first()
    if not wish: raise HTTPException(status_code=404, detail="找不到此許願單")
    existing_fav = db.query(WishpoolFavorite).filter(WishpoolFavorite.wishpool_id == wish_id, WishpoolFavorite.user_id == current_user.id).first()
    if not existing_fav:
        new_fav = WishpoolFavorite(wishpool_id=wish_id, user_id=current_user.id)
        db.add(new_fav)
        db.commit()
    return None

@router_wishpool.delete("/{wish_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def unfavorite_wish(wish_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_fav = db.query(WishpoolFavorite).filter(WishpoolFavorite.wishpool_id == wish_id, WishpoolFavorite.user_id == current_user.id).first()
    if existing_fav: db.delete(existing_fav)
    db.commit()
    return None

# --- [修改] 賣家接單 (Fulfill) ---
@router_wishpool.post("/{wish_id}/fulfill", response_model=WishpoolResponse)
def fulfill_wish(
    wish_id: int,
    fulfill_data: WishpoolFulfillRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此許願單")
    
    if wish.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="您不能接自己的單")
        
    if wish.status != 'open':
        raise HTTPException(status_code=400, detail="此願望已被接單或關閉")

    matched_product = None

    # --- 模式 A: 使用現有商品 ---
    if fulfill_data.product_id:
        matched_product = db.query(Product).filter(
            Product.id == fulfill_data.product_id,
            Product.seller_id == current_user.id
        ).first()
        
        if not matched_product:
            raise HTTPException(status_code=404, detail="找不到此商品或商品不屬於您")
            
        # [修改] 檢查庫存是否足夠覆蓋願望數量
        if matched_product.stock_quantity < wish.quantity:
             raise HTTPException(status_code=400, detail=f"您的商品庫存不足 ({matched_product.stock_quantity})，買家需要 {wish.quantity} 個")
             
        # 扣除庫存
        matched_product.stock_quantity -= wish.quantity
        if matched_product.stock_quantity <= 0:
            matched_product.status = "sold"

    # --- 模式 B: 快速接單 (自動建立商品) ---
    else:
        new_product_name = fulfill_data.new_product_name or f"回應願望：{wish.title}"
        matched_product = Product(
            seller_id=current_user.id,
            name=new_product_name,
            description=f"此商品是為了回應願望 #{wish.id} 而自動建立的。",
            price=wish.price, 
            category_id=wish.category_id if wish.category_id else 1, 
            
            # [修改] 庫存設定為願望數量 (然後馬上被訂走)
            stock_quantity=wish.quantity, 
            
            status="reserved", 
            sales_count=0,
            review_count=0,
        )
        if fulfill_data.new_product_image_url:
            from models.product import ProductImage
            matched_product.images.append(ProductImage(image_url=fulfill_data.new_product_image_url, display_order=0))
            
        db.add(matched_product)
        db.flush()

    # --- 自動建立訂單 (Order) ---
    # 使用願望中的地址快照
    shipping_cost = wish.shipping_cost 
    shipping_name = wish.shipping_name
    total_amount = (wish.price * wish.quantity) + shipping_cost

    new_order = Order(
        user_id=wish.user_id,
        total_amount=total_amount,
        shipping_address=wish.shipping_address, # 使用 JSON 快照
        shipping_method={"id": 0, "name": shipping_name, "cost": shipping_cost},
        status="preparing", # 賣家已接單 -> 待出貨
        payment_status="unpaid", 
        status_history=[{
            "status": "preparing",
            "timestamp": datetime.utcnow().isoformat(),
            "description": f"賣家 {current_user.nickname} 已接單，訂單自動建立。"
        }]
    )
    db.add(new_order)
    db.flush()

    # 建立訂單項目
    order_item = OrderItem(
        order_id=new_order.id,
        product_id=matched_product.id,
        quantity=wish.quantity,
        price_at_purchase=wish.price
    )
    db.add(order_item)

    # 更新願望狀態
    wish.status = 'matched'
    wish.matched_item_id = matched_product.id
    
    if matched_product.status == 'available': matched_product.status = 'reserved'

    db.commit()
    db.refresh(wish)
    db.refresh(wish, ['user', 'matched_item'])
    
    wish_response = WishpoolResponse.from_orm(wish)
    wish_response.like_count = db.query(WishpoolFavorite).filter(WishpoolFavorite.wishpool_id == wish.id).count()
    
    return wish_response

# (Invite 相關 API 保持不變，省略...)
# ... send_invite, get_received_invites, get_sent_invites, accept_invite, reject_invite ...
@router_wishpool.post("/{wish_id}/invite", response_model=WishpoolInviteResponse)
def send_invite(wish_id: int, invite_data: WishpoolInviteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).first()
    if not wish: raise HTTPException(status_code=404, detail="找不到此許願單")
    if wish.user_id == current_user.id: raise HTTPException(status_code=400, detail="您不能向自己的許願單發送邀請")
    new_invite = WishpoolInvite(wishpool_id=wish_id, seller_id=current_user.id, product_id=invite_data.product_id, message=invite_data.message)
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)
    return WishpoolInviteResponse.from_orm(new_invite)

@router_wishpool.get("/invites/received", response_model=List[WishpoolInviteResponse])
def get_received_invites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invites = db.query(WishpoolInvite).join(Wishpool).filter(Wishpool.user_id == current_user.id).options(joinedload(WishpoolInvite.seller), joinedload(WishpoolInvite.product), joinedload(WishpoolInvite.wishpool)).order_by(desc(WishpoolInvite.created_at)).all()
    return [WishpoolInviteResponse.from_orm(invite) for invite in invites]

@router_wishpool.get("/invites/sent", response_model=List[WishpoolInviteResponse])
def get_sent_invites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invites = db.query(WishpoolInvite).filter(WishpoolInvite.seller_id == current_user.id).options(joinedload(WishpoolInvite.wishpool), joinedload(WishpoolInvite.product)).order_by(desc(WishpoolInvite.created_at)).all()
    return [WishpoolInviteResponse.from_orm(invite) for invite in invites]

@router_wishpool.patch("/invites/{invite_id}/accept", response_model=WishpoolInviteResponse)
def accept_invite(invite_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invite = db.query(WishpoolInvite).filter(WishpoolInvite.id == invite_id).first()
    if not invite: raise HTTPException(status_code=404, detail="找不到此邀請")
    wish = db.query(Wishpool).filter(Wishpool.id == invite.wishpool_id).first()
    if not wish or wish.user_id != current_user.id: raise HTTPException(status_code=403, detail="您沒有權限接受此邀請")
    if wish.status != 'open': raise HTTPException(status_code=400, detail="此願望已被匹配或已關閉")
    invite.status = 'accepted'
    wish.status = 'matched'
    wish.matched_item_id = invite.product_id
    db.query(WishpoolInvite).filter(WishpoolInvite.wishpool_id == wish.id, WishpoolInvite.status == 'pending', WishpoolInvite.id != invite_id).update({"status": "rejected"})
    db.commit()
    db.refresh(invite)
    return WishpoolInviteResponse.from_orm(invite)

@router_wishpool.patch("/invites/{invite_id}/reject", response_model=WishpoolInviteResponse)
def reject_invite(invite_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invite = db.query(WishpoolInvite).filter(WishpoolInvite.id == invite_id).first()
    if not invite: raise HTTPException(status_code=404, detail="找不到此邀請")
    wish = db.query(Wishpool).filter(Wishpool.id == invite.wishpool_id).first()
    if not wish or wish.user_id != current_user.id: raise HTTPException(status_code=403, detail="您沒有權限拒絕此邀請")
    invite.status = 'rejected'
    db.commit()
    db.refresh(invite)
    return WishpoolInviteResponse.from_orm(invite)

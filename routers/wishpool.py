# ---FILE: routers/wishpool.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, subqueryload
from sqlalchemy import func, desc
from typing import List

from database.db import get_db
from models.user import User
from models.product import Product
from models.wishpool import Wishpool, WishpoolFavorite, WishpoolInvite
from schemas.wishpool_schema import WishpoolCreate, WishpoolUpdate, WishpoolResponse, WishpoolInviteCreate, WishpoolInviteResponse
from utils.token import get_current_user

router_wishpool = APIRouter(
    prefix="/wishpool",
    tags=["許願池 (Wishpool)"]
)

# ... (其他函式保持不變) ...

@router_wishpool.post("", response_model=WishpoolResponse, status_code=status.HTTP_201_CREATED)
def create_wish(
    wish_data: WishpoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_wish = Wishpool(
        **wish_data.model_dump(),
        user_id=current_user.id
    )
    db.add(new_wish)
    db.commit()
    db.refresh(new_wish)
    return WishpoolResponse.from_orm(new_wish)


@router_wishpool.get("", response_model=List[WishpoolResponse])
def get_all_wishes(
    db: Session = Depends(get_db)
):
    wishes = db.query(Wishpool).filter(Wishpool.status == 'open').options(
        joinedload(Wishpool.user), 
        joinedload(Wishpool.matched_item) 
    ).order_by(desc(Wishpool.created_at)).all()
    
    response = []
    for wish in wishes:
        wish_response = WishpoolResponse.from_orm(wish)
        wish_response.like_count = db.query(WishpoolFavorite).filter(WishpoolFavorite.wishpool_id == wish.id).count()
        response.append(wish_response)
        
    return response

@router_wishpool.get("/{wish_id}", response_model=WishpoolResponse)
def get_wish_by_id(
    wish_id: int,
    db: Session = Depends(get_db)
):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).options(
        joinedload(Wishpool.user),
        joinedload(Wishpool.matched_item)
    ).first()
    
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此許願單")
        
    wish_response = WishpoolResponse.from_orm(wish)
    wish_response.like_count = db.query(WishpoolFavorite).filter(WishpoolFavorite.wishpool_id == wish.id).count()
    return wish_response

@router_wishpool.put("/{wish_id}", response_model=WishpoolResponse)
def update_wish(
    wish_id: int,
    wish_data: WishpoolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此許願單")
    if wish.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="您沒有權限修改此許願單")

    update_data = wish_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(wish, key, value)
    
    db.commit()
    db.refresh(wish)
    return WishpoolResponse.from_orm(wish)

@router_wishpool.delete("/{wish_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wish(
    wish_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此許願單")
    if wish.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="您沒有權限刪除此許願單")

    db.delete(wish)
    db.commit()
    return None

@router_wishpool.post("/{wish_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def favorite_wish(
    wish_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此許願單")
        
    existing_fav = db.query(WishpoolFavorite).filter(
        WishpoolFavorite.wishpool_id == wish_id,
        WishpoolFavorite.user_id == current_user.id
    ).first()
    
    if not existing_fav:
        new_fav = WishpoolFavorite(wishpool_id=wish_id, user_id=current_user.id)
        db.add(new_fav)
        db.commit()
    
    return None

@router_wishpool.delete("/{wish_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def unfavorite_wish(
    wish_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_fav = db.query(WishpoolFavorite).filter(
        WishpoolFavorite.wishpool_id == wish_id,
        WishpoolFavorite.user_id == current_user.id
    ).first()
    
    if existing_fav:
        db.delete(existing_fav)
        db.commit()
    
    return None

# --- [修改] 發送邀請：不再強制檢查 product_id ---
@router_wishpool.post("/{wish_id}/invite", response_model=WishpoolInviteResponse)
def send_invite(
    wish_id: int,
    invite_data: WishpoolInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    wish = db.query(Wishpool).filter(Wishpool.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此許願單")
    
    if wish.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="您不能向自己的許願單發送邀請")
        
    # 只有當有傳入 product_id 時才檢查商品
    if invite_data.product_id:
        product = db.query(Product).filter(
            Product.id == invite_data.product_id,
            Product.seller_id == current_user.id 
        ).first()
        if not product:
             # 如果傳了 ID 但找不到商品，還是報錯比較安全
            raise HTTPException(status_code=404, detail="找不到此商品或商品不屬於您")

    new_invite = WishpoolInvite(
        wishpool_id=wish_id,
        seller_id=current_user.id,
        product_id=invite_data.product_id, # 可以是 None
        message=invite_data.message
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)
    return WishpoolInviteResponse.from_orm(new_invite)

@router_wishpool.get("/invites/received", response_model=List[WishpoolInviteResponse])
def get_received_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invites = db.query(WishpoolInvite).join(Wishpool).filter(
        Wishpool.user_id == current_user.id
    ).options(
        joinedload(WishpoolInvite.seller),
        joinedload(WishpoolInvite.product),
        joinedload(WishpoolInvite.wishpool) 
    ).order_by(desc(WishpoolInvite.created_at)).all()
    
    return [WishpoolInviteResponse.from_orm(invite) for invite in invites]

@router_wishpool.get("/invites/sent", response_model=List[WishpoolInviteResponse])
def get_sent_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invites = db.query(WishpoolInvite).filter(
        WishpoolInvite.seller_id == current_user.id
    ).options(
        joinedload(WishpoolInvite.wishpool), 
        joinedload(WishpoolInvite.product)   
    ).order_by(desc(WishpoolInvite.created_at)).all()
    
    return [WishpoolInviteResponse.from_orm(invite) for invite in invites]


@router_wishpool.patch("/invites/{invite_id}/accept", response_model=WishpoolInviteResponse)
def accept_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invite = db.query(WishpoolInvite).filter(WishpoolInvite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="找不到此邀請")
    
    wish = db.query(Wishpool).filter(Wishpool.id == invite.wishpool_id).first()
    if not wish or wish.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="您沒有權限接受此邀請")
        
    if wish.status != 'open':
        raise HTTPException(status_code=400, detail="此願望已被匹配或已關閉")

    invite.status = 'accepted'
    wish.status = 'matched'
    # 如果沒有 product_id，這裡會是 None，這是可接受的
    wish.matched_item_id = invite.product_id
    
    db.query(WishpoolInvite).filter(
        WishpoolInvite.wishpool_id == wish.id,
        WishpoolInvite.status == 'pending',
        WishpoolInvite.id != invite_id
    ).update({"status": "rejected"})

    db.commit()
    db.refresh(invite)
    return WishpoolInviteResponse.from_orm(invite)

@router_wishpool.patch("/invites/{invite_id}/reject", response_model=WishpoolInviteResponse)
def reject_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invite = db.query(WishpoolInvite).filter(WishpoolInvite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="找不到此邀請")
    
    wish = db.query(Wishpool).filter(Wishpool.id == invite.wishpool_id).first()
    if not wish or wish.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="您沒有權限拒絕此邀請")
        
    invite.status = 'rejected'
    db.commit()
    db.refresh(invite)
    return WishpoolInviteResponse.from_orm(invite)

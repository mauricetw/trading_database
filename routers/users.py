# --- FILE: routers/user.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database.db import get_db
from models.user import User
from schemas.user_schema import UserProfileResponse, UserPublicProfile, UserUpdate
from utils.token import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserPublicProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    獲取當前登入使用者的公開個人資料。
    這個 API 會透過 JWT Token 自動識別使用者身份。
    """
    return current_user

@router.put("/me")
async def update_current_user_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新當前登入使用者的個人資料。
    - 支援部分更新 (只傳送有變更的欄位)。
    """
    # exclude_unset=True 確保我們只獲取前端有傳送的欄位
    update_data = user_data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile_by_id(
    user_id: int, 
    db: Session = Depends(get_db)
):
    """
    根據使用者 ID 獲取特定使用者的公開個人資料。
    此 API 不需要登入即可存取。
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="找不到此使用者"
        )
    
    # 回傳與 UserProfileResponse schema 匹配的巢狀結構
    return {"user": user}

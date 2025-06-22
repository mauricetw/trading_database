from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
from database.db import get_db
from models.user import User
from schemas.user_schema import UserCreate, UserLogin, ForgotPasswordRequest, ResetPasswordRequest, UserResponse
from utils.hashing import hash_password, verify_password
from utils.token import create_reset_token, verify_reset_token, create_access_token
from mail_config import send_reset_email
import os

router = APIRouter()

# 註冊 API
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # 檢查帳號是否已經存在
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="帳號已存在")

    # 新增使用者
    new_user = User(
        username=user.username,
        password=hash_password(user.password),
        email=user.email,
        registered_at=datetime.utcnow(),
        is_verified=False,  #預設未驗證
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 生成 token
    token = create_access_token({"user_id": new_user.id})

    # 返回帶 token 的回應
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "token": token,
        "registeredAt": new_user.registered_at.isoformat(),
        "lastLoginAt": None,
        "phoneNumber": new_user.phone_number,
        "avatarUrl": new_user.avatar_url,
        "bio": new_user.bio,
        "schoolName": new_user.school_name,
        "isVerified": new_user.is_verified,
        "roles": new_user.roles.split(',') if new_user.roles else [],
        "isSeller": new_user.is_seller,
        "sellerName": new_user.seller_name,
        "sellerDescription": new_user.seller_description,
        "sellerRating": new_user.seller_rating,
        "productCount": new_user.product_count,
    }

# 登入 API
@router.post("/login", response_model=UserResponse)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    # 檢查帳號是否存在
    db_user = db.query(User).filter((User.username == user.login) | (User.email == user.login)).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="帳號或密碼錯誤")

    # 更新最後登入時間
    db_user.last_login_at = datetime.utcnow()
    db.commit()

    # 生成 Token
    access_token_expires = timedelta(minutes=30)
    token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )

    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "token": token,
        "registeredAt": db_user.registered_at.isoformat(),
        "lastLoginAt": db_user.last_login_at.isoformat() if db_user.last_login_at else None,
        "phoneNumber": db_user.phone_number,
        "avatarUrl": db_user.avatar_url,
        "bio": db_user.bio,
        "schoolName": db_user.school_name,
        "isVerified": db_user.is_verified,
        "roles": db_user.roles.split(',') if db_user.roles else [],
        "isSeller": db_user.is_seller,
        "sellerName": db_user.seller_name,
        "sellerDescription": db_user.seller_description,
        "sellerRating": db_user.seller_rating,
        "productCount": db_user.product_count
    }

# 忘記密碼 API
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):

    try:
        # 根據 username 或 email 查找使用者
        user = db.query(User).filter((User.username == request.login) | (User.email == request.login)).first()

        if not user:
            raise HTTPException(status_code=404, detail="找不到對應的帳號或電子郵件")

        # 產生重設密碼 token 並發送郵件
        token = create_reset_token(user.id)

         # 確保 BACKEND_URL 環境變數存在
        BACKEND_URL = os.getenv("BACKEND_URL")
        if not BACKEND_URL:
            raise HTTPException(status_code=500, detail="BACKEND_URL 未設定")
    
        #reset_link = f"app://reset-password/{user.id}?token={token}"

        #發送密碼
        send_reset_email(user.email)

        return {"message": "密碼重設信已寄出"}
    
    except Exception as e:
        print(f"Error in forgot_password: {e}")
        raise HTTPException(status_code=500, detail=f"伺服器錯誤：{str(e)}")

    

# 重設密碼 API
@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    # 驗證 token
    user_id = verify_reset_token(request.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Token 無效或過期")

    # 更新密碼
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到使用者")

    user.password = hash_password(request.new_password)
    db.commit()

    return {"message": "密碼已成功更新"}

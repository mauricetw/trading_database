from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from models import user
from schemas.user_schema import UserCreate, UserLogin, ForgotPasswordRequest, ResetPasswordRequest, UserResponse
from utils.hashing import hash_password, verify_password
from utils.token import create_reset_token, verify_reset_token
from mail_config import send_reset_email
import os

router = APIRouter()

# 註冊 API
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # 檢查帳號是否已經存在
    existing_user = db.query(User).filter(User.account == user.account).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="帳號已存在")

    # 新增使用者
    new_user = User(
        account=user.account,
        password=hash_password(user.password),
        email=user.email
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# 登入 API
@router.post("/login", response_model=UserResponse)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    # 檢查帳號是否存在
    db_user = db.query(User).filter((User.account == user.login) | (User.email == user.login)).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="帳號或密碼錯誤")

    return db_user

# 忘記密碼 API
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # 檢查帳號是否存在
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到帳號")

    # 產生 token 並寄送重設密碼郵件
    token = create_reset_token(user.id)
    BACKEND_URL = os.getenv("BACKEND_URL")

    reset_link = f"{BACKEND_URL}/reset-password?token={token}"

    send_reset_email(user.email, reset_link)

    return {"message": "密碼重設信已寄出"}

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

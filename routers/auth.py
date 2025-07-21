from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from database.db import get_db
from models.user import User
from schemas.auth_schema import (
    UserCreate, UserLogin, ForgotPasswordRequest, ResetPasswordRequest, 
    VerifyCodeRequest, LoginResponse, AuthResponse, UserDataForAuth # 確保 UserDataForAuth 已引入
)
from utils.hashing import hash_password, verify_password
from utils.token import create_access_token, create_reset_token, verify_reset_token
from mail_config import send_reset_email
import random

router = APIRouter()

# --- 重構後的註冊 API ---
@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        or_(User.username == user_data.username, User.email == user_data.email)
    ).first()
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="此使用者名稱已被註冊")
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="此電子郵件已被註冊")

    new_user = User(
        username=user_data.username,
        password=hash_password(user_data.password),
        email=user_data.email,
        phone_number=user_data.phone_number,
        avatar_url=user_data.avatar_url,
        bio=user_data.bio,
        school_name=user_data.school_name,
        registered_at=datetime.utcnow(),
        is_verified=False,
        roles=["user"]
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": str(new_user.id)})

    # --- 錯誤修正 ---
    # Pydantic 的 LoginResponse 模型期望 user 欄位是一個 UserDataForAuth 的實例。
    # 我們需要手動使用 .from_orm() 將 SQLAlchemy 的 new_user 物件轉換成 Pydantic 模型。
    user_for_response = UserDataForAuth.from_orm(new_user)

    return LoginResponse(
        token=AuthResponse(access_token=access_token),
        user=user_for_response # 傳入轉換後的 Pydantic 模型
    )

# --- 重構後的登入 API ---
@router.post("/login", response_model=LoginResponse)
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        or_(User.username == form_data.login, User.email == form_data.login)
    ).first()
    
    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)

    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    # --- 錯誤修正 (與註冊 API 相同的原因) ---
    # 手動將 SQLAlchemy 的 db_user 物件轉換成 UserDataForAuth Pydantic 模型。
    user_for_response = UserDataForAuth.from_orm(db_user)

    return LoginResponse(
        token=AuthResponse(access_token=access_token),
        user=user_for_response # 傳入轉換後的 Pydantic 模型
    )

# --- 忘記密碼流程 (保持不變) ---
@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(or_(User.username == request.login, User.email == request.login)).first()

    if not user:
        return {"message": "如果帳號存在，密碼重設信將會寄到您的信箱。"}

    code = str(random.randint(100000, 999999))
    
    try:
        send_reset_email(user.email, code)
    except Exception as e:
        print(f"Error sending email to {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="無法寄送郵件，請稍後再試。")

    user.verification_code = code
    user.code_expiration = datetime.utcnow() + timedelta(minutes=10)
    db.commit()

    return {"message": "如果帳號存在，密碼重設信將會寄到您的信箱。"}


@router.post("/verify-code")
async def verify_code(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(or_(User.username == request.login, User.email == request.login)).first()
    
    if not user or not user.verification_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無效的驗證請求")

    if user.verification_code != request.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="驗證碼錯誤")

    if datetime.utcnow() > user.code_expiration:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="驗證碼已過期")

    user.verification_code = None
    user.code_expiration = None
    db.commit()

    reset_token = create_reset_token(data={"sub": str(user.id)})
    return {"message": "驗證成功", "reset_token": reset_token}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        payload = verify_reset_token(request.token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 無效")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 無效或過期")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到使用者")

    if verify_password(request.new_password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密碼不得與舊密碼相同")

    user.password = hash_password(request.new_password)
    db.commit()

    return {"message": "密碼已成功更新"}

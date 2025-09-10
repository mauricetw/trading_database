# --- FILE: routers/auth.py (重構版) ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
import random, string

from database.db import get_db
from models.user import User
from models.verification import VerificationCode, CodePurpose # 引入新模型
from schemas.auth_schema import (
    UserCreate, UserLogin, ForgotPasswordRequest, ResetPasswordRequest,
    VerifyCodeRequest, AuthSuccessResponse, TokenSchema, UserResponseSchema,
    SendVerificationCodeRequest
)
from utils.hashing import hash_password, verify_password
from utils.token import create_access_token, create_reset_token, verify_reset_token
from mail_config import send_reset_email # 假設寄信函式

router = APIRouter()

ALLOWED_EMAIL_DOMAIN = "@mail.ntust.edu.tw"

async def _send_and_save_code(email: str, purpose: CodePurpose, db: Session):
    """輔助函式：產生、儲存並寄送驗證碼"""
    code = ''.join(random.choices(string.digits, k=6))
    
    # 刪除該 email 和 purpose 的舊有驗證碼
    db.query(VerificationCode).filter(
        VerificationCode.email == email,
        VerificationCode.purpose == purpose
    ).delete()

    # --- 設定此驗證碼的過期時間 ---
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # 4. 建立新的驗證碼資料庫紀錄，並包含過期時間
    new_code = VerificationCode(
        email=email, 
        code=code, 
        expires_at=expires_at, # <--- 將過期時間儲存到資料庫
        purpose=purpose
    )
    db.add(new_code)
    db.commit()

    try:
        # 這裡可以根據 purpose 客製化郵件主旨和內容
        send_reset_email(email, code)
    except Exception as e:
        print(f"Error sending email to {email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="無法寄送郵件")

@router.post("/send-verification-code", status_code=status.HTTP_200_OK)
async def send_registration_code(request: SendVerificationCodeRequest, db: Session = Depends(get_db)):
    if not request.email.endswith(ALLOWED_EMAIL_DOMAIN):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="僅允許台科大信箱")

    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="此電子郵件已被註冊")

    await _send_and_save_code(request.email, CodePurpose.REGISTRATION, db)
    return {"message": "驗證碼已成功寄至您的信箱"}

@router.post("/register", response_model=AuthSuccessResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 驗證驗證碼
    code_entry = db.query(VerificationCode).filter(
        VerificationCode.email == user_data.email,
        VerificationCode.purpose == CodePurpose.REGISTRATION,
        VerificationCode.code == user_data.code
    ).first()

    if not code_entry:
        raise HTTPException(status_code=400, detail="驗證碼錯誤")
    if datetime.utcnow() > code_entry.expires_at:
        raise HTTPException(status_code=400, detail="驗證碼已過期")

    # 檢查使用者是否存在
    if db.query(User).filter(or_(User.nickname == user_data.nickname, User.email == user_data.email)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="使用者名稱或電子郵件已被註冊")

    # 建立新使用者 (已修復 Bug)
    new_user = User(
        nickname=user_data.nickname,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        is_verified=True
    )
    db.add(new_user)
    db.delete(code_entry) # 刪除已使用的驗證碼
    db.commit()
    db.refresh(new_user)

    # 回傳 Token 和使用者資料
    access_token = create_access_token(data={"sub": str(new_user.id)})
    return AuthSuccessResponse(
        token=TokenSchema(access_token=access_token),
        user=UserResponseSchema.from_orm(new_user)
    )

@router.post("/login", response_model=AuthSuccessResponse)
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        or_(User.nickname == form_data.login, User.email == form_data.login)
    ).first()
    
    if not db_user or not verify_password(form_data.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)

    access_token = create_access_token(data={"sub": str(db_user.id)})
    return AuthSuccessResponse(
        token=TokenSchema(access_token=access_token),
        user=UserResponseSchema.from_orm(db_user)
    )

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.login).first()
    if user:
        await _send_and_save_code(user.email, CodePurpose.PASSWORD_RESET, db)
    # 為了安全，無論使用者是否存在，都回傳相同的成功訊息
    return {"message": "如果帳號存在，密碼重設信將會寄到您的信箱。"}

@router.post("/verify-code")
async def verify_code(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    code_entry = db.query(VerificationCode).filter(
        VerificationCode.email == request.login,
        VerificationCode.purpose == CodePurpose.PASSWORD_RESET,
        VerificationCode.code == request.code
    ).first()
    
    if not code_entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="驗證碼錯誤")
    if datetime.utcnow() > code_entry.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="驗證碼已過期")
    
    user = db.query(User).filter(User.email == request.login).first()
    if not user:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到使用者")

    db.delete(code_entry) # 驗證成功後刪除
    db.commit()

    reset_token = create_reset_token(data={"sub": str(user.id)})
    return {"reset_token": reset_token}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    payload = verify_reset_token(request.token)
    user_id = payload.get("sub")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到使用者")

    if verify_password(request.new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密碼不得與舊密碼相同")

    user.password_hash = hash_password(request.new_password)
    db.commit()

    return {"message": "密碼已成功更新"}

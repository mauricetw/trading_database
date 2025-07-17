from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from database.db import get_db
from models.user import User
from schemas.auth_schema import (
    UserCreate, UserLogin, ForgotPasswordRequest, ResetPasswordRequest, 
    VerifyCodeRequest, LoginResponse, AuthResponse, UserDataForAuth
)
from utils.hashing import hash_password, verify_password
from utils.token import create_access_token, create_reset_token, verify_reset_token
from mail_config import send_reset_email
import random

router = APIRouter()

# --- 重構後的註冊 API ---
@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 檢查 email 或 username 是否已經存在
    existing_user = db.query(User).filter(
        or_(User.username == user_data.username, User.email == user_data.email)
    ).first()
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="此使用者名稱已被註冊")
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="此電子郵件已被註冊")

    # 建立新的使用者物件
    new_user = User(
        username=user_data.username,
        password=hash_password(user_data.password),
        email=user_data.email,
        phone_number=user_data.phone_number,
        avatar_url=user_data.avatar_url,
        bio=user_data.bio,
        school_name=user_data.school_name,
        registered_at=datetime.utcnow(),
        is_verified=False, # 預設未驗證
        roles=["user"] # 預設角色
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # --- 安全性與一致性修正 ---
    # 統一使用 user.id 作為 token 的 subject (sub)
    access_token = create_access_token(data={"sub": str(new_user.id)})

    # --- 程式碼品質提升 ---
    # 不再手動建立字典，而是讓 Pydantic 自動從 ORM 物件轉換。
    # 這樣更簡潔、更健壯，且不會有手動處理 `roles` 的 bug。
    return LoginResponse(
        token=AuthResponse(access_token=access_token),
        user=new_user
    )

# --- 重構後的登入 API ---
@router.post("/login", response_model=LoginResponse)
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    # 允許使用 username 或 email 登入
    db_user = db.query(User).filter(
        or_(User.username == form_data.login, User.email == form_data.login)
    ).first()
    
    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最後登入時間
    db_user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)

    # 統一使用 user.id 作為 token 的 subject
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    # 同樣，直接回傳 ORM 物件，讓 Pydantic 處理
    return LoginResponse(
        token=AuthResponse(access_token=access_token),
        user=db_user
    )

# --- 優化後的忘記密碼流程 ---
@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(or_(User.username == request.login, User.email == request.login)).first()

    # 為了安全，即使找不到使用者，也回傳成功的訊息，避免被探測帳號是否存在
    if not user:
        return {"message": "如果帳號存在，密碼重設信將會寄到您的信箱。"}

    # 產生一個 6 位數的隨機驗證碼
    code = str(random.randint(100000, 999999))
    
    # 寄送郵件
    try:
        send_reset_email(user.email, code)
    except Exception as e:
        # 即使寄信失敗，也不要讓使用者知道，但後端需要記錄錯誤
        print(f"Error sending email to {user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="無法寄送郵件，請稍後再試。")

    # 儲存驗證碼和過期時間到資料庫
    user.verification_code = code
    user.code_expiration = datetime.utcnow() + timedelta(minutes=10) # 10 分鐘有效
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

    # 驗證通過後，清除驗證碼，並產生一個一次性的重設密碼 token
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

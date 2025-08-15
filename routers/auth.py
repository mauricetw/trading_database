# --- FILE: routers/auth.py ---
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from database.db import get_db
from models.user import User
from schemas.auth_schema import (
    UserCreate, UserLogin, ForgotPasswordRequest, ResetPasswordRequest, 
    VerifyCodeRequest, LoginResponse, AuthResponse, UserDataForAuth,
    SendVerificationCodeRequest # 引入新的 Schema
)
from utils.hashing import hash_password, verify_password
from utils.token import create_access_token, create_reset_token, verify_reset_token
from mail_config import send_reset_email
import random

router = APIRouter()

# --- 暫存驗證碼的記憶體字典 ---
# 格式: {"user@email.com": {"code": "123456", "expires_at": datetime_object}}
# 注意：這在伺服器重啟後會遺失。生產環境建議改用 Redis。
verification_codes = {}

# --- 新增 API：發送註冊驗證碼 ---
@router.post("/send-verification-code", status_code=status.HTTP_200_OK)
async def send_verification_code(request: SendVerificationCodeRequest, db: Session = Depends(get_db)):
    # 1. 檢查此電子郵件是否已被註冊
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="此電子郵件已被註冊"
        )

    # 2. 產生驗證碼
    code = str(random.randint(100000, 999999))

    # 3. 將驗證碼和過期時間暫存起來 (10 分鐘有效)
    verification_codes[request.email] = {
        "code": code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    print(f"Generated verification code for {request.email}: {code}")

    # 4. 發送郵件
    try:
        # 這裡可以建立一個新的郵件範本，或暫時共用
        send_reset_email(request.email, code) 
    except Exception as e:
        print(f"Error sending email to {request.email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="無法寄送郵件")

    return {"message": "驗證碼已成功寄至您的信箱"}


# --- 修改後的註冊 API ---
@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 1. 從暫存中讀取並驗證驗證碼
    stored_code_data = verification_codes.get(user_data.email)
    
    if not stored_code_data:
        raise HTTPException(status_code=400, detail="請先獲取驗證碼")
        
    if datetime.utcnow() > stored_code_data["expires_at"]:
        raise HTTPException(status_code=400, detail="驗證碼已過期")

    if stored_code_data["code"] != user_data.code:
        raise HTTPException(status_code=400, detail="驗證碼錯誤")
    
    # 2. 檢查使用者名稱和 email 是否已存在 (保持不變)
    existing_user = db.query(User).filter(
        or_(User.username == user_data.username, User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="使用者名稱或電子郵件已被註冊")

    # 3. 建立新使用者 (移除 code 欄位)
    new_user_dict = user_data.dict()
    new_user_dict.pop("code", None)
    
    new_user = User(
        **new_user_dict,
        password=hash_password(user_data.password),
        registered_at=datetime.utcnow(),
        is_verified=True, # 因為已經通過郵件驗證
        roles=["user"]
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. 驗證成功後，刪除暫存的驗證碼
    verification_codes.pop(user_data.email, None)

    # 5. 回傳 Token 和使用者資料 (保持不變)
    access_token = create_access_token(data={"sub": str(new_user.id)})
    user_for_response = UserDataForAuth.from_orm(new_user)
    return LoginResponse(
        token=AuthResponse(access_token=access_token),
        user=user_for_response
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

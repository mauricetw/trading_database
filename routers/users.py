from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db
# 修正：引入正確的 Schema
from schemas.user_schema import UserProfileResponse, UserPublicProfile
# --- 功能升級：引入 get_current_user ---
from utils.token import get_current_user
from models.user import User

router = APIRouter()

# --- 功能升級：新增 /me 路由，取得當前登入者的公開資料 ---
# 這個 API 會要求使用者必須提供有效的 Bearer Token。
# FastAPI 會自動處理 Token 的驗證，並將使用者物件傳入 `current_user`。
@router.get("/me", response_model=UserPublicProfile)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    取得當前登入使用者的公開個人資料。
    需要有效的 Access Token 進行授權。
    """
    # 因為 Pydantic 的 orm_mode，可以直接回傳 user 物件
    return current_user



# --- 修正後的 get_user API ---
# 1. 將 user_id 的類型提示改為 int，更精確。
# 2. response_model 指向修正後的 UserProfileResponse。
# 3. 回傳的結構 `{"user": user}` 與 Schema 的巢狀結構匹配。
#    因為 Schema 已經修正，Pydantic 現在可以正確地從 user ORM 物件轉換資料。
@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """
    根據使用者 ID 取得特定使用者的公開個人資料。
    此 API 不需要授權。
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到此使用者")
    
    # 回傳與 Schema 匹配的巢狀結構
    return {"user": user}


# --- FILE: models/verification.py ---
from sqlalchemy import Column, Integer, String, DateTime, Enum
from database.db import Base
from datetime import datetime
import enum

# 定義一個 Enum 來表示驗證碼的用途
class CodePurpose(str, enum.Enum):
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"

class VerificationCode(Base):
    """
    一個專門用來儲存所有類型驗證碼的資料表。
    """
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    purpose = Column(Enum(CodePurpose), nullable=False) # 標示驗證碼的用途
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<VerificationCode(email='{self.email}', purpose='{self.purpose}')>"

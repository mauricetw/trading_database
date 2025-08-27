# --- models/verification.py ---
from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SQLAlchemyEnum
from datetime import datetime, timedelta
import enum

class CodePurpose(enum.Enum):
    REGISTRATION = "registration"
    PASSWORD_RESET = "password_reset"

class VerificationCode(Base):
    __tablename__ = 'verification_codes'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    code = Column(String(10), nullable=False)
    purpose = Column(SQLAlchemyEnum(CodePurpose), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(minutes=10))

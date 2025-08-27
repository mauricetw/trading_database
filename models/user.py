# --- FILE: models/user.py (重構版) ---
# 說明：
# 1. 將 `password` 欄位更名為 `password_hash`，使其語意更清晰。
# 2. 移除了 `verification_code` 和 `code_expiration` 欄位，這些將由新的 VerificationCode 模型處理。
# 3. 新增了與 VerificationCode 的關聯 (雖然在這個檔案中不是必要的，但保持完整性)。

from database.db import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # 前端傳來的 username 我們對應到 nickname，因為 email 才是真正的登入名
    nickname = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False) # 更名
    email = Column(String(255), unique=True, index=True, nullable=False)

    phone_number = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    bio = Column(Text, nullable=True)
    school_name = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    roles = Column(JSON, default=["user"])

    # 賣家相關
    is_seller = Column(Boolean, default=False)
    seller_name = Column(String(255), nullable=True)
    seller_description = Column(Text, nullable=True)
    seller_rating = Column(Float, nullable=True)
    buyer_rating = Column(Float, nullable=True)
    product_count = Column(Integer, default=0)
    
    # --- SQLAlchemy 關聯 ---
    products = relationship("Product", back_populates="seller")
    shipping_options = relationship("ShippingOption", back_populates="seller") # 運送選項的關聯

    def __repr__(self):
        return f"<User(id={self.id}, nickname={self.nickname}, email={self.email})>"

# --- ShippingOption 資料表 ---
class ShippingOption(Base):
    __tablename__ = "shipping_options"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    cost = Column(Float, nullable=False)
    is_enabled = Column(Boolean, default=True)
    
    # 關聯到賣家，表示這是哪個賣家提供的運送方式
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller = relationship("User", back_populates="shipping_options")

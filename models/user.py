from database.db import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)

    phone_number = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    bio = Column(Text, nullable=True)
    school_name = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    roles = Column(JSON, nullable=True)  # JSON 儲存角色清單，例如 ["user", "seller"]

    buyer_rating = Column(Float, nullable=True)

    # 賣家相關
    is_seller = Column(Boolean, default=False)
    seller_name = Column(String(255), nullable=True)
    seller_description = Column(LONGTEXT, nullable=True)
    seller_rating = Column(Float, nullable=True)
    product_count = Column(Integer, default=0)

    # 重設密碼驗證碼
    verification_code = Column(String(6), nullable=True)
    code_expiration = Column(DateTime, nullable=True)
    
    products = relationship("Product", back_populates="seller")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


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

# --- FILE: models/user.py ---
from database.db import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    bio = Column(Text, nullable=True)
    school_name = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    roles = Column(JSON, default=["user"])
    is_seller = Column(Boolean, default=False)
    seller_name = Column(String(255), nullable=True)
    seller_description = Column(Text, nullable=True)
    seller_rating = Column(Float, nullable=True)
    buyer_rating = Column(Float, nullable=True)
    product_count = Column(Integer, default=0)
    
    # --- SQLAlchemy 關聯 ---
    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")
    shipping_options = relationship("ShippingOption", back_populates="seller", cascade="all, delete-orphan")
    
    # --- 加入與 CartItem 和 WishlistItem 的雙向關聯 ---
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    wishlist_items = relationship("WishlistItem", back_populates="user", cascade="all, delete-orphan")

    # --- 新增與 Address 的關聯 ---
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, nickname={self.nickname}, email={self.email})>"

# (ShippingOption 模型保持不變)
class ShippingOption(Base):
    __tablename__ = "shipping_options"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    cost = Column(Float, nullable=False)
    is_enabled = Column(Boolean, default=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller = relationship("User", back_populates="shipping_options")

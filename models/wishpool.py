# --- FILE: models/wishpool.py ---
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from database.db import Base

class Wishpool(Base):
    """
    許願池 (買家發布的願望)
    """
    __tablename__ = "wishpools"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # 願望發布者 (買家)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 關聯到商品分類 (product_categories)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    tags = Column(JSON, nullable=True) # 儲存為 List[str]
    photo_url = Column(String(500), nullable=True)
    
    price_min = Column(Integer, nullable=True)
    price_max = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    course_code = Column(String(100), nullable=True) # 課程代碼

    status = Column(String(50), default="open", nullable=False) # open, matched, closed
    
    # 當買家 'accept' 一個 'invite' 時，會填入這個欄位
    matched_item_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- 關聯 Relationships ---
    user = relationship("User", back_populates="wishpools")
    category = relationship("Category") # 假設 Category 在 models/product.py 中
    matched_item = relationship("Product") # 假設 Product 在 models/product.py 中

    # 關聯到收藏 (Favorites) - 用於計算 like_count
    favorites = relationship("WishpoolFavorite", back_populates="wishpool", cascade="all, delete-orphan")
    
    # 關聯到邀請 (Invites) - 賣家發來的報價
    invites = relationship("WishpoolInvite", back_populates="wishpool", cascade="all, delete-orphan")

class WishpoolFavorite(Base):
    """
    許願池收藏 (誰點了 "我也想要")
    """
    __tablename__ = "wishpool_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wishpool_id = Column(Integer, ForeignKey("wishpools.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    wishpool = relationship("Wishpool", back_populates="favorites")

class WishpoolInvite(Base):
    """
    許願池邀請 (賣家發給買家的報價/接單)
    """
    __tablename__ = "wishpool_invites"

    id = Column(Integer, primary_key=True, index=True)
    wishpool_id = Column(Integer, ForeignKey("wishpools.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False) # 賣家
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True) # 賣家提供的商品
    
    message = Column(String(500), nullable=True)
    status = Column(String(50), default="pending", nullable=False) # pending, accepted, rejected
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    wishpool = relationship("Wishpool", back_populates="invites")
    seller = relationship("User")
    product = relationship("Product")

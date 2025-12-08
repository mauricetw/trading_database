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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    tags = Column(JSON, nullable=True)
    photo_url = Column(String(500), nullable=True)
    
    price = Column(Integer, nullable=False) 
    quantity = Column(Integer, default=1, nullable=False)
    
    # --- [修改] 使用 JSON 儲存地址快照，防止買家刪除地址後資料遺失 ---
    # 這裡不再使用 ForeignKey("addresses.id")
    shipping_address = Column(JSON, nullable=False) 
    
    # 綁定運送方式
    shipping_name = Column(String(100), default="標準配送", nullable=False)
    shipping_cost = Column(Float, default=60.0, nullable=False)

    location = Column(String(255), nullable=True)
    course_code = Column(String(100), nullable=True)

    status = Column(String(50), default="open", nullable=False) 
    matched_item_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- 關聯 Relationships ---
    user = relationship("User", back_populates="wishpools")
    category = relationship("Category")
    matched_item = relationship("Product")
    
    # address 關聯已移除，因為現在是 JSON

    favorites = relationship("WishpoolFavorite", back_populates="wishpool", cascade="all, delete-orphan")
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

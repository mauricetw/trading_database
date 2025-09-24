# --- FILE: models/user_interactions.py ---
from database.db import Base
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class CartItem(Base):
    """
    購物車項目資料表模型。
    """
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- 關鍵修正：建立雙向關聯並優化查詢效能 ---
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", lazy="joined") # "joined" 能在查詢購物車時自動 JOIN 商品資料

    def __repr__(self):
        return f"<CartItem(user_id={self.user_id}, product_id={self.product_id}, quantity={self.quantity})>"


class WishlistItem(Base):
    """
    收藏清單項目資料表模型。
    """
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # --- 關鍵修正：建立雙向關聯並優化查詢效能 ---
    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product", lazy="joined")

    def __repr__(self):
        return f"<WishlistItem(user_id={self.user_id}, product_id={self.product_id})>"
    

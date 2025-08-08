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
    
    # 關聯到使用者 ID，表示這個購物車項目屬於哪個使用者
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 關聯到商品 ID，表示購物車中的是哪個商品
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # 商品數量
    quantity = Column(Integer, nullable=False, default=1)
    
    # 加入時間
    added_at = Column(DateTime, default=datetime.utcnow)

    # SQLAlchemy 關聯，方便在查詢時直接存取 User 和 Product 物件
    user = relationship("User")
    product = relationship("Product")

    def __repr__(self):
        return f"<CartItem(user_id={self.user_id}, product_id={self.product_id}, quantity={self.quantity})>"


class WishlistItem(Base):
    """
    收藏清單項目資料表模型。
    """
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)

    # 關聯到使用者 ID，表示這個收藏項目屬於哪個使用者
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 關聯到商品 ID，表示收藏的是哪個商品
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # 加入收藏的時間，對應前端的 createdAt
    added_at = Column(DateTime, default=datetime.utcnow)

    # SQLAlchemy 關聯
    user = relationship("User")
    product = relationship("Product")

    def __repr__(self):
        return f"<WishlistItem(user_id={self.user_id}, product_id={self.product_id})>"

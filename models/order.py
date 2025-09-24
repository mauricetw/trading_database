# --- FILE: models/order.py ---
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from database.db import Base
from models.product import Product
from models.user import User

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(String(50), default="pending", nullable=False) # pending, processing, shipped, delivered, cancelled
    total_amount = Column(Float, nullable=False)
    shipping_address = Column(JSON, nullable=False) # 將地址資訊以 JSON 格式儲存快照
    shipping_method = Column(JSON, nullable=False) # 將運送方式以 JSON 格式儲存快照
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False) # 記錄購買當下的價格快照

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    

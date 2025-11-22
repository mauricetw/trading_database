# --- FILE: models/order.py ---
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from database.db import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(String(50), default="pending", nullable=False) # pending, failed, completed, rejected

    # --- [BUG 修正] ---
    # 1. 在資料庫模型中正式加入 payment_status 欄位
    #    預設為 "unpaid" (未付款)
    payment_status = Column(String(50), default="unpaid", nullable=False) # 例如: unpaid, paid

    total_amount = Column(Float, nullable=False)
    shipping_address = Column(JSON, nullable=False) # 將地址資訊以 JSON 格式儲存快照
    shipping_method = Column(JSON, nullable=False) # 將運送方式以 JSON 格式儲存快照

    status_history = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- 加入 back_populates 以建立雙向關聯 ---
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status='{self.status}')>"


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False) # 記錄購買當下的價格快照

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    def __repr__(self):
        return f"<OrderItem(order_id={self.order_id}, product_id={self.product_id})>"
    

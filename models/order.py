# --- FILE: models/order.py (新檔案) ---
from database.db import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    # 訂單總金額
    total_amount = Column(Float, nullable=False)
    # 訂單狀態 (例如: pending, processing, shipped, completed, cancelled)
    status = Column(String(50), nullable=False, default="pending")
    # 運送資訊 (以 JSON 格式儲存地址、運送方式等)
    shipping_info = Column(JSON, nullable=False)
    # 建立時間
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    buyer = relationship("User", back_populates="orders_as_buyer")
    
    # 一個訂單可以包含多個訂單項目
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False)
    # 記錄購買當下的價格，避免商品價格變動影響歷史訂單
    price_at_purchase = Column(Float, nullable=False)

    # 關聯
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

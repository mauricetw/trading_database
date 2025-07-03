from database.db import Base
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)  # Flutter 中的 id 為 String，可轉為 str(uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)

    category_id = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False)  # 可選：冗餘儲存分類名稱以加速查詢

    stock_quantity = Column(Integer, nullable=False)
    status = Column(String(50), default="available")  # "available", "sold", "unavailable"

    image_urls = Column(JSON, nullable=False)  # 儲存圖片 URL 陣列 (List[str])

    tags = Column(JSON, nullable=True)  # List[str]

    sales_count = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)

    is_favorite = Column(Boolean, default=False)  # 預設不收藏
    is_sold = Column(Boolean, default=False)

    # 時間欄位
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 賣家關聯 (可對應 user 資料表)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller = relationship("User", back_populates="products")

    # 運送資訊（選擇性擴充）
    shipping_info = Column(JSON, nullable=True)  # 可以儲存如地址、重量、運費等

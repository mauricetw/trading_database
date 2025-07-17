from database.db import Base
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class Product(Base):
    __tablename__ = "products"

    # --- 欄位對齊與確認 ---
    # id: Integer, 主鍵，與前端的 int id 匹配。
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True) # 與前端的 double? originalPrice 匹配

    # 分類
    category_id = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False) # 冗餘儲存分類名稱以加速查詢

    # 庫存與狀態
    stock_quantity = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="available", nullable=False) # e.g., "available", "sold", "delisted"

    # --- 圖片儲存：遵循最佳實踐，儲存 URL 列表 ---
    image_urls = Column(JSON, nullable=True) # 儲存圖片 URL 陣列 (List[str])

    # 銷售與評價
    sales_count = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)
    review_count = Column(Integer, default=0)

    # 標籤
    tags = Column(JSON, nullable=True) # List[str]

    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller = relationship("User", back_populates="products")

    # 運送資訊（JSON格式，彈性高）
    shipping_info = Column(JSON, nullable=True)

    # --- 邏輯修正：移除 is_favorite 和 is_sold ---
    # is_favorite 應由使用者和商品的關聯表來管理。
    # is_sold 的狀態應由 status 或 stock_quantity 來判斷，不在資料庫中重複儲存。

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}')>"


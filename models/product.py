# --- FILE: models/product.py ---
from database.db import Base
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    
    # 關聯到 Product 模型
    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=1)
    status = Column(String(50), default="available")
    tags = Column(JSON, nullable=True)
    sales_count = Column(Integer, default=0)
    average_rating = Column(Float, nullable=True)
    review_count = Column(Integer, default=0)
    shipping_info = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- 關聯 ---
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller = relationship("User", back_populates="products")

    # --- 關鍵修正：只保留 category_id ---
    # 我們不再需要冗餘的 'category' 字串欄位。
    # 分類名稱將透過下面的 'category' relationship 來獲取。
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Category", back_populates="products")
    
    # 這個關聯確保了當一個 Product 被刪除時，所有相關的 ProductImage 也會被自動刪除。
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

    # --- 關鍵新增：加入與 ChatRoom 的關聯 ---
    chat_rooms = relationship("ChatRoom", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}')>"

class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(500), nullable=False)
    display_order = Column(Integer, default=0)
    
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product", back_populates="images")

    def __repr__(self):
        # --- 錯誤修正：顯示 image_url 而不是不存在的 name ---
        return f"<ProductImage(id={self.id}, url='{self.image_url}')>"

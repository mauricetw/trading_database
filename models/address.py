# --- FILE: models/address.py ---
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database.db import Base

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    recipient_name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False)
    
    # --- 補上前端模型中存在的欄位 ---
    country = Column(String(100), default="台灣")
    province = Column(String(100))
    city = Column(String(100), nullable=False)
    district = Column(String(100))
    
    # --- 關鍵修正：將欄位名稱與前端的 streetAddress1/2 對齊 ---
    street_address_1 = Column(String(500), nullable=False)
    street_address_2 = Column(String(500), nullable=True)
    
    postal_code = Column(String(20), nullable=False)
    is_default = Column(Boolean, default=False)
    
    # --- 關鍵修正：補上 additionalInfo 欄位 ---
    additional_info = Column(JSON, nullable=True)

    user = relationship("User", back_populates="addresses")

    @property
    def displayAddress(self):
        """提供一個與前端 getter 邏輯類似的屬性，方便後端使用"""
        parts = [
            self.postal_code, self.country, self.province, self.city, 
            self.district, self.street_address_1, self.street_address_2
        ]
        return ' '.join(filter(None, parts))

    def __repr__(self):
        return f"<Address(id={self.id}, user_id={self.user_id})>"

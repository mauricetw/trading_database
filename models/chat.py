# --- FILE: models/chat.py ---
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database.db import Base

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- [修改] 允許 product_id 為空 (通用聊天) ---
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 建立與 User 和 Product 的關聯
    product = relationship("Product")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="chats_as_buyer")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="chats_as_seller")

    # 建立與 ChatMessage 的一對多關聯
    messages = relationship("ChatMessage", back_populates="chat_room", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    text = Column(Text) # 改為可選，以支援圖片等非文字訊息
    image_url = Column(String(500))
    # ... 未來可擴充 video_url 等
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 修正：is_read 的類型應為 Boolean
    is_read = Column(Boolean, default=False)
    
    chat_room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

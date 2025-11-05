# --- FILE: schemas/chat_schema.py ---
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from .user_schema import UserPublicProfile # 引入用於顯示使用者資訊的 Schema

# --- 用於 API 回應的 Message 模型 ---
class MessageResponse(BaseModel):
    id: int
    chat_room_id: int
    sender_id: int
    receiver_id: int
    text: Optional[str] = None
    image_url: Optional[str] = None
    timestamp: datetime
    is_read: bool

    class Config:
        from_attributes = True
        

# --- 用於 API 請求 (Request) 的模型 ---
class ChatRoomCreateRequest(BaseModel):
    product_id: int
    

# --- 用於 API 回應的 ChatRoom 摘要模型 (用於列表) ---
class ChatRoomResponse(BaseModel):
    id: int
    other_party: UserPublicProfile
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0

    class Config:
        from_attributes = True

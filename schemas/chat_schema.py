# --- FILE: schemas/chat_schema.py ---
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from .user_schema import UserPublicProfile
from .product_schema import ProductResponse # 如果需要顯示商品資訊

# --- [修改] 用於 API 請求 (Request) 的模型 ---
class ChatRoomCreateRequest(BaseModel):
    # 如果是從商品頁發起，傳 product_id
    product_id: Optional[int] = None
    # 如果是從個人頁發起 (通用聊天)，傳 seller_id
    seller_id: Optional[int] = None

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

# --- 用於 API 回應的 ChatRoom 摘要模型 (用於列表) ---
class ChatRoomResponse(BaseModel):
    id: int
    other_party: UserPublicProfile
    # product 變為可選的
    product: Optional[ProductResponse] = None
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0

    class Config:
        from_attributes = True

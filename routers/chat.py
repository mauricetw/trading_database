# --- FILE: routers/chat.py ---
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import or_
from typing import List, Dict, Any
from datetime import datetime

from database.db import SessionLocal, get_db
from models.user import User
from models.product import Product
from models.chat import ChatRoom, ChatMessage
from schemas.chat_schema import ChatRoomResponse, MessageResponse, ChatRoomCreateRequest
from schemas.user_schema import UserPublicProfile
from utils.token import get_current_user, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

router_chat = APIRouter(
    prefix="/chats",
    tags=["聊天 (Chat)"]
)

# ... (ConnectionManager 類別保持不變，省略以節省篇幅) ...
class ConnectionManager:
    def __init__(self):
        # 映射：room_id -> 活躍的 WebSocket 列表
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        print(f"使用者連線到聊天室 {room_id}。")

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            try:
                self.active_connections[room_id].remove(websocket)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
                print(f"使用者從聊天室 {room_id} 斷線。")
            except ValueError:
                pass

    async def broadcast(self, message: Dict[str, Any], room_id: int):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except RuntimeError as e:
                    pass

manager = ConnectionManager()

# ... (get_user_from_token 函式保持不變) ...
def get_user_from_token(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Token 無效 (缺少 sub)")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise ValueError("找不到使用者")
        return user
    except JWTError:
        raise ValueError("Token JWT 無效")
    except Exception as e:
        raise ValueError(f"Token 驗證錯誤: {e}")

# --- REST API ---

@router_chat.get("", response_model=List[ChatRoomResponse])
def get_my_chat_rooms(
    role: str = Query(..., enum=["buyer", "seller"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    options = [
        joinedload(ChatRoom.buyer), 
        joinedload(ChatRoom.seller), 
        joinedload(ChatRoom.product)
    ]
    
    if role == "buyer":
        chat_rooms_query = db.query(ChatRoom).options(*options).filter(ChatRoom.buyer_id == current_user.id)
    else: 
        chat_rooms_query = db.query(ChatRoom).options(*options).filter(ChatRoom.seller_id == current_user.id)
        
    chat_rooms = chat_rooms_query.all()

    response = []
    for room in chat_rooms:
        last_message = db.query(ChatMessage).filter(
            ChatMessage.chat_room_id == room.id
        ).order_by(ChatMessage.timestamp.desc()).first()
        
        unread_count = db.query(ChatMessage).filter(
            ChatMessage.chat_room_id == room.id,
            ChatMessage.receiver_id == current_user.id,
            ChatMessage.is_read == False
        ).count()
        
        other_party_model = room.seller if role == "buyer" else room.buyer
        other_party = UserPublicProfile.from_orm(other_party_model)

        response.append(ChatRoomResponse(
            id=room.id,
            product=room.product, 
            other_party=other_party,
            last_message=last_message,
            unread_count=unread_count,
        ))
        
    return sorted(
        response, 
        key=lambda r: r.last_message.timestamp if r.last_message else datetime.min, 
        reverse=True
    )

@router_chat.get("/{room_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(
    room_id: int,
    background_tasks: BackgroundTasks, # [FIX] 修正 Depends 順序問題
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room or (current_user.id not in [chat_room.buyer_id, chat_room.seller_id]):
        raise HTTPException(status_code=403, detail="您沒有權限存取此聊天室")

    # (使用 BackgroundTasks 處理已讀標記)
    def mark_as_read(db_session: Session, room_id: int, user_id: int):
        try:
            db_session.query(ChatMessage).filter(
                ChatMessage.chat_room_id == room_id,
                ChatMessage.receiver_id == user_id,
                ChatMessage.is_read == False
            ).update({"is_read": True})
            db_session.commit()
        finally:
            db_session.close()

    db_for_task = SessionLocal()
    background_tasks.add_task(mark_as_read, db_for_task, room_id, current_user.id)
    
    messages = db.query(ChatMessage).filter(ChatMessage.chat_room_id == room_id).order_by(ChatMessage.timestamp.asc()).all()
    return messages

# --- [修改] 尋找或建立聊天室 (支援通用聊天) ---
@router_chat.post("", response_model=ChatRoomResponse)
def find_or_create_chat_room(
    request: ChatRoomCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    尋找或建立聊天室。
    1. 如果提供 product_id -> 建立針對該商品的聊天室。
    2. 如果只提供 seller_id -> 建立與該賣家的通用聊天室 (product_id 為 NULL)。
    """
    
    target_product = None
    target_seller_id = None

    # 情境 A: 針對商品聊天
    if request.product_id:
        target_product = db.query(Product).filter(Product.id == request.product_id).first()
        if not target_product:
            raise HTTPException(status_code=404, detail="找不到該商品")
        if target_product.seller_id == current_user.id:
            raise HTTPException(status_code=400, detail="您不能與自己開始聊天")
        
        target_seller_id = target_product.seller_id
        
        # 尋找現有的商品聊天室
        existing_room = db.query(ChatRoom).filter(
            ChatRoom.product_id == request.product_id,
            ChatRoom.buyer_id == current_user.id
        ).first()

    # 情境 B: 通用聊天 (從賣家頁面)
    elif request.seller_id:
        if request.seller_id == current_user.id:
            raise HTTPException(status_code=400, detail="您不能與自己開始聊天")
        
        target_seller_id = request.seller_id
        
        # 尋找現有的通用聊天室 (product_id 為 NULL)
        existing_room = db.query(ChatRoom).filter(
            ChatRoom.buyer_id == current_user.id,
            ChatRoom.seller_id == request.seller_id,
            ChatRoom.product_id == None # 關鍵：通用聊天的 product_id 為空
        ).first()
        
    else:
        raise HTTPException(status_code=400, detail="必須提供 product_id 或 seller_id")

    # 如果聊天室已存在，直接回傳
    if existing_room:
        room = existing_room
    else:
        # 建立新聊天室
        new_room = ChatRoom(
            product_id=request.product_id, # 可能是 None
            buyer_id=current_user.id,
            seller_id=target_seller_id
        )
        db.add(new_room)
        db.commit()
        db.refresh(new_room)
        room = new_room

    # 準備回傳資料
    db.refresh(room, ['buyer', 'seller', 'product'])
    
    other_party_model = room.seller
    other_party = UserPublicProfile.from_orm(other_party_model)
    
    last_message = db.query(ChatMessage).filter(
        ChatMessage.chat_room_id == room.id
    ).order_by(ChatMessage.timestamp.desc()).first()
    
    return ChatRoomResponse(
        id=room.id,
        product=room.product, # 可能是 None
        other_party=other_party,
        last_message=last_message,
        unread_count=0
    )

# --- WebSocket API ---

@router_chat.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(...) # 安全性修正：Token 從 Query 參數獲取
):
    db = SessionLocal()
    try:
        user = get_user_from_token(token=token, db=db)
    except ValueError as e:
        # Token 驗證失敗
        print(f"WebSocket Token 驗證失敗: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        db.close()
        return

    # 檢查使用者是否有權限加入此聊天室
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room or (user.id not in [chat_room.buyer_id, chat_room.seller_id]):
        print(f"WebSocket 權限不足: User {user.id} 試圖加入 Room {room_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        db.close()
        return

    # 連線成功
    await manager.connect(websocket, room_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_text = data
            
            # (重新獲取 chat_room 確保 session 活躍，雖然可能不需要)
            chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
            if not chat_room: continue

            receiver_id = chat_room.seller_id if user.id == chat_room.buyer_id else chat_room.buyer_id

            new_message = ChatMessage(
                chat_room_id=room_id,
                sender_id=user.id,
                receiver_id=receiver_id,
                text=message_text
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            # --- [BUG 修正] ---
            # .model_dump() 不會將 datetime 轉為字串，導致 JSON 序列化失敗
            # .model_dump(mode='json') 會將其正確轉換為 ISO 字串
            response_data = MessageResponse.from_orm(new_message).model_dump(mode='json')
            
            await manager.broadcast(response_data, room_id)

    except WebSocketDisconnect as e:
        print(f"WebSocket (客戶端關閉) 從聊天室 {room_id} 斷線")
    except Exception as e:
        print(f"WebSocket 聊天室 {room_id} 發生錯誤: {e}")
    finally:
        manager.disconnect(websocket, room_id)
        db.close()
        

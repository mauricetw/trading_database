# --- FILE: routers/chat.py ---
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload, lazyload, selectinload
from sqlalchemy import or_
from typing import List, Dict, Any
from datetime import datetime

from database.db import SessionLocal, get_db # 引入 SessionLocal 以便在 WebSocket 中使用
from models.user import User
from models.product import Product
from models.chat import ChatRoom, ChatMessage
# 1. 引入 Schema
from schemas.chat_schema import ChatRoomResponse, MessageResponse, ChatRoomCreateRequest
from schemas.product_schema import ProductResponse
from schemas.user_schema import UserPublicProfile
from utils.token import get_current_user, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

router_chat = APIRouter(
    prefix="/chats",
    tags=["聊天 (Chat)"]
)

# --- WebSocket 連線管理器 ---
class ConnectionManager:
    def __init__(self):
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
            except ValueError:
                pass # WebSocket 可能已經不在列表中
        print(f"使用者從聊天室 {room_id} 斷線。")

    async def broadcast(self, message: Dict[str, Any], room_id: int):
        if room_id in self.active_connections:
            # 建立一個副本列表以避免在迭代時修改
            connections = list(self.active_connections[room_id])
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"廣播到 {connection} 失敗: {e}")
                    # 廣播失敗 (例如連線已中斷)，將其移除
                    self.disconnect(connection, room_id)

manager = ConnectionManager()

# --- 安全性修正：將 get_user_from_token 修改為拋出非 HTTP 異常 ---
def get_user_from_token(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Token 無效 (no sub)")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise ValueError(f"找不到使用者 (ID: {user_id})")
        return user
    except JWTError:
        raise ValueError("Token 驗證失敗 (JWTError)")
    except Exception as e:
        raise ValueError(f"Token 處理失敗: {e}")

# --- REST API ---

@router_chat.post("", response_model=ChatRoomResponse)
def find_or_create_chat_room(
    request: ChatRoomCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    尋找或建立一個基於 product_id 的聊天室。
    - 如果買家 (current_user) 和該商品的賣家之間已存在此商品的聊天室，則返回該聊天室。
    - 否則，建立一個新的聊天室。
    """
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="找不到商品")
    
    if product.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="您不能與自己開始聊天")

    # 檢查是否已存在
    chat_room = db.query(ChatRoom).filter(
        ChatRoom.product_id == request.product_id,
        ChatRoom.buyer_id == current_user.id,
        ChatRoom.seller_id == product.user_id
    ).first()

    if not chat_room:
        # 建立新的聊天室
        chat_room = ChatRoom(
            product_id=request.product_id,
            buyer_id=current_user.id,
            seller_id=product.user_id
        )
        db.add(chat_room)
        db.commit()
        db.refresh(chat_room)
        print(f"使用者 {current_user.id} 建立了新的聊天室 (ID: {chat_room.id}) for Product {product.id}")

    # 載入關聯資料以便 Pydantic
    db.refresh(chat_room, ['buyer', 'seller', 'product'])
    
    # 準備回應
    # (注意：這裡的 'other_party' 是賣家)
    other_party_model = chat_room.seller
    other_party = UserPublicProfile.from_orm(other_party_model)

    return ChatRoomResponse(
        id=chat_room.id,
        # product=chat_room.product, # (如果 schema 需要，請取消註解)
        other_party=other_party,
        last_message=None, # 新建立的聊天室沒有最後訊息
        unread_count=0
    )


@router_chat.get("", response_model=List[ChatRoomResponse])
def get_my_chat_rooms(
    role: str = Query(..., enum=["buyer", "seller"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取當前使用者的聊天室列表，可根據角色篩選。"""
    
    # 為了優化查詢，使用 joinedload/selectinload 預先載入需要的資料
    options = (
        selectinload(ChatRoom.buyer),   # 預載入買家 (User)
        selectinload(ChatRoom.seller),  # 預載入賣家 (User)
        selectinload(ChatRoom.product)  # 預載入商品 (Product)
    )

    if role == "buyer":
        chat_rooms_query = db.query(ChatRoom).options(*options).filter(ChatRoom.buyer_id == current_user.id)
    else: # role == "seller"
        chat_rooms_query = db.query(ChatRoom).options(*options).filter(ChatRoom.seller_id == current_user.id)
        
    chat_rooms = chat_rooms_query.all()

    response = []
    for room in chat_rooms:
        # 獲取最後一則訊息 (這仍然是一個 N+1 查詢，未來可以優化)
        last_message = db.query(ChatMessage).filter(ChatMessage.chat_room_id == room.id).order_by(ChatMessage.timestamp.desc()).first()
        
        # 獲取未讀訊息數
        unread_count = db.query(ChatMessage).filter(
            ChatMessage.chat_room_id == room.id,
            ChatMessage.receiver_id == current_user.id,
            ChatMessage.is_read == False
        ).count()
        
        # 決定 'other_party' (對方)
        other_party_model = room.seller if role == "buyer" else room.buyer
        
        # 確保 'other_party_model' 不是 None (雖然理論上不應該)
        if not other_party_model:
            continue # 略過這個損壞的聊天室

        other_party = UserPublicProfile.from_orm(other_party_model)

        response.append(ChatRoomResponse(
            id=room.id,
            # product=room.product, # 修正 Bug：schema 中沒有 product，已移除
            other_party=other_party,
            last_message=last_message, # Pydantic 會自動處理 None
            unread_count=unread_count
        ))
        
    # 在 Python 中排序，因為 last_message 是動態獲取的
    return sorted(response, key=lambda r: r.last_message.timestamp if r.last_message else datetime.min, reverse=True)

@router_chat.get("/{room_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(
    room_id: int,
    # --- [BUG 修正] ---
    # `background_tasks` (無預設值) 必須在 `db` (有預設值) 之前
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取指定聊天室的所有歷史訊息，並將訊息標記為已讀。"""
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room or (current_user.id not in [chat_room.buyer_id, chat_room.seller_id]):
        raise HTTPException(status_code=403, detail="您沒有權限存取此聊天室")

    # 標記為已讀 (非同步)
    # 為了讓 API 快速回應，將 DB 更新作為後台任務執行
    def mark_as_read(db_session: Session, room_id: int, user_id: int):
        try:
            db_session.query(ChatMessage).filter(
                ChatMessage.chat_room_id == room_id,
                ChatMessage.receiver_id == user_id,
                ChatMessage.is_read == False
            ).update({"is_read": True})
            db_session.commit()
            print(f"後台任務：已將聊天室 {room_id} 中使用者 {user_id} 的訊息標記為已讀")
        except Exception as e:
            print(f"後台任務失敗 (mark_as_read): {e}")
            db_session.rollback()
        finally:
            db_session.close()

    # 建立一個新的 DB Session 供後台任務使用
    db_for_task = SessionLocal()
    background_tasks.add_task(mark_as_read, db_for_task, room_id, current_user.id)
    
    # 立即獲取並返回訊息
    messages = db.query(ChatMessage).filter(ChatMessage.chat_room_id == room_id).order_by(ChatMessage.timestamp.asc()).all()
    return messages

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
        

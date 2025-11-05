# --- FILE: routers/chat.py ---
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Dict, Any
from datetime import datetime

from database.db import SessionLocal, get_db # 引入 SessionLocal 以便在 WebSocket 中使用
from models.user import User
from models.product import Product # <-- [新增] 引入 Product 模型
from models.chat import ChatRoom, ChatMessage
from schemas.chat_schema import ChatRoomResponse, MessageResponse, ChatRoomCreateRequest # <-- [新增] 引入 ChatRoomCreateRequest
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
                # 邊界情況：websocket 不在列表中
                pass

    async def broadcast(self, message: Dict[str, Any], room_id: int):
        """ 將 JSON (dict) 訊息廣播到房間內的所有連線。 """
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except RuntimeError as e:
                    # 處理在廣播發送前連線就已關閉的情況
                    print(f"廣播時發生錯誤: {e}")
                    # (可選) 移除中斷的連線
                    # self.disconnect(connection, room_id) # 迭代中修改列表需謹慎
                    pass

manager = ConnectionManager()

def get_user_from_token(token: str, db: Session) -> User:
    """ 輔助函式：驗證 token 並從 DB 獲取使用者。 """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            # 對於 WS，使用 ValueError 而非 HTTPException
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
    """ 獲取當前使用者的聊天室列表，可根據角色篩選。 """
    
    # 使用 joinedload 預先載入資料以提高效率
    options = [
        joinedload(ChatRoom.buyer), 
        joinedload(ChatRoom.seller), 
        joinedload(ChatRoom.product)
    ]
    
    if role == "buyer":
        chat_rooms_query = db.query(ChatRoom).options(*options).filter(ChatRoom.buyer_id == current_user.id)
    else: # role == "seller"
        chat_rooms_query = db.query(ChatRoom).options(*options).filter(ChatRoom.seller_id == current_user.id)
        
    chat_rooms = chat_rooms_query.all()

    response = []
    for room in chat_rooms:
        # 查詢最後一條訊息 (高效)
        last_message = db.query(ChatMessage).filter(
            ChatMessage.chat_room_id == room.id
        ).order_by(ChatMessage.timestamp.desc()).first()
        
        # 查詢未讀計數 (高效)
        unread_count = db.query(ChatMessage).filter(
            ChatMessage.chat_room_id == room.id,
            ChatMessage.receiver_id == current_user.id,
            ChatMessage.is_read == False
        ).count()
        
        # 'other_party_model' 已經由 joinedload 載入
        other_party_model = room.seller if role == "buyer" else room.buyer
        other_party = UserPublicProfile.from_orm(other_party_model)

        response.append(ChatRoomResponse(
            id=room.id,
            # product=room.product, # (移除這一行，因為 ChatRoomResponse schema 中沒有 'product')
            other_party=other_party,
            last_message=last_message,
            unread_count=unread_count,
            # 確保 ChatRoomResponse 有 'product' 欄位 (如果需要的話)
        ))
        
    # 獲取所有資料後在 Python 中排序
    return sorted(
        response, 
        key=lambda r: r.last_message.timestamp if r.last_message else datetime.min, 
        reverse=True
    )

@router_chat.get("/{room_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ 獲取指定聊天室的所有歷史訊息。 """
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
    if not chat_room or (current_user.id not in [chat_room.buyer_id, chat_room.seller_id]):
        raise HTTPException(status_code=403, detail="您沒有權限存取此聊天室")

    # 一次性將所有傳送給當前使用者的訊息標記為已讀
    db.query(ChatMessage).filter(
        ChatMessage.chat_room_id == room_id,
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False # 僅更新未讀的
    ).update({"is_read": True}, synchronize_session=False) # 使用 synchronize_session=False 提高效率
    
    db.commit()
    
    # Commit 後再獲取訊息
    messages = db.query(ChatMessage).filter(
        ChatMessage.chat_room_id == room_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    return messages

# --- [新功能] 尋找或建立聊天室 ---
@router_chat.post("", response_model=ChatRoomResponse)
def find_or_create_chat_room(
    request: ChatRoomCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ 根據 product_id 尋找現有聊天室，或建立一個新聊天室。 """
    
    # 1. 檢查商品是否存在
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="找不到該商品")
        
    # 2. 檢查使用者是否為賣家本人
    if product.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="您不能與自己開始聊天")
        
    seller_id = product.seller_id
    
    # 3. 檢查聊天室是否已存在 (針對此買家和此商品)
    existing_room = db.query(ChatRoom).filter(
        ChatRoom.product_id == request.product_id,
        ChatRoom.buyer_id == current_user.id
    ).first()
    
    if existing_room:
        room = existing_room
        # (可選) 載入賣家資訊
        other_party_model = db.query(User).filter(User.id == seller_id).first()
    else:
        # 4. 如果不存在，建立新聊天室
        new_room = ChatRoom(
            product_id=request.product_id,
            buyer_id=current_user.id,
            seller_id=seller_id
        )
        db.add(new_room)
        db.commit()
        db.refresh(new_room)
        room = new_room
        other_party_model = product.seller # 假設 Product.seller 關聯已設置
        
        # 如果 Product.seller 關聯沒有設置，手動查詢
        if not other_party_model:
            other_party_model = db.query(User).filter(User.id == seller_id).first()

    if not other_party_model:
         raise HTTPException(status_code=404, detail="找不到賣家資訊")

    # 5. 建立並回傳 ChatRoomResponse
    other_party = UserPublicProfile.from_orm(other_party_model)
    
    # 查詢最後一條訊息 (對於新房間，這會是 None)
    last_message = db.query(ChatMessage).filter(
        ChatMessage.chat_room_id == room.id
    ).order_by(ChatMessage.timestamp.desc()).first()
    
    return ChatRoomResponse(
        id=room.id,
        other_party=other_party,
        last_message=last_message,
        unread_count=0 # 新房間或剛點進來，未讀數為 0
    )

# --- WebSocket API ---

# 修正 2 (安全性): 從路徑中移除 {token}
@router_chat.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    # 修正 2 (安全性): 改用 Query 參數來獲取 token
    token: str = Query(...) 
):
    db = SessionLocal()
    user = None
    try:
        # 1. 使用 token 驗證使用者
        user = get_user_from_token(token=token, db=db)
        
        # 2. (額外安全檢查) 驗證使用者是否屬於此聊天室
        chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if not chat_room or (user.id not in [chat_room.buyer_id, chat_room.seller_id]):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="未授權存取")
            return
            
        # 3. 連線到管理器
        await manager.connect(websocket, room_id)
        
        while True:
            # 4. 等待客戶端傳來訊息 (假定是純文字)
            data = await websocket.receive_text()
            message_text = data
            
            # (chat_room 已經在上面獲取)
            
            # 5. 決定接收者
            receiver_id = chat_room.seller_id if user.id == chat_room.buyer_id else chat_room.buyer_id

            # 6. 建立新訊息並儲存到 DB
            new_message = ChatMessage(
                chat_room_id=room_id,
                sender_id=user.id,
                receiver_id=receiver_id,
                text=message_text,
                is_read=False # 明確設為 False
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            # 7. 準備廣播資料
            # 修正 1 (Bug): 使用 .model_dump() 取得 dict, 而不是 .model_dump_json()
            response_data = MessageResponse.from_orm(new_message).model_dump()
            
            # 8. 廣播 dict (它將被 send_json 正確編碼)
            await manager.broadcast(response_data, room_id)

    except WebSocketDisconnect:
        print(f"WebSocket (客戶端關閉) 從聊天室 {room_id} 斷線")
        manager.disconnect(websocket, room_id)
    except ValueError as e: # 捕捉來自 get_user_from_token 的自訂 token 錯誤
        print(f"WebSocket 驗證錯誤: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
    except Exception as e:
        # 其他所有錯誤
        print(f"WebSocket 聊天室 {room_id} 發生錯誤: {e}")
        manager.disconnect(websocket, room_id)
        try:
            # 如果連線還在，嘗試發送錯誤碼
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="伺服器內部錯誤")
        except RuntimeError:
            pass # 連線已經關閉
    finally:
        # 確保 DB Session 總是被關閉
        db.close()

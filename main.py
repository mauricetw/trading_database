# --- FILE: trading_database/main.py ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    auth, 
    users, 
    products, 
    seller, 
    cart, 
    wishlist,
    announcements,
    # orders # TODO: 當 orders.py 建立後，取消此行的註解
)
from database.db import engine

# --- 初始化 FastAPI 應用程式 ---
app = FastAPI(
    title="交易平台 API",
    description="這是一個使用 FastAPI 和 MariaDB 開發的交易平台後端 API。",
    version="1.0.0",
    # 可以在這裡加入更多 API 的元數據
)

# --- 設定 CORS 中介軟體 ---
# 允許所有來源，方便前端在開發時進行連線。
# 在正式上線時，建議將 allow_origins 修改為你的前端服務的實際網域。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 註解：資料庫表格管理 ---
# 我們使用 Alembic 來管理資料庫的遷移 (migrations)，
# 因此 `Base.metadata.create_all(bind=engine)` 這行程式碼已被移除，
# 以確保資料庫的結構變更是可控且可追蹤的。

# --- 2. 註冊所有模組的 API 路由 ---
# 為每個 router 加上 prefix，讓 API 的 URL 更有組織性。
# 為每個 router 加上 tags，讓自動產生的 API 文件 (/docs) 更清晰。

app.include_router(auth.router, prefix="/auth", tags=["使用者認證 (Authentication)"])
app.include_router(users.router, prefix="/users", tags=["使用者資料 (Users)"])
app.include_router(products.router, prefix="/products", tags=["商品 (Products)"])

app.include_router(seller.router, prefix="/seller", tags=["賣家中心 (Seller)"])
app.include_router(cart.router, prefix="/cart", tags=["購物車 (Cart)"])
app.include_router(wishlist.router, prefix="/wishlist", tags=["收藏清單 (Wishlist)"])
app.include_router(announcements.router, prefix="/announcements", tags=["公告 (Announcements)"])
# app.include_router(orders.router, prefix="/orders", tags=["訂單 (Orders)"]) # TODO: 當 orders.py 建立後，取消此行的註解


# --- 根目錄 API 端點 ---
@app.get("/", tags=["根目錄 (Root)"])
def read_root():
    """
    一個簡單的根目錄端點，提供 API 的基本歡迎訊息。
    """
    return {"message": "歡迎來到交易平台 API！請前往 /docs 查看 API 文件。"}

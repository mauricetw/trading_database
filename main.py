from fastapi import FastAPI
from routers import auth, products, orders, users
from database.db import engine, Base
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="交易平台 API",
    description="這是一個使用 FastAPI 和 MariaDB 開發的交易平台後端 API。",
    version="1.0.0",
)

# 設定 CORS 中介軟體
# 在開發階段，允許所有來源是方便的。
# 在正式上線（Production）時，建議將 allow_origins 修改為你的前端服務的實際網域。
# 例如: allow_origins=["https://your-flutter-app-domain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 不限制來源
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有方法（GET、POST 等）
    allow_headers=["*"],  # 允許所有 headers
)

# 建立資料庫表
#Base.metadata.create_all(bind=engine)
#改為Alembic控制

# 引入並註冊各個模組的路由
app.include_router(auth.router, prefix="/auth", tags=["使用者認證 (Authentication)"])
app.include_router(products.router, prefix="/products", tags=["商品 (Products)"])
app.include_router(orders.router, prefix="/orders", tags=["訂單 (Orders)"])
app.include_router(users.router, prefix="/users", tags=["使用者資料 (Users)"])
app.include_router(seller.router, prefix="/seller", tags=["賣家中心 (Seller)"])

@app.get("/", tags=["根目錄 (Root)"])
def read_root():
    """
    根目錄，提供 API 基本資訊。
    """
    return {"message": "歡迎來到交易平台 API！請前往 /docs 查看 API 文件。"}

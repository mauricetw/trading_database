from fastapi import FastAPI
from routers import auth, products, orders, getUser
from database.db import engine, Base
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 加上這段以允許任何來源（網域）都能連線
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 不限制來源
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有方法（GET、POST 等）
    allow_headers=["*"],  # 允許所有 headers
)

# 建立資料庫表
Base.metadata.create_all(bind=engine)

# 註冊路由
app.include_router(auth.router, tags=["Authentication"])
app.include_router(products.router, tags=["Product"])
app.include_router(orders.router, tags=["Order"])

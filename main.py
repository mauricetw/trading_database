from fastapi import FastAPI
from routers import auth, products, orders
from database.db import engine, Base

app = FastAPI()

# 建立資料庫表
Base.metadata.create_all(bind=engine)

# 註冊路由
app.include_router(auth.router, tags=["Authentication"])
app.include_router(products.router, tags=["Product"])
app.include_router(orders.router, tags=["Order"])

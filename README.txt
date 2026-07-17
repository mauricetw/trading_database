專案名稱: 交易平台 API (Trading Platform API)

簡介:
這是一個使用 FastAPI 和 MariaDB 開發的交易平台後端 API。
提供完整的電子商務與交易平台功能，包含使用者認證、商品管理、購物車、訂單處理與即時聊天等。

主要功能模組:
- 使用者認證 (Authentication): 登入、註冊與權限管理。
- 使用者資料 (Users): 使用者個人資料管理。
- 公開商品 (Public Products): 瀏覽與搜尋商品。
- 賣家功能 (Seller): 賣家商品管理。
- 檔案上傳 (Uploads): 處理圖片等靜態檔案上傳。
- 購物車 (Cart): 購物車管理。
- 願望清單 (Wishlist): 收藏喜愛的商品。
- 公告 (Announcements): 平台公告系統。
- 地址管理 (Address): 使用者收件地址管理。
- 運送方式 (Shipping): 物流與運送設定。
- 訂單管理 (Orders): 建立與追蹤訂單。
- 聊天室 (Chat): 買賣家即時通訊功能。
- 許願池 (Wishpool): 許願池功能。

技術棧:
- 後端框架: FastAPI, Uvicorn
- 資料庫與 ORM: MariaDB, SQLAlchemy, PyMySQL
- 資料庫遷移: Alembic
- 認證與安全性: Passlib (Bcrypt), Python-JOSE
- 其他工具: Python-Multipart (檔案上傳), Python-Dotenv, Email-Validator

目錄結構:
- `alembic/`: 資料庫遷移設定檔與版本控制。
- `database/`: 資料庫連線設定。
- `models/`: SQLAlchemy ORM 模型定義。
- `routers/`: FastAPI 路由控制器 (各功能模組 API)。
- `schemas/`: Pydantic 資料驗證與序列化模型。
- `static/`: 靜態檔案儲存目錄 (例如上傳的圖片)。
- `utils/`: 共用工具與輔助函式。
- `main.py`: FastAPI 應用程式主程式與進入點。
- `requirements.txt`: 專案依賴套件清單。
- `alembic.ini`: Alembic 設定檔。
- `mail_config.py`: 郵件發送設定檔。

安裝與執行:
1. 確保已安裝 Python 3.7+。
2. 建立並啟動虛擬環境 (建議):
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
3. 安裝依賴套件:
   pip install -r requirements.txt
4. 設定環境變數 (.env 檔)，包含資料庫連線等資訊。
5. 執行資料庫遷移:
   alembic upgrade head
6. 啟動 FastAPI 開發伺服器:
   uvicorn main:app --reload

API 文件:
啟動伺服器後，可前往以下網址查看自動產生的互動式 API 文件：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

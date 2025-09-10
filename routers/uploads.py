# --- FILE: routers/uploads.py ---
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import magic
from models.user import User
from utils.token import get_current_user
import uuid
from pathlib import Path

# 初始化 API Router
router_uploads = APIRouter(
    tags=["檔案上傳 (Uploads)"]
)

# 設定儲存路徑
UPLOAD_DIR = Path("static/images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router_uploads.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user)
):
    """
    上傳單張圖片至伺服器本機。
    - **需要提供認證 Token**
    - **會在伺服器端驗證檔案的真實類型**
    """
    allowed_mime_types = ["image/jpeg", "image/png", "image/webp"]
    
    # --- 關鍵修正：在伺服器端驗證檔案類型 ---
    try:
        # 2. 先將檔案內容讀入記憶體
        contents = await file.read()
        
        # 3. 使用 python-magic 從檔案內容中識別 MIME 類型
        mime_type = magic.from_buffer(contents, mime=True)

        if mime_type not in allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"不支援的檔案類型。請上傳 JPG, PNG, 或 WEBP 檔案。(偵測到的類型為: {mime_type})"
            )
        
        # 4. 產生獨一無二的檔名
        # 我們可以根據真實的 MIME 類型來決定副檔名，更安全
        ext = ".jpg" if mime_type == "image/jpeg" else ".png" if mime_type == "image/png" else ".webp"
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # 5. 將已讀入記憶體的內容寫入檔案
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
            
        # 回傳可供前端使用的相對 URL
        file_url = f"/static/images/{unique_filename}"
        return {"image_url": file_url}

    except HTTPException as http_exc:
        # 如果是我們主動拋出的 HTTP 錯誤，直接重新拋出
        raise http_exc
    except Exception as e:
        # 處理其他可能的錯誤，例如檔案讀取失敗
        print(f"檔案上傳或驗證時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail="圖片上傳失敗，伺服器內部錯誤。")


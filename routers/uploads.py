from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from models.user import User
from utils.token import get_current_user
import uuid
from pathlib import Path

# 初始化 API Router
router_uploads = APIRouter(
    prefix="/uploads",
    tags=["檔案上傳 (Uploads)"]
)

# --- 設定儲存路徑 ---
UPLOAD_DIR = Path("static/images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True) # 確保資料夾存在

@router_uploads.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user)
):
    """
    上傳單張圖片至伺服器本機。
    """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="僅支援 JPG 或 PNG 格式的圖片。")
    
    try:
        # 產生獨一無二的檔名
        ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # 異步寫入檔案
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        # 回傳可供前端使用的相對 URL
        file_url = f"/static/images/{unique_filename}"
        return {"image_url": file_url}
    except Exception as e:
        print(f"本機檔案儲存失敗: {e}")
        raise HTTPException(status_code=500, detail="圖片上傳失敗。")

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from models.user import User
from utils.token import get_current_user
from utils.gcs import upload_file_to_gcs

# 初始化 API Router
router = APIRouter(
    prefix="/uploads",
    tags=["檔案上傳 (Uploads)"]
)

@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user)
):
    """
    上傳單張圖片至 Google Cloud Storage。

    - **需要提供認證 Token**
    - 僅接受 'image/jpeg' 或 'image/png' 格式。
    - 成功後回傳圖片的公開 URL。
    """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="僅支援 JPG 或 PNG 格式的圖片。")
    
    try:
        # 呼叫 GCS 上傳工具函式
        file_url = upload_file_to_gcs(file)
        return {"image_url": file_url}
    except Exception as e:
        # 捕捉來自 gcs.py 的錯誤並回傳 500 錯誤
        print(f"Upload failed in router: {e}")
        raise HTTPException(status_code=500, detail="圖片上傳失敗。")


# ==============================================================================
# 0. 新增：GCS 上傳工具 (建立新檔案 utils/gcs.py)
# ==============================================================================
from google.cloud import storage
from google.api_core import exceptions
import os
from dotenv import load_dotenv
from fastapi import UploadFile
import uuid

load_dotenv()

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
# GOOGLE_APPLICATION_CREDENTIALS 環境變數會被 google-cloud-storage 套件自動讀取
# storage_client = storage.Client() # 如果環境變數已設定，可直接初始化
# 為了確保路徑正確，我們明確指定
try:
    storage_client = storage.Client.from_service_account_json(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
except Exception as e:
    print(f"無法載入 GCS 憑證，請確認 .env 中的 GOOGLE_APPLICATION_CREDENTIALS 路徑是否正確。錯誤: {e}")
    storage_client = None

def upload_file_to_gcs(file: UploadFile) -> str:
    """
    將上傳的檔案儲存到 Google Cloud Storage 並回傳公開 URL。
    """
    if not storage_client:
        raise Exception("Google Cloud Storage 客戶端未成功初始化。")
        
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        # 產生一個獨一無二的檔案名稱
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"products/{uuid.uuid4()}{file_extension}"
        
        blob = bucket.blob(unique_filename)
        
        # 上傳檔案
        blob.upload_from_file(file.file, content_type=file.content_type)
        
        # 將檔案設為公開可讀
        # 注意：請確保您的 GCS Bucket 已啟用「公開存取權限」
        blob.make_public()
        
        return blob.public_url

    except exceptions.NotFound:
        print(f"GCS 儲存桶 '{GCS_BUCKET_NAME}' 不存在。")
        raise Exception("伺服器無法連接到儲存服務。")
    except Exception as e:
        print(f"GCS 上傳失敗: {e}")
        raise

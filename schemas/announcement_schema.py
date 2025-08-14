# --- FILE: schemas/announcement_schema.py (新檔案) ---
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    short_description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    published_at: datetime

    class Config:
        from_attributes = True

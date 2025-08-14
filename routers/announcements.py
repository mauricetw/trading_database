# --- FILE: routers/announcements.py (新檔案) ---
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from models.announcement import Announcement
from schemas.announcement_schema import AnnouncementResponse

router = APIRouter()

@router.get("", response_model=List[AnnouncementResponse])
async def get_all_announcements(db: Session = Depends(get_db)):
    """獲取所有公告列表，按發布日期降序排列。"""
    announcements = db.query(Announcement).order_by(Announcement.published_at.desc()).all()
    return announcements

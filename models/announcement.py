# --- FILE: models/announcement.py (新檔案) ---
from database.db import Base
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    short_description = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)

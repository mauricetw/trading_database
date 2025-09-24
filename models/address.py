# --- FILE: models/address.py ---
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database.db import Base

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    recipient_name = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False)
    address_line_1 = Column(String(500), nullable=False)
    address_line_2 = Column(String(500), nullable=True)
    city = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")

    def __repr__(self):
        return f"<Address(id={self.id}, user_id={self.user_id}, recipient_name='{self.recipient_name}')>"
    

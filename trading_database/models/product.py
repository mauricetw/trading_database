from database.db import Base
from sqlalchemy import Column, Integer, String, Float

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    price = Column(Float)
    description = Column(String(500))

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserResponseData(BaseModel):
    id: str
    username: str
    avatarUrl: Optional[str]
    schoolName: Optional[str]
    buyerRating: Optional[float]
    sellerRating: Optional[float]

    class Config:
        orm_mode = True

class UserResponse(BaseModel):
    user: UserResponseData

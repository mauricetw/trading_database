from pydantic import BaseModel, Field
from typing import Optional
from pydantic.alias_generators import to_camel

class UserPublicProfile(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    school_name: Optional[str] = None
    buyer_rating: Optional[float] = None
    seller_rating: Optional[float] = None

    class Config:
        # --- 錯誤修正：將 orm_mode = True 改為 from_attributes = True ---
        from_attributes = True
        alias_generator = to_camel
        populate_by_name = True

class UserProfileResponse(BaseModel):
    user: UserPublicProfile

    class Config:
        alias_generator = to_camel
        populate_by_name = True

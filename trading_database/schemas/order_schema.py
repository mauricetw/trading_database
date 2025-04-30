from pydantic import BaseModel

class OrderCreate(BaseModel):
    user_id: int
    product_id: int

class OrderResponse(OrderCreate):
    id: int

    class Config:
        orm_mode = True

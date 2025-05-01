from pydantic import BaseModel

class UserCreate(BaseModel):
    account: str
    password: str
    email: str

class UserLogin(BaseModel):
    account: str
    password: str

class ForgotPasswordRequest(BaseModel):
    account: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    account: str
    email: str

    class Config:
        orm_mode = True

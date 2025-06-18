from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class UserLogin(BaseModel):
    login: str
    password: str

class ForgotPasswordRequest(BaseModel):
    login: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    token: str

    class Config:
        orm_mode = True

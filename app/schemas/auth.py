from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username: str
    password: str = Field(..., max_length=72)
    employee_id: str
    role: Optional[str] = "employee"


class UserLogin(BaseModel):
    username: str
    password: str = Field(..., max_length=72)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ForgotPassword(BaseModel):
    username: str
    new_password: str = Field(..., max_length=72)

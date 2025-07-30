from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    """User registration model"""
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "user"

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_in: int
    user_info: dict

class User(BaseModel):
    """User model"""
    uid: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    """User creation model for Firebase"""
    email: str
    full_name: str
    role: str
    is_active: bool = True
    created_at: datetime

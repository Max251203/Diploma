from pydantic import BaseModel
from typing import Optional, Dict, List, Any


class UserBase(BaseModel):
    login: str
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    role: str = "student"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    login: Optional[str] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    id: int
    created_at: str

from pydantic import BaseModel
from typing import Optional, Dict, List, Any


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


class LoginForm(BaseModel):
    username: str
    password: str

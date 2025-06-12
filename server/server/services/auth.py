from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import jwt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from utils.security import verify_password, get_password_hash
import database


def authenticate_user(login: str, password: str) -> Optional[Dict[str, Any]]:
    """Аутентификация пользователя"""
    user = database.get_user_by_login(login)
    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return user


def create_access_token(user_id: int, role: str) -> str:
    """Создание JWT токена доступа"""
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": str(user_id),
        "role": role,
        "exp": expire
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def register_user(login: str, password: str, last_name: str, first_name: str, middle_name: str, role: str = "student") -> Dict[str, Any]:
    """Регистрация нового пользователя"""
    # Проверяем, что пользователь с таким логином не существует
    existing_user = database.get_user_by_login(login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким логином уже существует"
        )

    # Создаем пользователя
    user_id = database.create_user(
        login, password, last_name, first_name, middle_name, role)

    # Получаем созданного пользователя
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании пользователя"
        )

    return user

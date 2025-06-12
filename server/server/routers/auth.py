from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from models.auth import Token, LoginForm
from models.users import UserCreate, User
from services import auth as auth_service
from utils.security import get_current_active_user

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Получение токена доступа"""
    user = auth_service.authenticate_user(
        form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(user["id"], user["role"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=Token)
async def login(form_data: LoginForm):
    """Вход в систему"""
    user = auth_service.authenticate_user(
        form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(user["id"], user["role"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/register", response_model=User)
async def register(user_data: UserCreate):
    """Регистрация нового пользователя"""
    user = auth_service.register_user(
        user_data.login,
        user_data.password,
        user_data.last_name,
        user_data.first_name,
        user_data.middle_name,
        user_data.role
    )
    return user


@router.get("/me", response_model=User)
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    return current_user

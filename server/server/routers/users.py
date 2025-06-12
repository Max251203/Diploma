from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from models.users import User, UserCreate, UserUpdate
import database
from utils.security import get_current_active_user

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={401: {"description": "Unauthorized"}},
)


@router.get("/", response_model=List[User])
async def get_users(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получение списка всех пользователей"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    users = database.get_all_users()
    return users


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получение информации о пользователе по ID"""
    # Проверяем, что пользователь имеет права администратора или преподавателя,
    # или запрашивает информацию о себе
    if current_user["role"] not in ["admin", "teacher"] and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    return user


@router.post("/", response_model=User)
async def create_user(user_data: UserCreate, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Создание нового пользователя"""
    # Проверяем, что пользователь имеет права администратора
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    # Проверяем, что пользователь с таким логином не существует
    existing_user = database.get_user_by_login(user_data.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким логином уже существует"
        )

    # Создаем пользователя
    user_id = database.create_user(
        user_data.login,
        user_data.password,
        user_data.last_name,
        user_data.first_name,
        user_data.middle_name,
        user_data.role
    )

    # Получаем созданного пользователя
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании пользователя"
        )

    return user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Обновление информации о пользователе"""
    # Проверяем, что пользователь имеет права администратора или обновляет свой профиль
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    # Проверяем, что пользователь существует
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Если обычный пользователь пытается изменить роль, запрещаем
    if current_user["role"] != "admin" and user_data.role and user_data.role != user["role"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для изменения роли"
        )

    # Если указан новый логин, проверяем его уникальность
    if user_data.login and user_data.login != user["login"]:
        existing_user = database.get_user_by_login(user_data.login)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким логином уже существует"
            )

    # Обновляем пользователя
    success = database.update_user(user_id, user_data.dict(exclude_unset=True))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении пользователя"
        )

    # Получаем обновленного пользователя
    updated_user = database.get_user_by_id(user_id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении обновленного пользователя"
        )

    return updated_user


@router.delete("/{user_id}")
async def delete_user(user_id: int, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Удаление пользователя"""
    # Проверяем, что пользователь имеет права администратора
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    # Проверяем, что пользователь не пытается удалить себя
    if current_user["id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить свою учетную запись"
        )

    # Проверяем, что пользователь существует
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Удаляем пользователя
    success = database.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении пользователя"
        )

    return {"message": "Пользователь успешно удален"}

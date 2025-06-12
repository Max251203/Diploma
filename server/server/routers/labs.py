from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from models.labs import Lab, LabCreate, LabUpdate, Task, TaskCreate, TaskUpdate, LabResult, LabResultCreate, LabResultUpdate, TaskResult, TaskResultUpdate
from services import labs as labs_service
from utils.security import get_current_active_user
import database

router = APIRouter(
    prefix="/api/labs",
    tags=["labs"],
    responses={401: {"description": "Unauthorized"}},
)


@router.get("/", response_model=List[Lab])
async def get_labs(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получение списка всех лабораторных работ"""
    return labs_service.get_all_labs()


@router.get("/{lab_id}", response_model=Lab)
async def get_lab(lab_id: int, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получение лабораторной работы по ID"""
    return labs_service.get_lab(lab_id)


@router.post("/", response_model=Lab)
async def create_lab(lab_data: LabCreate, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Создание новой лабораторной работы"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    lab = labs_service.create_lab(
        lab_data.title,
        lab_data.description,
        lab_data.content,
        current_user["id"]
    )

    # Если указаны задания, создаем их
    if lab_data.tasks:
        for task_data in lab_data.tasks:
            labs_service.create_task(
                lab["id"],
                task_data.title,
                task_data.description,
                task_data.task_type,
                task_data.content,
                task_data.order_index,
                task_data.max_score
            )

        # Получаем обновленную лабораторную работу с заданиями
        lab = labs_service.get_lab(lab["id"])

    return lab


@router.put("/{lab_id}", response_model=Lab)
async def update_lab(
    lab_id: int,
    lab_data: LabUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Обновление лабораторной работы"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    # Проверяем, что лабораторная работа существует
    lab = labs_service.get_lab(lab_id)

    # Проверяем, что пользователь является создателем или администратором
    if current_user["role"] != "admin" and lab["created_by"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этой лабораторной работы"
        )

    # Обновляем лабораторную работу
    updated_lab = labs_service.update_lab(
        lab_id, lab_data.dict(exclude_unset=True))

    return updated_lab


@router.delete("/{lab_id}")
async def delete_lab(lab_id: int, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Удаление лабораторной работы"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    # Проверяем, что лабораторная работа существует
    lab = labs_service.get_lab(lab_id)

    # Проверяем, что пользователь является создателем или администратором
    if current_user["role"] != "admin" and lab["created_by"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этой лабораторной работы"
        )

    # Удаляем лабораторную работу
    labs_service.delete_lab(lab_id)

    return {"message": "Лабораторная работа успешно удалена"}


@router.post("/{lab_id}/tasks", response_model=Task)
async def create_task(
    lab_id: int,
    task_data: TaskCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Создание нового задания для лабораторной работы"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    # Проверяем, что лабораторная работа существует
    lab = labs_service.get_lab(lab_id)

    # Проверяем, что пользователь является создателем или администратором
    if current_user["role"] != "admin" and lab["created_by"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этой лабораторной работы"
        )

    # Создаем задание
    task = labs_service.create_task(
        lab_id,
        task_data.title,
        task_data.description,
        task_data.task_type,
        task_data.content,
        task_data.order_index,
        task_data.max_score
    )

    return task


@router.put("/{lab_id}/tasks/{task_id}", response_model=Task)
async def update_task(
    lab_id: int,
    task_id: int,
    task_data: TaskUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Обновление задания"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    # Проверяем, что лабораторная работа существует
    lab = labs_service.get_lab(lab_id)

    # Проверяем, что пользователь является создателем или администратором
    if current_user["role"] != "admin" and lab["created_by"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этой лабораторной работы"
        )

    # Обновляем задание
    task = labs_service.update_task(
        task_id, task_data.dict(exclude_unset=True))

    return task


@router.delete("/{lab_id}/tasks/{task_id}")
async def delete_task(
    lab_id: int,
    task_id: int,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Удаление задания"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

    # Проверяем, что лабораторная работа существует
    lab = labs_service.get_lab(lab_id)

    # Проверяем, что пользователь является создателем или администратором
    if current_user["role"] != "admin" and lab["created_by"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этой лабораторной работы"
        )

    # Удаляем задание
    labs_service.delete_task(task_id)

    return {"message": "Задание успешно удалено"}


@router.post("/{lab_id}/start", response_model=LabResult)
async def start_lab(lab_id: int, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Начало выполнения лабораторной работы"""
    # Проверяем, что лабораторная работа существует
    labs_service.get_lab(lab_id)

    # Создаем результат выполнения
    result = labs_service.create_lab_result(lab_id, current_user["id"])

    return result


@router.get("/results/{result_id}", response_model=LabResult)
async def get_lab_result(result_id: int, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получение результата выполнения лабораторной работы"""
    # Получаем результат
    result = labs_service.get_lab_result(result_id)

    # Проверяем, что пользователь имеет права на просмотр результата
    if current_user["role"] not in ["admin", "teacher"] and result["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этого результата"
        )

    return result


@router.put("/results/{result_id}", response_model=LabResult)
async def update_lab_result(
    result_id: int,
    result_data: LabResultUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Обновление результата выполнения лабораторной работы"""
    # Получаем результат
    result = labs_service.get_lab_result(result_id)

    # Проверяем права на обновление результата
    if result["user_id"] != current_user["id"] and current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления этого результата"
        )

    # Если пользователь пытается изменить статус на "submitted", проверяем, что он владелец
    if result_data.status == "submitted" and result["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец может отправить работу на проверку"
        )

    # Если пользователь пытается поставить оценку, проверяем, что он преподаватель или администратор
    if (result_data.score is not None or result_data.feedback is not None) and current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только преподаватель или администратор может оценивать работы"
        )

    # Обновляем результат
    updated_result = labs_service.update_lab_result(result_id, result_data.dict(
        exclude_unset=True), current_user["id"] if current_user["role"] in ["admin", "teacher"] else None)

    return updated_result


@router.put("/results/{result_id}/tasks/{task_result_id}", response_model=TaskResult)
async def update_task_result(
    result_id: int,
    task_result_id: int,
    task_result_data: TaskResultUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Обновление результата выполнения задания"""
    # Получаем результат лабораторной работы
    result = labs_service.get_lab_result(result_id)

    # Проверяем права на обновление результата задания
    if result["user_id"] != current_user["id"] and current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления этого результата"
        )

    # Если пользователь пытается поставить оценку, проверяем, что он преподаватель или администратор
    if (task_result_data.score is not None or task_result_data.feedback is not None) and current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только преподаватель или администратор может оценивать задания"
        )

    # Обновляем результат задания
    updated_task_result = labs_service.update_task_result(
        task_result_id, task_result_data.dict(exclude_unset=True))

    return updated_task_result


@router.get("/user/{user_id}/results", response_model=List[LabResult])
async def get_user_lab_results(user_id: int, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получение результатов выполнения лабораторных работ пользователя"""
    # Проверяем права на просмотр результатов
    if user_id != current_user["id"] and current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра результатов этого пользователя"
        )

    # Получаем результаты
    results = database.get_lab_results_by_user(user_id)

    # Для каждого результата получаем полную информацию
    full_results = []
    for result in results:
        full_result = labs_service.get_lab_result(result["id"])
        full_results.append(full_result)

    return full_results


@router.get("/{lab_id}/results", response_model=List[LabResult])
async def get_lab_results(lab_id: int, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получение результатов выполнения лабораторной работы"""
    # Проверяем, что пользователь имеет права преподавателя или администратора
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра результатов"
        )

    # Получаем результаты
    results = database.get_lab_results_by_lab(lab_id)

    # Для каждого результата получаем полную информацию
    full_results = []
    for result in results:
        full_result = labs_service.get_lab_result(result["id"])
        full_results.append(full_result)

    return full_results

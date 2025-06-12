from typing import Dict, List, Any, Optional
from fastapi import HTTPException, status
import database
import json


def create_lab(title: str, description: str, content: Dict[str, Any], created_by: int) -> Dict[str, Any]:
    """Создание новой лабораторной работы"""
    lab_id = database.create_lab(title, description, content, created_by)
    lab = database.get_lab(lab_id)
    if not lab:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании лабораторной работы"
        )
    return lab


def get_lab(lab_id: int) -> Dict[str, Any]:
    """Получение лабораторной работы по ID"""
    lab = database.get_lab(lab_id)
    if not lab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лабораторная работа не найдена"
        )
    return lab


def get_all_labs() -> List[Dict[str, Any]]:
    """Получение списка всех лабораторных работ"""
    return database.get_all_labs()


def update_lab(lab_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Обновление лабораторной работы"""
    success = database.update_lab(lab_id, data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лабораторная работа не найдена"
        )

    lab = database.get_lab(lab_id)
    if not lab:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении обновленной лабораторной работы"
        )

    return lab


def delete_lab(lab_id: int) -> bool:
    """Удаление лабораторной работы"""
    success = database.delete_lab(lab_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лабораторная работа не найдена"
        )
    return True


def create_task(lab_id: int, title: str, description: str, task_type: str, content: Dict[str, Any], order_index: int, max_score: float) -> Dict[str, Any]:
    """Создание нового задания для лабораторной работы"""
    # Проверяем существование лабораторной работы
    lab = database.get_lab(lab_id)
    if not lab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лабораторная работа не найдена"
        )

    task_id = database.create_task(
        lab_id, title, description, task_type, content, order_index, max_score)

    # Получаем обновленную лабораторную работу с заданиями
    lab = database.get_lab(lab_id)

    # Находим созданное задание
    task = None
    for t in lab["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if not task:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании задания"
        )

    return task


def update_task(task_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Обновление задания"""
    success = database.update_task(task_id, data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задание не найдено"
        )

    # Получаем обновленное задание
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT lab_id FROM lab_tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задание не найдено"
        )

    lab_id = row["lab_id"]
    lab = database.get_lab(lab_id)

    # Находим обновленное задание
    task = None
    for t in lab["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if not task:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении обновленного задания"
        )

    return task


def delete_task(task_id: int) -> bool:
    """Удаление задания"""
    success = database.delete_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задание не найдено"
        )
    return True


def add_device_to_task(task_id: int, device_id: str, required_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Добавление устройства к заданию"""
    # Проверяем существование задания
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM lab_tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задание не найдено"
        )
    conn.close()

    device_task_id = database.add_device_to_task(
        task_id, device_id, required_state)

    return {
        "id": device_task_id,
        "task_id": task_id,
        "device_id": device_id,
        "required_state": required_state
    }


def remove_device_from_task(task_id: int, device_id: str) -> bool:
    """Удаление устройства из задания"""
    success = database.remove_device_from_task(task_id, device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено в задании"
        )
    return True


def create_lab_result(lab_id: int, user_id: int) -> Dict[str, Any]:
    """Создание результата выполнения лабораторной работы"""
    # Проверяем существование лабораторной работы
    lab = database.get_lab(lab_id)
    if not lab:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лабораторная работа не найдена"
        )

    # Проверяем существование пользователя
    user = database.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Проверяем, нет ли уже начатой работы
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM lab_results WHERE lab_id = ? AND user_id = ? AND status = 'in_progress'",
        (lab_id, user_id)
    )
    existing_result = cursor.fetchone()
    conn.close()

    if existing_result:
        return database.get_lab_result(existing_result["id"])

    result_id = database.create_lab_result(lab_id, user_id)

    # Создаем пустые результаты для всех заданий
    for task in lab["tasks"]:
        database.create_task_result(result_id, task["id"])

    return database.get_lab_result(result_id)


def get_lab_result(result_id: int) -> Dict[str, Any]:
    """Получение результата выполнения лабораторной работы по ID"""
    result = database.get_lab_result(result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Результат не найден"
        )
    return result


def update_lab_result(result_id: int, data: Dict[str, Any], user_id: int = None) -> Dict[str, Any]:
    """Обновление результата выполнения лабораторной работы"""
    # Если указан user_id, добавляем его в данные для обновления
    if user_id is not None:
        data["reviewed_by"] = user_id

    success = database.update_lab_result(result_id, data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Результат не найден"
        )

    return database.get_lab_result(result_id)


def update_task_result(task_result_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Обновление результата выполнения задания"""
    success = database.update_task_result(task_result_id, data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Результат задания не найден"
        )

    # Получаем обновленный результат задания
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM task_results WHERE id = ?",
                   (task_result_id,))
    task_result = cursor.fetchone()
    conn.close()

    if not task_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Результат задания не найден"
        )

    task_result_dict = dict(task_result)
    if task_result_dict["answer"]:
        task_result_dict["answer"] = json.loads(task_result_dict["answer"])

    return task_result_dict

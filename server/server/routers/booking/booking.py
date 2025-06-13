from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Any
from datetime import datetime, timedelta
from models.booking.booking import BookingCreate, BookingUpdate, Booking, DeviceAvailability, BookingRequest, BookingResponse
from services.booking import booking_service
from utils.security import get_current_active_user
from services.websocket import ws_manager

router = APIRouter(
    prefix="/api/booking",
    tags=["booking"],
    responses={401: {"description": "Unauthorized"}},
)


@router.get("/devices/{device_id}/availability")
async def get_device_availability(
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Получение информации о доступности устройства"""
    # Проверяем, что устройство существует
    from services import devices as devices_service
    try:
        devices_service.get_device(device_id)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено"
        )

    # Очищаем истекшие бронирования
    booking_service.cleanup_expired_bookings()

    # Получаем информацию о доступности
    availability = booking_service.get_device_availability(device_id)
    return availability


@router.get("/devices/{device_id}/queue")
async def get_device_queue(
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Получение очереди бронирований для устройства"""
    # Проверяем, что устройство существует
    from services import devices as devices_service
    try:
        devices_service.get_device(device_id)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено"
        )

    # Очищаем истекшие бронирования
    booking_service.cleanup_expired_bookings()

    # Получаем очередь
    queue = booking_service.get_device_queue(device_id)
    return queue


@router.post("/devices/{device_id}", response_model=BookingResponse)
async def book_device(
    device_id: str,
    booking_data: BookingRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Бронирование устройства"""
    # Проверяем, что устройство существует
    from services import devices as devices_service
    try:
        devices_service.get_device(device_id)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено"
        )

    # Проверяем корректность времени
    if booking_data.start_time >= booking_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Время начала должно быть раньше времени окончания"
        )

    # Проверяем, что время начала не в прошлом
    if booking_data.start_time < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Время начала не может быть в прошлом"
        )

    # Очищаем истекшие бронирования
    booking_service.cleanup_expired_bookings()

    # Проверяем доступность устройства
    if not booking_service.is_device_available(device_id, booking_data.start_time, booking_data.end_time):
        # Получаем информацию о текущей очереди
        queue = booking_service.get_device_queue(device_id)

        return BookingResponse(
            success=False,
            message="Устройство недоступно в указанное время",
            position_in_queue=len(queue) + 1
        )

    try:
        # Создаем бронирование
        booking_id = booking_service.create_booking(
            device_id,
            current_user["id"],
            booking_data.start_time,
            booking_data.end_time,
            booking_data.purpose
        )

        # Отправляем уведомление через WebSocket
        background_tasks.add_task(
            ws_manager.broadcast_booking_notification,
            device_id,
            current_user["id"],
            "created",
            {
                "booking_id": booking_id,
                "device_id": device_id,
                "start_time": booking_data.start_time.isoformat(),
                "end_time": booking_data.end_time.isoformat(),
                "user": {
                    "id": current_user["id"],
                    "login": current_user["login"]
                }
            }
        )

        return BookingResponse(
            success=True,
            booking_id=booking_id,
            message="Устройство успешно забронировано"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при бронировании: {str(e)}"
        )


@router.get("/user/bookings")
async def get_user_bookings(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Получение всех бронирований пользователя"""
    # Очищаем истекшие бронирования
    booking_service.cleanup_expired_bookings()

    # Получаем бронирования пользователя
    bookings = booking_service.get_user_bookings(current_user["id"])
    return bookings


@router.get("/{booking_id}")
async def get_booking(
    booking_id: int,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Получение информации о бронировании"""
    booking = booking_service.get_booking(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронирование не найдено"
        )

    # Проверяем права доступа (владелец или администратор/преподаватель)
    if booking["user_id"] != current_user["id"] and current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для просмотра этого бронирования"
        )

    return booking


@router.put("/{booking_id}")
async def update_booking(
    booking_id: int,
    booking_data: BookingUpdate,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Обновление бронирования"""
    booking = booking_service.get_booking(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронирование не найдено"
        )

    # Проверяем права доступа (владелец или администратор/преподаватель)
    if booking["user_id"] != current_user["id"] and current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для изменения этого бронирования"
        )

    # Проверяем, что бронирование активно
    if booking["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Можно изменять только активные бронирования"
        )

    # Обновляем данные
    data = booking_data.dict(exclude_unset=True)
    success = booking_service.update_booking(booking_id, data)

    if success:
        # Отправляем уведомление через WebSocket
        background_tasks.add_task(
            ws_manager.broadcast_booking_notification,
            booking["device_id"],
            current_user["id"],
            "updated",
            {
                "booking_id": booking_id,
                "device_id": booking["device_id"],
                "changes": data
            }
        )

        return {"message": "Бронирование успешно обновлено"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении бронирования"
        )


@router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Отмена бронирования"""
    booking = booking_service.get_booking(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронирование не найдено"
        )

    # Проверяем права доступа (владелец или администратор/преподаватель)
    is_owner = booking["user_id"] == current_user["id"]
    is_admin = current_user["role"] in ["admin", "teacher"]

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для отмены этого бронирования"
        )

    # Отменяем бронирование
    success = booking_service.cancel_booking(booking_id)

    if success:
        # Отправляем уведомление через WebSocket
        background_tasks.add_task(
            ws_manager.broadcast_booking_notification,
            booking["device_id"],
            current_user["id"],
            "cancelled",
            {
                "booking_id": booking_id,
                "device_id": booking["device_id"],
                "cancelled_by": {
                    "id": current_user["id"],
                    "login": current_user["login"],
                    "is_owner": is_owner
                }
            }
        )

        return {"message": "Бронирование успешно отменено"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при отмене бронирования"
        )

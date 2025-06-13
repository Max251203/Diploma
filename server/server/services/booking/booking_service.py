from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import database
import json
from models.booking.booking import Booking, DeviceAvailability
from config import logger


def get_device_bookings(device_id: str) -> List[Dict[str, Any]]:
    """Получение всех бронирований для устройства"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM device_bookings 
        WHERE device_id = ? 
        ORDER BY start_time
    """, (device_id,))
    bookings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return bookings


def get_user_bookings(user_id: int) -> List[Dict[str, Any]]:
    """Получение всех бронирований пользователя"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, d.name as device_name 
        FROM device_bookings b
        LEFT JOIN devices d ON b.device_id = d.id
        WHERE b.user_id = ? 
        ORDER BY b.start_time
    """, (user_id,))
    bookings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return bookings


def get_booking(booking_id: int) -> Optional[Dict[str, Any]]:
    """Получение информации о бронировании по ID"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM device_bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()
    conn.close()

    if booking:
        return dict(booking)
    return None


def create_booking(device_id: str, user_id: int, start_time: datetime,
                   end_time: datetime, purpose: str) -> int:
    """Создание нового бронирования"""
    # Проверяем, доступно ли устройство в указанное время
    if not is_device_available(device_id, start_time, end_time):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Устройство недоступно в указанное время"
        )

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO device_bookings 
        (device_id, user_id, start_time, end_time, purpose, status, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        device_id,
        user_id,
        start_time.isoformat(),
        end_time.isoformat(),
        purpose,
        "active",
        datetime.now().isoformat()
    ))
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()

    logger.info(
        f"Создано бронирование {booking_id} для устройства {device_id} пользователем {user_id}")
    return booking_id


def update_booking(booking_id: int, data: Dict[str, Any]) -> bool:
    """Обновление бронирования"""
    booking = get_booking(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронирование не найдено"
        )

    # Если меняется время, проверяем доступность
    if ('start_time' in data or 'end_time' in data) and booking['status'] == 'active':
        start_time = data.get('start_time', booking['start_time'])
        end_time = data.get('end_time', booking['end_time'])

        # Проверяем, не пересекается ли с другими бронированиями
        if not is_device_available(booking['device_id'], start_time, end_time, exclude_booking_id=booking_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Устройство недоступно в указанное время"
            )

    fields = []
    values = []

    for key, value in data.items():
        if key in ['start_time', 'end_time'] and isinstance(value, datetime):
            fields.append(f"{key} = ?")
            values.append(value.isoformat())
        elif key in ['purpose', 'status']:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    values.append(booking_id)

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE device_bookings SET {', '.join(fields)} WHERE id = ?",
        values
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    logger.info(f"Обновлено бронирование {booking_id}: {data}")
    return success


def cancel_booking(booking_id: int, user_id: int = None) -> bool:
    """Отмена бронирования"""
    booking = get_booking(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронирование не найдено"
        )

    # Если указан user_id, проверяем, что это его бронирование
    if user_id and booking['user_id'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для отмены этого бронирования"
        )

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE device_bookings SET status = 'cancelled' WHERE id = ?",
        (booking_id,)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    logger.info(f"Отменено бронирование {booking_id}")
    return success


def is_device_available(device_id: str, start_time: datetime, end_time: datetime,
                        exclude_booking_id: int = None) -> bool:
    """Проверка доступности устройства в указанное время"""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT COUNT(*) FROM device_bookings 
        WHERE device_id = ? 
        AND status = 'active'
        AND NOT (end_time <= ? OR start_time >= ?)
    """
    params = [device_id, start_time.isoformat(), end_time.isoformat()]

    if exclude_booking_id:
        query += " AND id != ?"
        params.append(exclude_booking_id)

    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()

    return count == 0


def get_device_availability(device_id: str) -> DeviceAvailability:
    """Получение информации о доступности устройства"""
    now = datetime.now()

    # Получаем текущее активное бронирование
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM device_bookings 
        WHERE device_id = ? 
        AND status = 'active'
        AND start_time <= ? 
        AND end_time > ?
        ORDER BY start_time
        LIMIT 1
    """, (device_id, now.isoformat(), now.isoformat()))
    current_booking = cursor.fetchone()

    # Получаем следующие бронирования
    cursor.execute("""
        SELECT * FROM device_bookings 
        WHERE device_id = ? 
        AND status = 'active'
        AND start_time > ?
        ORDER BY start_time
    """, (device_id, now.isoformat()))
    upcoming_bookings = cursor.fetchall()
    conn.close()

    # Формируем ответ
    is_available = current_booking is None
    next_available = None

    if not is_available and current_booking:
        next_available = datetime.fromisoformat(current_booking['end_time'])
    elif upcoming_bookings:
        next_available = datetime.fromisoformat(
            upcoming_bookings[0]['start_time'])

    return DeviceAvailability(
        device_id=device_id,
        is_available=is_available,
        current_booking=dict(current_booking) if current_booking else None,
        next_available=next_available,
        queue_length=len(upcoming_bookings)
    )


def get_device_queue(device_id: str) -> List[Dict[str, Any]]:
    """Получение очереди бронирований для устройства"""
    now = datetime.now()

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, u.login as user_login, u.last_name, u.first_name
        FROM device_bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.device_id = ? 
        AND b.status = 'active'
        AND b.end_time > ?
        ORDER BY b.start_time
    """, (device_id, now.isoformat()))
    queue = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return queue


def cleanup_expired_bookings():
    """Очистка истекших бронирований"""
    now = datetime.now()

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE device_bookings 
        SET status = 'completed' 
        WHERE status = 'active' 
        AND end_time < ?
    """, (now.isoformat(),))
    count = cursor.rowcount
    conn.commit()
    conn.close()

    if count > 0:
        logger.info(f"Очищено {count} истекших бронирований")

    return count

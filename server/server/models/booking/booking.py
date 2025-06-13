from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class BookingBase(BaseModel):
    """Базовая модель бронирования устройства"""
    device_id: str
    user_id: int
    start_time: datetime
    end_time: datetime
    purpose: str


class BookingCreate(BookingBase):
    """Модель для создания бронирования"""
    pass


class BookingUpdate(BaseModel):
    """Модель для обновления бронирования"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    purpose: Optional[str] = None
    status: Optional[str] = None


class Booking(BookingBase):
    """Полная модель бронирования с ID и статусом"""
    id: int
    status: str = "active"  # active, completed, cancelled
    created_at: datetime


class BookingQueue(BaseModel):
    """Модель очереди бронирования для устройства"""
    device_id: str
    current_booking: Optional[Booking] = None
    queue: List[Booking] = []


class DeviceAvailability(BaseModel):
    """Модель доступности устройства"""
    device_id: str
    is_available: bool
    current_booking: Optional[Booking] = None
    next_available: Optional[datetime] = None
    queue_length: int = 0


class BookingRequest(BaseModel):
    """Модель запроса на бронирование"""
    device_id: str
    start_time: datetime
    end_time: datetime
    purpose: str


class BookingResponse(BaseModel):
    """Модель ответа на запрос бронирования"""
    success: bool
    booking_id: Optional[int] = None
    message: str
    position_in_queue: Optional[int] = None

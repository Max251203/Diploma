from PySide6.QtCore import QThread, Signal
from typing import Dict, List, Any, Optional
from core.api import api_client


class GetDeviceAvailabilityWorker(QThread):
    """Рабочий поток для получения информации о доступности устройства"""

    result_ready = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client, device_id: str):
        super().__init__()
        self.api_client = api_client
        self.device_id = device_id

    def run(self):
        try:
            result = self.api_client.get_device_availability(self.device_id)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class GetDeviceQueueWorker(QThread):
    """Рабочий поток для получения очереди бронирований для устройства"""

    result_ready = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client, device_id: str):
        super().__init__()
        self.api_client = api_client
        self.device_id = device_id

    def run(self):
        try:
            result = self.api_client.get_device_queue(self.device_id)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class BookDeviceWorker(QThread):
    """Рабочий поток для бронирования устройства"""

    result_ready = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client, device_id: str, start_time: str, end_time: str, purpose: str):
        super().__init__()
        self.api_client = api_client
        self.device_id = device_id
        self.start_time = start_time
        self.end_time = end_time
        self.purpose = purpose

    def run(self):
        try:
            result = self.api_client.book_device(
                self.device_id,
                self.start_time,
                self.end_time,
                self.purpose
            )
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class GetUserBookingsWorker(QThread):
    """Рабочий поток для получения всех бронирований пользователя"""

    result_ready = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client

    def run(self):
        try:
            result = self.api_client.get_user_bookings()
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class CancelBookingWorker(QThread):
    """Рабочий поток для отмены бронирования"""

    result_ready = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self, api_client, booking_id: int):
        super().__init__()
        self.api_client = api_client
        self.booking_id = booking_id

    def run(self):
        try:
            result = self.api_client.cancel_booking(self.booking_id)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

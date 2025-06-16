from PySide6.QtCore import QObject, Signal
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.api import api_client
from core.booking.booking_worker import (
    GetDeviceAvailabilityWorker, GetDeviceQueueWorker,
    BookDeviceWorker, GetUserBookingsWorker, CancelBookingWorker
)
from core.logger import get_logger


class BookingManager(QObject):
    """Менеджер для работы с бронированием устройств"""

    # Сигналы для уведомления об изменениях
    device_availability_updated = Signal(str, dict)
    device_queue_updated = Signal(str, list)
    user_bookings_updated = Signal(list)
    booking_created = Signal(dict)
    booking_cancelled = Signal(int)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self._workers = []

    def get_device_availability(self, device_id: str):
        """Получение информации о доступности устройства"""
        worker = GetDeviceAvailabilityWorker(api_client, device_id)
        worker.result_ready.connect(
            lambda result: self._handle_availability_result(device_id, result))
        worker.error_occurred.connect(self.error_occurred.emit)
        self._workers.append(worker)
        worker.start()

    def get_device_queue(self, device_id: str):
        """Получение очереди бронирований для устройства"""
        worker = GetDeviceQueueWorker(api_client, device_id)
        worker.result_ready.connect(
            lambda result: self._handle_queue_result(device_id, result))
        worker.error_occurred.connect(self.error_occurred.emit)
        self._workers.append(worker)
        worker.start()

    def book_device(self, device_id: str, start_time: datetime, end_time: datetime, purpose: str):
        """Бронирование устройства"""
        worker = BookDeviceWorker(
            api_client,
            device_id,
            start_time.isoformat(),
            end_time.isoformat(),
            purpose
        )
        worker.result_ready.connect(self._handle_booking_result)
        worker.error_occurred.connect(self.error_occurred.emit)
        self._workers.append(worker)
        worker.start()

    def get_user_bookings(self):
        """Получение всех бронирований пользователя"""
        worker = GetUserBookingsWorker(api_client)
        worker.result_ready.connect(self._handle_user_bookings_result)
        worker.error_occurred.connect(self.error_occurred.emit)
        self._workers.append(worker)
        worker.start()

    def cancel_booking(self, booking_id: int):
        """Отмена бронирования"""
        worker = CancelBookingWorker(api_client, booking_id)
        worker.result_ready.connect(
            lambda result: self._handle_cancel_result(booking_id, result))
        worker.error_occurred.connect(self.error_occurred.emit)
        self._workers.append(worker)
        worker.start()

    def _handle_availability_result(self, device_id: str, result: Optional[Dict[str, Any]]):
        """Обработка результата получения доступности устройства"""
        if result:
            self.device_availability_updated.emit(device_id, result)
            self.logger.info(
                f"Получена информация о доступности устройства {device_id}")
        else:
            self.logger.error(
                f"Не удалось получить информацию о доступности устройства {device_id}")

    def _handle_queue_result(self, device_id: str, result: Optional[List[Dict[str, Any]]]):
        """Обработка результата получения очереди бронирований"""
        if result:
            self.device_queue_updated.emit(device_id, result)
            self.logger.info(
                f"Получена очередь бронирований для устройства {device_id}")
        else:
            self.logger.error(
                f"Не удалось получить очередь бронирований для устройства {device_id}")

    def _handle_booking_result(self, result: Optional[Dict[str, Any]]):
        """Обработка результата бронирования устройства"""
        if result and result.get("success"):
            self.booking_created.emit(result)
            self.logger.success(
                f"Устройство успешно забронировано: {result.get('booking_id')}")
            # Обновляем список бронирований пользователя
            self.get_user_bookings()
        else:
            message = result.get(
                "message", "Неизвестная ошибка") if result else "Не удалось забронировать устройство"
            self.error_occurred.emit(message)
            self.logger.error(f"Ошибка бронирования: {message}")

    def _handle_user_bookings_result(self, result: Optional[List[Dict[str, Any]]]):
        """Обработка результата получения бронирований пользователя"""
        if result is not None:
            self.user_bookings_updated.emit(result)
            self.logger.info(
                f"Получено {len(result)} бронирований пользователя")
        else:
            self.logger.error("Не удалось получить бронирования пользователя")

    def _handle_cancel_result(self, booking_id: int, result: bool):
        """Обработка результата отмены бронирования"""
        if result:
            self.booking_cancelled.emit(booking_id)
            self.logger.success(f"Бронирование {booking_id} успешно отменено")
            # Обновляем список бронирований пользователя
            self.get_user_bookings()
        else:
            self.error_occurred.emit(
                f"Не удалось отменить бронирование {booking_id}")
            self.logger.error(f"Не удалось отменить бронирование {booking_id}")

    def cleanup_workers(self):
        """Очистка завершенных рабочих потоков"""
        for worker in self._workers[:]:
            if not worker.isRunning():
                worker.deleteLater()
                self._workers.remove(worker)
            else:
                # Если поток все еще работает, пытаемся его остановить
                worker.quit()
                worker.wait(1000)  # Ждем до 1 секунды
                if worker.isRunning():
                    worker.terminate()
                worker.deleteLater()
                self._workers.remove(worker)

from core.booking.booking_manager import BookingManager
from core.booking.booking_worker import (
    GetDeviceAvailabilityWorker, GetDeviceQueueWorker,
    BookDeviceWorker, GetUserBookingsWorker, CancelBookingWorker
)

# Создаем глобальный экземпляр менеджера бронирования
booking_manager = BookingManager()

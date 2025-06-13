from core.api.api_client import APIClient
from core.api.api_worker import (
    APIWorker, LoginWorker, RegisterWorker, GetDevicesWorker, GetDeviceWorker,
    SendDeviceCommandWorker, GetDeviceHistoryWorker, GetDeviceAvailabilityWorker,
    GetDeviceQueueWorker, BookDeviceWorker, GetUserBookingsWorker, CancelBookingWorker,
    GetLabsWorker, GetLabWorker, StartLabWorker, GetLabResultWorker, UpdateLabResultWorker,
    UpdateTaskResultWorker, GetUserLabResultsWorker, GetLabResultsWorker, CreateLabWorker,
    UpdateLabWorker, DeleteLabWorker, CreateTaskWorker, UpdateTaskWorker, DeleteTaskWorker,
    GetUsersWorker, GetUserWorker, CreateUserWorker, UpdateUserWorker, DeleteUserWorker
)

# Создаем глобальный экземпляр API клиента
api_client = APIClient()

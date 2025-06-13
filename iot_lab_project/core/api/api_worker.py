from PySide6.QtCore import QThread, Signal
from typing import Dict, List, Any, Optional, Callable
from core.api.api_client import APIClient


class APIWorker(QThread):
    """Рабочий поток для выполнения API запросов"""

    # Сигналы для уведомления о результатах
    result_ready = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client: APIClient, method_name: str, *args, **kwargs):
        super().__init__()
        self.api_client = api_client
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        """Выполнение API запроса в отдельном потоке"""
        try:
            # Получаем метод API клиента по имени
            method = getattr(self.api_client, self.method_name)

            # Вызываем метод с переданными аргументами
            self.result = method(*self.args, **self.kwargs)

            # Отправляем сигнал с результатом
            self.result_ready.emit(self.result)
        except Exception as e:
            # В случае ошибки отправляем сигнал с сообщением об ошибке
            self.error_occurred.emit(str(e))


class LoginWorker(APIWorker):
    """Рабочий поток для входа в систему"""

    def __init__(self, api_client: APIClient, username: str, password: str):
        super().__init__(api_client, "login", username, password)


class RegisterWorker(APIWorker):
    """Рабочий поток для регистрации"""

    def __init__(self, api_client: APIClient, user_data: Dict[str, Any]):
        super().__init__(api_client, "register", user_data)


class GetDevicesWorker(APIWorker):
    """Рабочий поток для получения списка устройств"""

    def __init__(self, api_client: APIClient):
        super().__init__(api_client, "get_devices")


class GetDeviceWorker(APIWorker):
    """Рабочий поток для получения информации об устройстве"""

    def __init__(self, api_client: APIClient, device_id: str):
        super().__init__(api_client, "get_device", device_id)


class SendDeviceCommandWorker(APIWorker):
    """Рабочий поток для отправки команды устройству"""

    def __init__(self, api_client: APIClient, device_id: str, command: Dict[str, Any]):
        super().__init__(api_client, "send_device_command", device_id, command)


class GetDeviceHistoryWorker(APIWorker):
    """Рабочий поток для получения истории показаний устройства"""

    def __init__(self, api_client: APIClient, device_id: str, limit: int = 100):
        super().__init__(api_client, "get_device_history", device_id, limit)


class GetDeviceAvailabilityWorker(APIWorker):
    """Рабочий поток для получения информации о доступности устройства"""

    def __init__(self, api_client: APIClient, device_id: str):
        super().__init__(api_client, "get_device_availability", device_id)


class GetDeviceQueueWorker(APIWorker):
    """Рабочий поток для получения очереди бронирований для устройства"""

    def __init__(self, api_client: APIClient, device_id: str):
        super().__init__(api_client, "get_device_queue", device_id)


class BookDeviceWorker(APIWorker):
    """Рабочий поток для бронирования устройства"""

    def __init__(self, api_client: APIClient, device_id: str, start_time: str, end_time: str, purpose: str):
        super().__init__(api_client, "book_device", device_id, start_time, end_time, purpose)


class GetUserBookingsWorker(APIWorker):
    """Рабочий поток для получения всех бронирований пользователя"""

    def __init__(self, api_client: APIClient):
        super().__init__(api_client, "get_user_bookings")


class CancelBookingWorker(APIWorker):
    """Рабочий поток для отмены бронирования"""

    def __init__(self, api_client: APIClient, booking_id: int):
        super().__init__(api_client, "cancel_booking", booking_id)


class GetLabsWorker(APIWorker):
    """Рабочий поток для получения списка лабораторных работ"""

    def __init__(self, api_client: APIClient):
        super().__init__(api_client, "get_labs")


class GetLabWorker(APIWorker):
    """Рабочий поток для получения информации о лабораторной работе"""

    def __init__(self, api_client: APIClient, lab_id: int):
        super().__init__(api_client, "get_lab", lab_id)


class StartLabWorker(APIWorker):
    """Рабочий поток для начала выполнения лабораторной работы"""

    def __init__(self, api_client: APIClient, lab_id: int):
        super().__init__(api_client, "start_lab", lab_id)


class GetLabResultWorker(APIWorker):
    """Рабочий поток для получения результата выполнения лабораторной работы"""

    def __init__(self, api_client: APIClient, result_id: int):
        super().__init__(api_client, "get_lab_result", result_id)


class UpdateLabResultWorker(APIWorker):
    """Рабочий поток для обновления результата выполнения лабораторной работы"""

    def __init__(self, api_client: APIClient, result_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "update_lab_result", result_id, data)


class UpdateTaskResultWorker(APIWorker):
    """Рабочий поток для обновления результата выполнения задания"""

    def __init__(self, api_client: APIClient, result_id: int, task_result_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "update_task_result", result_id, task_result_id, data)


class GetUserLabResultsWorker(APIWorker):
    """Рабочий поток для получения результатов выполнения лабораторных работ пользователя"""

    def __init__(self, api_client: APIClient, user_id: int):
        super().__init__(api_client, "get_user_lab_results", user_id)


class GetLabResultsWorker(APIWorker):
    """Рабочий поток для получения результатов выполнения лабораторной работы"""

    def __init__(self, api_client: APIClient, lab_id: int):
        super().__init__(api_client, "get_lab_results", lab_id)


class CreateLabWorker(APIWorker):
    """Рабочий поток для создания новой лабораторной работы"""

    def __init__(self, api_client: APIClient, data: Dict[str, Any]):
        super().__init__(api_client, "create_lab", data)


class UpdateLabWorker(APIWorker):
    """Рабочий поток для обновления лабораторной работы"""

    def __init__(self, api_client: APIClient, lab_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "update_lab", lab_id, data)


class DeleteLabWorker(APIWorker):
    """Рабочий поток для удаления лабораторной работы"""

    def __init__(self, api_client: APIClient, lab_id: int):
        super().__init__(api_client, "delete_lab", lab_id)


class CreateTaskWorker(APIWorker):
    """Рабочий поток для создания нового задания для лабораторной работы"""

    def __init__(self, api_client: APIClient, lab_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "create_task", lab_id, data)


class UpdateTaskWorker(APIWorker):
    """Рабочий поток для обновления задания"""

    def __init__(self, api_client: APIClient, lab_id: int, task_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "update_task", lab_id, task_id, data)


class DeleteTaskWorker(APIWorker):
    """Рабочий поток для удаления задания"""

    def __init__(self, api_client: APIClient, lab_id: int, task_id: int):
        super().__init__(api_client, "delete_task", lab_id, task_id)


class GetUsersWorker(APIWorker):
    """Рабочий поток для получения списка пользователей"""

    def __init__(self, api_client: APIClient):
        super().__init__(api_client, "get_users")


class GetUserWorker(APIWorker):
    """Рабочий поток для получения информации о пользователе"""

    def __init__(self, api_client: APIClient, user_id: int):
        super().__init__(api_client, "get_user", user_id)


class CreateUserWorker(APIWorker):
    """Рабочий поток для создания нового пользователя"""

    def __init__(self, api_client: APIClient, data: Dict[str, Any]):
        super().__init__(api_client, "create_user", data)


class UpdateUserWorker(APIWorker):
    """Рабочий поток для обновления пользователя"""

    def __init__(self, api_client: APIClient, user_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "update_user", user_id, data)


class DeleteUserWorker(APIWorker):
    """Рабочий поток для удаления пользователя"""

    def __init__(self, api_client: APIClient, user_id: int):
        super().__init__(api_client, "delete_user", user_id)

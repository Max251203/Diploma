from PySide6.QtCore import QThread, Signal
from typing import Dict, List, Any, Optional, Callable
from core.logger import get_logger

logger = get_logger()


class APIWorker(QThread):
    """Рабочий поток для выполнения API запросов"""

    # Сигналы для уведомления о результатах
    result_ready = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client, method_name: str, *args, **kwargs):
        super().__init__()
        self.api_client = api_client
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self._is_running = False
        logger.info(f"Создан APIWorker для метода {method_name}")

    def run(self):
        """Выполнение API запроса в отдельном потоке"""
        self._is_running = True
        logger.info(f"Запуск APIWorker для метода {self.method_name}")
        try:
            # Получаем метод API клиента по имени
            method = getattr(self.api_client, self.method_name)

            # Вызываем метод с переданными аргументами
            self.result = method(*self.args, **self.kwargs)

            # Отправляем сигнал с результатом
            if self._is_running:  # Проверяем, что поток не был остановлен
                logger.info(
                    f"APIWorker для метода {self.method_name} успешно выполнен")
                self.result_ready.emit(self.result)
        except Exception as e:
            # В случае ошибки отправляем сигнал с сообщением об ошибке
            logger.error(
                f"Ошибка в APIWorker для метода {self.method_name}: {e}")
            if self._is_running:  # Проверяем, что поток не был остановлен
                self.error_occurred.emit(str(e))
        finally:
            self._is_running = False
            logger.info(f"APIWorker для метода {self.method_name} завершен")

    def stop(self):
        """Безопасная остановка потока"""
        logger.info(f"Остановка APIWorker для метода {self.method_name}")
        self._is_running = False
        self.quit()
        self.wait()

    def __del__(self):
        logger.info(f"Уничтожение APIWorker для метода {self.method_name}")
        if self.isRunning():
            logger.warning(
                f"APIWorker для метода {self.method_name} уничтожается во время работы!")
            self.stop()


class LoginWorker(APIWorker):
    """Рабочий поток для входа в систему"""

    def __init__(self, api_client, username: str, password: str):
        super().__init__(api_client, "login", username, password)
        logger.info(f"Создан LoginWorker для пользователя {username}")


class RegisterWorker(APIWorker):
    """Рабочий поток для регистрации"""

    def __init__(self, api_client, user_data: Dict[str, Any]):
        super().__init__(api_client, "register", user_data)
        logger.info(
            f"Создан RegisterWorker для пользователя {user_data.get('login')}")


class GetUsersWorker(APIWorker):
    """Рабочий поток для получения списка пользователей"""

    def __init__(self, api_client):
        super().__init__(api_client, "get_users")
        logger.info("Создан GetUsersWorker")


class GetUserWorker(APIWorker):
    """Рабочий поток для получения информации о пользователе"""

    def __init__(self, api_client, user_id: int):
        super().__init__(api_client, "get_user", user_id)
        logger.info(f"Создан GetUserWorker для пользователя {user_id}")


class UpdateUserWorker(APIWorker):
    """Рабочий поток для обновления пользователя"""

    def __init__(self, api_client, user_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "update_user", user_id, data)
        logger.info(f"Создан UpdateUserWorker для пользователя {user_id}")


class DeleteUserWorker(APIWorker):
    """Рабочий поток для удаления пользователя"""

    def __init__(self, api_client, user_id: int):
        super().__init__(api_client, "delete_user", user_id)
        logger.info(f"Создан DeleteUserWorker для пользователя {user_id}")


class CreateUserWorker(APIWorker):
    """Рабочий поток для создания нового пользователя"""

    def __init__(self, api_client, data: Dict[str, Any]):
        super().__init__(api_client, "create_user", data)
        logger.info(
            f"Создан CreateUserWorker для пользователя {data.get('login')}")


class GetDevicesWorker(APIWorker):
    """Рабочий поток для получения списка устройств"""

    def __init__(self, api_client):
        super().__init__(api_client, "get_devices")
        logger.info("Создан GetDevicesWorker")


class GetDeviceWorker(APIWorker):
    """Рабочий поток для получения информации об устройстве"""

    def __init__(self, api_client, device_id: str):
        super().__init__(api_client, "get_device", device_id)
        logger.info(f"Создан GetDeviceWorker для устройства {device_id}")


class SendDeviceCommandWorker(APIWorker):
    """Рабочий поток для отправки команды устройству"""

    def __init__(self, api_client, device_id: str, command: Dict[str, Any]):
        super().__init__(api_client, "send_device_command", device_id, command)
        logger.info(
            f"Создан SendDeviceCommandWorker для устройства {device_id}")


class GetLabsWorker(APIWorker):
    """Рабочий поток для получения списка лабораторных работ"""

    def __init__(self, api_client):
        super().__init__(api_client, "get_labs")
        logger.info("Создан GetLabsWorker")


class GetLabWorker(APIWorker):
    """Рабочий поток для получения информации о лабораторной работе"""

    def __init__(self, api_client, lab_id: int):
        super().__init__(api_client, "get_lab", lab_id)
        logger.info(f"Создан GetLabWorker для лабораторной работы {lab_id}")


class StartLabWorker(APIWorker):
    """Рабочий поток для начала выполнения лабораторной работы"""

    def __init__(self, api_client, lab_id: int):
        super().__init__(api_client, "start_lab", lab_id)
        logger.info(f"Создан StartLabWorker для лабораторной работы {lab_id}")


class GetLabResultWorker(APIWorker):
    """Рабочий поток для получения результата выполнения лабораторной работы"""

    def __init__(self, api_client, result_id: int):
        super().__init__(api_client, "get_lab_result", result_id)
        logger.info(f"Создан GetLabResultWorker для результата {result_id}")


class GetLabResultsWorker(APIWorker):
    """Рабочий поток для получения результатов выполнения лабораторной работы"""

    def __init__(self, api_client, lab_id: int):
        super().__init__(api_client, "get_lab_results", lab_id)
        logger.info(
            f"Создан GetLabResultsWorker для лабораторной работы {lab_id}")


class UpdateLabResultWorker(APIWorker):
    """Рабочий поток для обновления результата выполнения лабораторной работы"""

    def __init__(self, api_client, result_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "update_lab_result", result_id, data)
        logger.info(f"Создан UpdateLabResultWorker для результата {result_id}")


class UpdateTaskResultWorker(APIWorker):
    """Рабочий поток для обновления результата выполнения задания"""

    def __init__(self, api_client, result_id: int, task_result_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "update_task_result", result_id, task_result_id, data)
        logger.info(
            f"Создан UpdateTaskResultWorker для результата задания {task_result_id}")


class CreateLabWorker(APIWorker):
    """Рабочий поток для создания новой лабораторной работы"""

    def __init__(self, api_client, data: Dict[str, Any]):
        super().__init__(api_client, "create_lab", data)
        logger.info("Создан CreateLabWorker")


class UpdateLabWorker(APIWorker):
    """Рабочий поток для обновления лабораторной работы"""

    def __init__(self, api_client, lab_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "update_lab", lab_id, data)
        logger.info(f"Создан UpdateLabWorker для лабораторной работы {lab_id}")


class DeleteLabWorker(APIWorker):
    """Рабочий поток для удаления лабораторной работы"""

    def __init__(self, api_client, lab_id: int):
        super().__init__(api_client, "delete_lab", lab_id)
        logger.info(f"Создан DeleteLabWorker для лабораторной работы {lab_id}")


class CreateTaskWorker(APIWorker):
    """Рабочий поток для создания нового задания для лабораторной работы"""

    def __init__(self, api_client, lab_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "create_task", lab_id, data)
        logger.info(
            f"Создан CreateTaskWorker для лабораторной работы {lab_id}")


class UpdateTaskWorker(APIWorker):
    """Рабочий поток для обновления задания"""

    def __init__(self, api_client, lab_id: int, task_id: int, data: Dict[str, Any]):
        super().__init__(api_client, "update_task", lab_id, task_id, data)
        logger.info(f"Создан UpdateTaskWorker для задания {task_id}")


class DeleteTaskWorker(APIWorker):
    """Рабочий поток для удаления задания"""

    def __init__(self, api_client, lab_id: int, task_id: int):
        super().__init__(api_client, "delete_task", lab_id, task_id)
        logger.info(f"Создан DeleteTaskWorker для задания {task_id}")

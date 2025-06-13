import requests
import json
from typing import Dict, List, Any, Optional
from PySide6.QtCore import QObject, Signal
from core.logger import get_logger


class APIClient(QObject):
    """Клиент для работы с API сервера"""

    # Сигналы для уведомления об ошибках и событиях
    error_occurred = Signal(str)
    connection_status_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.base_url = ""
        self.api_key = ""
        self.token = ""
        self.connected = False

    def configure(self, base_url: str, api_key: str):
        """Настройка клиента API"""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.connected = False

    def set_token(self, token: str):
        """Установка токена авторизации"""
        self.token = token

    def get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов"""
        headers = {"x-api-key": self.api_key}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def check_connection(self) -> bool:
        """Проверка соединения с сервером"""
        try:
            response = requests.get(
                f"{self.base_url}/ping",
                headers=self.get_headers(),
                timeout=5
            )
            self.connected = response.status_code == 200
            self.connection_status_changed.emit(self.connected)
            return self.connected
        except Exception as e:
            self.logger.error(f"Ошибка соединения с сервером: {e}")
            self.connected = False
            self.connection_status_changed.emit(False)
            return False

    def is_connected(self) -> bool:
        """Проверка статуса соединения"""
        return self.connected

    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Вход в систему"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                headers=self.get_headers(),
                json={"username": username, "password": password}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token", "")
                return data
            else:
                error_msg = response.json().get("detail", "Ошибка авторизации")
                self.logger.error(f"Ошибка входа: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при входе: {e}")
            self.error_occurred.emit(str(e))
            return None

    def register(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Регистрация нового пользователя"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                headers=self.get_headers(),
                json=user_data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка регистрации")
                self.logger.error(f"Ошибка регистрации: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при регистрации: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Получение информации о текущем пользователе"""
        try:
            response = requests.get(
                f"{self.base_url}/api/auth/me",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения данных пользователя")
                self.logger.error(
                    f"Ошибка получения данных пользователя: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении данных пользователя: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_devices(self) -> Optional[Dict[str, Any]]:
        """Получение списка устройств"""
        try:
            response = requests.get(
                f"{self.base_url}/api/devices",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения устройств")
                self.logger.error(f"Ошибка получения устройств: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении устройств: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации об устройстве"""
        try:
            response = requests.get(
                f"{self.base_url}/api/devices/{device_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения устройства")
                self.logger.error(
                    f"Ошибка получения устройства {device_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении устройства {device_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def send_device_command(self, device_id: str, command: Dict[str, Any]) -> bool:
        """Отправка команды устройству"""
        try:
            response = requests.post(
                f"{self.base_url}/api/devices/{device_id}/command",
                headers=self.get_headers(),
                json={"command": command}
            )

            if response.status_code == 200:
                return True
            else:
                error_msg = response.json().get("detail", "Ошибка отправки команды")
                self.logger.error(
                    f"Ошибка отправки команды устройству {device_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return False
        except Exception as e:
            self.logger.error(
                f"Ошибка при отправке команды устройству {device_id}: {e}")
            self.error_occurred.emit(str(e))
            return False

    def get_device_history(self, device_id: str, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Получение истории показаний устройства"""
        try:
            response = requests.get(
                f"{self.base_url}/api/devices/{device_id}/history?limit={limit}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения истории")
                self.logger.error(
                    f"Ошибка получения истории устройства {device_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении истории устройства {device_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_device_availability(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о доступности устройства"""
        try:
            response = requests.get(
                f"{self.base_url}/api/booking/devices/{device_id}/availability",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения доступности")
                self.logger.error(
                    f"Ошибка получения доступности устройства {device_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении доступности устройства {device_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_device_queue(self, device_id: str) -> Optional[List[Dict[str, Any]]]:
        """Получение очереди бронирований для устройства"""
        try:
            response = requests.get(
                f"{self.base_url}/api/booking/devices/{device_id}/queue",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения очереди")
                self.logger.error(
                    f"Ошибка получения очереди устройства {device_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении очереди устройства {device_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def book_device(self, device_id: str, start_time: str, end_time: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Бронирование устройства"""
        try:
            response = requests.post(
                f"{self.base_url}/api/booking/devices/{device_id}",
                headers=self.get_headers(),
                json={
                    "start_time": start_time,
                    "end_time": end_time,
                    "purpose": purpose
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка бронирования")
                self.logger.error(
                    f"Ошибка бронирования устройства {device_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при бронировании устройства {device_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_user_bookings(self) -> Optional[List[Dict[str, Any]]]:
        """Получение всех бронирований пользователя"""
        try:
            response = requests.get(
                f"{self.base_url}/api/booking/user/bookings",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения бронирований")
                self.logger.error(
                    f"Ошибка получения бронирований пользователя: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении бронирований пользователя: {e}")
            self.error_occurred.emit(str(e))
            return None

    def cancel_booking(self, booking_id: int) -> bool:
        """Отмена бронирования"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/booking/{booking_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return True
            else:
                error_msg = response.json().get("detail", "Ошибка отмены бронирования")
                self.logger.error(
                    f"Ошибка отмены бронирования {booking_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return False
        except Exception as e:
            self.logger.error(
                f"Ошибка при отмене бронирования {booking_id}: {e}")
            self.error_occurred.emit(str(e))
            return False

    def get_labs(self) -> Optional[List[Dict[str, Any]]]:
        """Получение списка лабораторных работ"""
        try:
            response = requests.get(
                f"{self.base_url}/api/labs",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения лабораторных работ")
                self.logger.error(
                    f"Ошибка получения лабораторных работ: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении лабораторных работ: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_lab(self, lab_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о лабораторной работе"""
        try:
            response = requests.get(
                f"{self.base_url}/api/labs/{lab_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения лабораторной работы")
                self.logger.error(
                    f"Ошибка получения лабораторной работы {lab_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении лабораторной работы {lab_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def start_lab(self, lab_id: int) -> Optional[Dict[str, Any]]:
        """Начало выполнения лабораторной работы"""
        try:
            response = requests.post(
                f"{self.base_url}/api/labs/{lab_id}/start",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get(
                    "detail", "Ошибка начала выполнения лабораторной работы")
                self.logger.error(
                    f"Ошибка начала выполнения лабораторной работы {lab_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при начале выполнения лабораторной работы {lab_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_lab_result(self, result_id: int) -> Optional[Dict[str, Any]]:
        """Получение результата выполнения лабораторной работы"""
        try:
            response = requests.get(
                f"{self.base_url}/api/labs/results/{result_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения результата")
                self.logger.error(
                    f"Ошибка получения результата {result_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении результата {result_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def update_lab_result(self, result_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновление результата выполнения лабораторной работы"""
        try:
            response = requests.put(
                f"{self.base_url}/api/labs/results/{result_id}",
                headers=self.get_headers(),
                json=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка обновления результата")
                self.logger.error(
                    f"Ошибка обновления результата {result_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при обновлении результата {result_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def update_task_result(self, result_id: int, task_result_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновление результата выполнения задания"""
        try:
            response = requests.put(
                f"{self.base_url}/api/labs/results/{result_id}/tasks/{task_result_id}",
                headers=self.get_headers(),
                json=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка обновления результата задания")
                self.logger.error(
                    f"Ошибка обновления результата задания {task_result_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при обновлении результата задания {task_result_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_user_lab_results(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Получение результатов выполнения лабораторных работ пользователя"""
        try:
            response = requests.get(
                f"{self.base_url}/api/labs/user/{user_id}/results",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения результатов")
                self.logger.error(
                    f"Ошибка получения результатов пользователя {user_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении результатов пользователя {user_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_lab_results(self, lab_id: int) -> Optional[List[Dict[str, Any]]]:
        """Получение результатов выполнения лабораторной работы"""
        try:
            response = requests.get(
                f"{self.base_url}/api/labs/{lab_id}/results",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения результатов")
                self.logger.error(
                    f"Ошибка получения результатов лабораторной работы {lab_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении результатов лабораторной работы {lab_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def create_lab(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Создание новой лабораторной работы"""
        try:
            response = requests.post(
                f"{self.base_url}/api/labs",
                headers=self.get_headers(),
                json=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка создания лабораторной работы")
                self.logger.error(
                    f"Ошибка создания лабораторной работы: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при создании лабораторной работы: {e}")
            self.error_occurred.emit(str(e))
            return None

    def update_lab(self, lab_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновление лабораторной работы"""
        try:
            response = requests.put(
                f"{self.base_url}/api/labs/{lab_id}",
                headers=self.get_headers(),
                json=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка обновления лабораторной работы")
                self.logger.error(
                    f"Ошибка обновления лабораторной работы {lab_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при обновлении лабораторной работы {lab_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def delete_lab(self, lab_id: int) -> bool:
        """Удаление лабораторной работы"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/labs/{lab_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return True
            else:
                error_msg = response.json().get("detail", "Ошибка удаления лабораторной работы")
                self.logger.error(
                    f"Ошибка удаления лабораторной работы {lab_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return False
        except Exception as e:
            self.logger.error(
                f"Ошибка при удалении лабораторной работы {lab_id}: {e}")
            self.error_occurred.emit(str(e))
            return False

    def create_task(self, lab_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Создание нового задания для лабораторной работы"""
        try:
            response = requests.post(
                f"{self.base_url}/api/labs/{lab_id}/tasks",
                headers=self.get_headers(),
                json=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка создания задания")
                self.logger.error(
                    f"Ошибка создания задания для лабораторной работы {lab_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при создании задания для лабораторной работы {lab_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def update_task(self, lab_id: int, task_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновление задания"""
        try:
            response = requests.put(
                f"{self.base_url}/api/labs/{lab_id}/tasks/{task_id}",
                headers=self.get_headers(),
                json=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка обновления задания")
                self.logger.error(
                    f"Ошибка обновления задания {task_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении задания {task_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def delete_task(self, lab_id: int, task_id: int) -> bool:
        """Удаление задания"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/labs/{lab_id}/tasks/{task_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return True
            else:
                error_msg = response.json().get("detail", "Ошибка удаления задания")
                self.logger.error(
                    f"Ошибка удаления задания {task_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return False
        except Exception as e:
            self.logger.error(f"Ошибка при удалении задания {task_id}: {e}")
            self.error_occurred.emit(str(e))
            return False

    def get_users(self) -> Optional[List[Dict[str, Any]]]:
        """Получение списка пользователей"""
        try:
            response = requests.get(
                f"{self.base_url}/api/users",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения пользователей")
                self.logger.error(
                    f"Ошибка получения пользователей: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении пользователей: {e}")
            self.error_occurred.emit(str(e))
            return None

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе"""
        try:
            response = requests.get(
                f"{self.base_url}/api/users/{user_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка получения пользователя")
                self.logger.error(
                    f"Ошибка получения пользователя {user_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при получении пользователя {user_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def create_user(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Создание нового пользователя"""
        try:
            response = requests.post(
                f"{self.base_url}/api/users",
                headers=self.get_headers(),
                json=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка создания пользователя")
                self.logger.error(f"Ошибка создания пользователя: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(f"Ошибка при создании пользователя: {e}")
            self.error_occurred.emit(str(e))
            return None

    def update_user(self, user_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновление пользователя"""
        try:
            response = requests.put(
                f"{self.base_url}/api/users/{user_id}",
                headers=self.get_headers(),
                json=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.json().get("detail", "Ошибка обновления пользователя")
                self.logger.error(
                    f"Ошибка обновления пользователя {user_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return None
        except Exception as e:
            self.logger.error(
                f"Ошибка при обновлении пользователя {user_id}: {e}")
            self.error_occurred.emit(str(e))
            return None

    def delete_user(self, user_id: int) -> bool:
        """Удаление пользователя"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/users/{user_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                return True
            else:
                error_msg = response.json().get("detail", "Ошибка удаления пользователя")
                self.logger.error(
                    f"Ошибка удаления пользователя {user_id}: {error_msg}")
                self.error_occurred.emit(error_msg)
                return False
        except Exception as e:
            self.logger.error(
                f"Ошибка при удалении пользователя {user_id}: {e}")
            self.error_occurred.emit(str(e))
            return False

    def get_websocket_url(self) -> str:
        """Получение URL для WebSocket соединения"""
        # Заменяем http на ws или https на wss
        if self.base_url.startswith("https://"):
            ws_url = self.base_url.replace("https://", "wss://")
        else:
            ws_url = self.base_url.replace("http://", "ws://")

        return f"{ws_url}/ws?token={self.token}"

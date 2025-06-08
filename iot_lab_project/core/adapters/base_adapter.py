from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseAdapter(ABC):
    """
    Базовый интерфейс для адаптеров подключения (HA, Custom API и др.)
    """

    def __init__(self):
        self.connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Попытка соединения"""
        pass

    @abstractmethod
    def get_devices_by_category(self) -> Dict[str, List[Dict]]:
        """Вернуть устройства, разбитые по категориям"""
        pass

    @abstractmethod
    def get_device_details(self, device_id: str) -> Dict:
        """Получить подробную информацию об устройстве по его ID"""
        pass

    @abstractmethod
    def send_command(self, device_id: str, command: Dict) -> bool:
        """Отправить команду устройству, если доступно"""
        pass

    @abstractmethod
    def get_connection_name(self) -> str:
        """Возвращает название подключения для отображения"""
        pass

    def is_connected(self) -> bool:
        return self.connected

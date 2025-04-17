from PySide6.QtCore import QThread, Signal
from utils.logger import Logger

class DeviceLoader(QThread):
    """Поток для загрузки устройств"""

    devices_loaded = Signal(dict)
    error = Signal(str)

    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self.logger = Logger()

    def run(self):
        try:
            self.logger.info("Запрос устройств через DeviceManager...")
            
            # Теперь get_categorized_devices требует callback
            self.device_manager.get_categorized_devices(callback=self._on_devices_loaded)

        except Exception as e:
            self.logger.error(f"Ошибка запуска потока загрузки устройств: {e}")
            self.error.emit(str(e))

    def _on_devices_loaded(self, categorized_devices: dict):
        """Обработка загруженных устройств"""
        self.logger.success("Устройства успешно загружены в потоке.")
        self.devices_loaded.emit(categorized_devices)
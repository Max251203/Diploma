from PySide6.QtCore import Signal
from core.workers.base_worker import BaseWorker


class DeviceLoader(BaseWorker):
    devices_loaded = Signal(dict)

    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager

    def run(self):
        self.run_safe(self._task)

    def _task(self):
        self.logger.info("Запрос устройств через DeviceManager...")
        self.device_manager.get_categorized_devices(
            callback=self._on_devices_loaded)

    def _on_devices_loaded(self, categorized: dict):
        self.logger.success("Устройства успешно загружены.")
        self.devices_loaded.emit(categorized)

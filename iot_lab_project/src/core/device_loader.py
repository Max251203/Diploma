from PySide6.QtCore import QThread, Signal
from core.device_manager import DeviceManager


class DeviceLoader(QThread):
    devices_loaded = Signal(dict)
    error = Signal(str)

    def __init__(self, device_manager: DeviceManager):
        super().__init__()
        self.device_manager = device_manager

    def run(self):
        try:
            categorized = self.device_manager.get_categorized_devices()
            self.devices_loaded.emit(categorized)
        except Exception as e:
            self.error.emit(str(e))
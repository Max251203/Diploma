from PySide6.QtCore import QThread, Signal

class DeviceLoader(QThread):
    """Поток для загрузки устройств"""
    devices_loaded = Signal(dict)
    error = Signal(str)
    
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
    
    def run(self):
        try:
            # Получаем устройства по категориям
            categorized = self.device_manager.get_categorized_devices()
            self.devices_loaded.emit(categorized)
        except Exception as e:
            self.error.emit(str(e))
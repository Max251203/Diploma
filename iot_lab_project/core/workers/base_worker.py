from PySide6.QtCore import QThread, Signal
from core.logger import get_logger


class BaseWorker(QThread):
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.logger = get_logger()

    def run_safe(self, task_func):
        """Безопасный запуск с логированием и обработкой ошибок"""
        try:
            task_func()
        except Exception as e:
            self.logger.error(f"[Worker] Ошибка: {e}")
            self.error.emit(str(e))

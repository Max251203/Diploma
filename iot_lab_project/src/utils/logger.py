# В файле src/utils/logger.py
import logging
from datetime import datetime

class Logger:
    """Класс для логирования событий приложения"""
    
    def __init__(self, log_level=logging.INFO, console_output=False):
        # Настройка логгера
        self.logger = logging.getLogger("IoTLab")
        self.logger.setLevel(log_level)
        
        # Очищаем все обработчики
        self.logger.handlers = []
        
        # Создаем обработчик для консоли если нужно
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            
            # Создаем форматтер
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            
            # Добавляем обработчик к логгеру
            self.logger.addHandler(console_handler)
        
        # Текстовый лог для UI
        self.text_log = []
    
    def info(self, message):
        """Логирует информационное сообщение"""
        self.logger.info(message)
        self._add_to_text_log("ℹ️", message)
    
    def warning(self, message):
        """Логирует предупреждение"""
        self.logger.warning(message)
        self._add_to_text_log("⚠️", message)
    
    def error(self, message):
        """Логирует ошибку"""
        self.logger.error(message)
        self._add_to_text_log("❌", message)
    
    def success(self, message):
        """Логирует успешное событие"""
        self.logger.info(f"SUCCESS: {message}")
        self._add_to_text_log("✅", message)
    
    def _add_to_text_log(self, icon, message):
        """Добавляет сообщение в текстовый лог с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_log.append(f"[{timestamp}] {icon} {message}")
    
    def get_text_log(self):
        """Возвращает текстовый лог для отображения в UI"""
        return "\n".join(self.text_log)
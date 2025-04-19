from datetime import datetime

class Logger:
    """Singleton логгер для UI"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._init_internal()
        return cls._instance

    def _init_internal(self):
        self.text_log = []

    def info(self, message: str):
        self._add_to_text_log("info", message)

    def warning(self, message: str):
        self._add_to_text_log("warning", message)

    def error(self, message: str):
        self._add_to_text_log("error", message)

    def success(self, message: str):
        self._add_to_text_log("success", message)

    def _add_to_text_log(self, icon_name: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon_path = f":/icon/icons/{icon_name}.png"
        # выравнивание по центру, перенос строки
        icon_html = f'<img src="{icon_path}" width="16" height="16" style="vertical-align:middle;">'
        self.text_log.append(f"[{timestamp}] {icon_html} {message}<br/>")

    def get_text_log(self) -> str:
        return "".join(self.text_log)


def get_logger() -> Logger:
    return Logger()    
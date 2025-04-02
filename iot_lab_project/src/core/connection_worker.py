from PySide6.QtCore import QThread, Signal
from core.ws_client import HomeAssistantWSClient
from core.entity_manager import EntityManager
from core.device_manager import DeviceManager
from urllib.parse import urlparse


class ConnectionWorker(QThread):
    connection_success = Signal(object, object, object, str)  # ws_client, entity_manager, device_manager, ws_url
    connection_failed = Signal(str)

    def __init__(self, raw_url: str, token: str):
        super().__init__()
        self.raw_url = raw_url
        self.token = token

    def run(self):
        try:
            ws_url = self._format_websocket_url(self.raw_url)

            ws_client = HomeAssistantWSClient(ws_url, self.token)
            entity_manager = EntityManager(ws_client)
            device_manager = DeviceManager(ws_client, entity_manager)

            # Проверим подключение
            device_manager.get_physical_devices()

            self.connection_success.emit(ws_client, entity_manager, device_manager, ws_url)

        except Exception as e:
            self.connection_failed.emit(str(e))

    def _format_websocket_url(self, raw_url: str) -> str:
        parsed = urlparse(raw_url)
        scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        netloc = parsed.netloc or parsed.path
        return f"{scheme}://{netloc}/api/websocket"
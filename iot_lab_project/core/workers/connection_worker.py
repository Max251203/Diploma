from PySide6.QtCore import Signal
from urllib.parse import urlparse
from core.workers.base_worker import BaseWorker
from core.ha.ws_client import HomeAssistantWSClient
from core.ha.rest_client import HomeAssistantRestClient
from core.ha.entity_manager import EntityManager
from core.ha.device_manager import DeviceManager

class ConnectionWorker(BaseWorker):
    connection_success = Signal(object, object, object, object, str)  # ws, rest, entity, device, url
    connection_failed = Signal(str)
    state_changed = Signal(str, dict)

    def __init__(self, raw_url: str, token: str):
        super().__init__()
        self.raw_url = raw_url
        self.token = token

    def run(self):
        self.run_safe(self._task)

    def _task(self):
        self.logger.info("Инициализация подключения...")

        ws_url = self._format_websocket_url(self.raw_url)
        rest_url = self._format_rest_url(self.raw_url)
        ws_client = HomeAssistantWSClient.init(ws_url, self.token)

        for _ in range(10):
            if ws_client.is_connected():
                break
            self.msleep(500)
        else:
            self.logger.error("WebSocket не подключен.")
            self.connection_failed.emit("Не удалось установить соединение с WebSocket.")
            return

        rest_client = HomeAssistantRestClient(rest_url, self.token)
        entity_manager = EntityManager(ws_client, rest_client)
        device_manager = DeviceManager(ws_client, entity_manager)

        def on_devices_loaded(devices):
            self.logger.success("Подключение и загрузка устройств успешны.")

            def on_state_changed(event):
                new_state = event.get("data", {}).get("new_state")
                if not new_state:
                    return
                entity_id = new_state.get("entity_id")
                self.logger.info(f"[LIVE] {entity_id} → {new_state.get('state')}")
                self.state_changed.emit(entity_id, new_state)

            ws_client.subscribe_event("state_changed", on_state_changed)
            self.connection_success.emit(ws_client, rest_client, entity_manager, device_manager, ws_url)

        ws_client.send_command("config/device_registry/list", callback=on_devices_loaded)

    def _format_websocket_url(self, raw_url: str) -> str:
        parsed = urlparse(raw_url)
        scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        netloc = parsed.netloc or parsed.path
        return f"{scheme}://{netloc}/api/websocket"

    def _format_rest_url(self, raw_url: str) -> str:
        parsed = urlparse(raw_url)
        scheme = parsed.scheme or 'http'
        netloc = parsed.netloc or parsed.path
        return f"{scheme}://{netloc}"
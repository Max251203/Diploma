from PySide6.QtCore import Signal
from core.workers.base_worker import BaseWorker
from core.ha.ws_client import HomeAssistantWSClient
from core.ha.rest_client import HomeAssistantRestClient
from core.ha.entity_manager import EntityManager
from core.ha.device_manager import DeviceManager


class ConnectionWorker(BaseWorker):
    # ws, rest, entity, device, url
    connection_success = Signal(object, object, object, object, str)
    connection_failed = Signal(str)
    state_changed = Signal(str, dict)

    def __init__(self, raw_url: str, token: str):
        super().__init__()
        self.raw_url = raw_url
        self.token = token
        self._abort = False

    def quit(self):
        self._abort = True
        super().quit()

    def run(self):
        if self._abort:
            return
        self.run_safe(self._task)

    def _task(self):
        self.logger.info("Инициализация подключения...")

        from urllib.parse import urlparse

        def _ws_url(raw_url: str) -> str:
            parsed = urlparse(raw_url)
            scheme = 'wss' if parsed.scheme == 'https' else 'ws'
            return f"{scheme}://{parsed.netloc or parsed.path}/api/websocket"

        def _rest_url(raw_url: str) -> str:
            parsed = urlparse(raw_url)
            return f"{parsed.scheme or 'http'}://{parsed.netloc or parsed.path}"

        ws_url = _ws_url(self.raw_url)
        rest_url = _rest_url(self.raw_url)
        ws_client = HomeAssistantWSClient.init(ws_url, self.token)

        for _ in range(15):
            if self._abort:
                return
            if ws_client.is_connected():
                break
            self.msleep(300)
        else:
            self.connection_failed.emit("Не удалось подключиться к WebSocket.")
            return

        rest_client = HomeAssistantRestClient(rest_url, self.token)
        entity_manager = EntityManager(ws_client, rest_client)
        device_manager = DeviceManager(ws_client, entity_manager)

        def on_state_change(event):
            new_state = event.get("data", {}).get("new_state")
            if new_state:
                entity_id = new_state.get("entity_id")
                self.logger.info(f"[HA] Обновление: {entity_id}")
                self.state_changed.emit(entity_id, new_state)

        ws_client.subscribe_event("state_changed", on_state_change)
        self.connection_success.emit(
            ws_client, rest_client, entity_manager, device_manager, ws_url)

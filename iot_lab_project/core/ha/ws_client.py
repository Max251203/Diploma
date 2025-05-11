import asyncio, json, websockets, threading
from typing import Callable, Dict, Any, Optional
from core.logger import get_logger

text_logger = get_logger()

class HomeAssistantWSClient:
    _instance = None

    @staticmethod
    def get_instance() -> 'HomeAssistantWSClient':
        if HomeAssistantWSClient._instance is None:
            raise RuntimeError("WS клиент не инициализирован. Вызови init() сначала.")
        return HomeAssistantWSClient._instance

    @staticmethod
    def init(url: str, token: str) -> 'HomeAssistantWSClient':
        if HomeAssistantWSClient._instance is None:
            HomeAssistantWSClient._instance = HomeAssistantWSClient(url, token)
        return HomeAssistantWSClient._instance

    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self._ws = None
        self._id_counter = 1
        self._pending: Dict[int, Callable[[Any], None]] = {}
        self._events: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self._loop = asyncio.new_event_loop()
        self._connected = False
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()

    def _start_loop(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect())
            self._loop.run_forever()
        except Exception as e:
            text_logger.error(f"[WS] Ошибка в loop: {e}")

    async def _connect(self):
        try:
            text_logger.info(f"[WS] Подключение к {self.url}")
            self._ws = await websockets.connect(self.url)
            await self._authorize()
            self._connected = True
            asyncio.create_task(self._listen())
            text_logger.success("[WS] Соединение установлено")
        except Exception as e:
            self._connected = False
            text_logger.error(f"[WS] Ошибка подключения: {e}")

    async def _authorize(self):
        try:
            await self._ws.recv()
            await self._ws.send(json.dumps({"type": "auth", "access_token": self.token}))
            await self._ws.recv()
            text_logger.success("[WS] Авторизация прошла успешно")
        except Exception as e:
            text_logger.error(f"[WS] Ошибка авторизации: {e}")
            raise

    async def _listen(self):
        while self._connected:
            try:
                msg = await self._ws.recv()
                data = json.loads(msg)

                if data.get("type") == "result" and "id" in data:
                    cb = self._pending.pop(data["id"], None)
                    if cb:
                        cb(data.get("result"))

                elif data.get("type") == "event":
                    event_type = data["event"].get("event_type")
                    handler = self._events.get(event_type)
                    if handler:
                        handler(data["event"])

            except Exception as e:
                self._connected = False
                text_logger.error(f"[WS] Ошибка прослушивания: {e}")
                break

    def send_command(self, command_type: str, payload: Optional[Dict] = None,
                     callback: Optional[Callable[[Any], None]] = None):
        if not self._connected or not self._ws:
            text_logger.warning("[WS] Попытка отправки команды без соединения.")
            return

        asyncio.run_coroutine_threadsafe(
            self._send(command_type, payload, callback),
            self._loop
        )

    async def _send(self, command_type: str, payload: Optional[Dict],
                    callback: Optional[Callable[[Any], None]]):
        msg_id = self._id_counter
        self._id_counter += 1
        msg = {"id": msg_id, "type": command_type}
        if payload:
            msg.update(payload)
        if callback:
            self._pending[msg_id] = callback
        try:
            await self._ws.send(json.dumps(msg))
        except Exception as e:
            text_logger.error(f"[WS] Ошибка отправки: {e}")
            self._pending.pop(msg_id, None)

    def subscribe_event(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        self._events[event_type] = handler
        self.send_command("subscribe_events", {"event_type": event_type})

    def is_connected(self) -> bool:
        return self._connected and self._ws is not None
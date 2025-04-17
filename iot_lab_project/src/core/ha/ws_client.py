import asyncio
import json
import websockets
import threading
from typing import Callable, Dict, Any, Optional
from utils.logger import Logger

_log = Logger()
logger = _log.logger
text_logger = _log

class HomeAssistantWSClient:
    """Singleton WebSocket-клиент для Home Assistant."""

    _instance = None

    @staticmethod
    def get_instance() -> 'HomeAssistantWSClient':
        if HomeAssistantWSClient._instance is None:
            raise RuntimeError("HomeAssistantWSClient не инициализирован. Вызови init() сначала.")
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
        self._pending_commands: Dict[int, Callable[[Any], None]] = {}
        self._event_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}

        self._loop = asyncio.new_event_loop()
        self._running = True
        self._connected = False

        # Запуск asyncio loop в отдельном потоке
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()

    def _start_loop(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._run())
            self._loop.run_forever()
        except Exception as e:
            text_logger.error(f"[WS] Ошибка в loop: {e}")

    async def _run(self):
        try:
            text_logger.info(f"[WS] Подключение к {self.url}")
            self._ws = await websockets.connect(self.url)
            await self._authorize()
            self._connected = True
            asyncio.create_task(self._listen())
            text_logger.success("[WS] Установлено соединение с Home Assistant")
        except Exception as e:
            self._connected = False
            text_logger.error(f"[WS] Ошибка подключения: {e}")

    async def _authorize(self):
        try:
            auth_required = await self._ws.recv()
            text_logger.info("[WS] Получен auth_required")
            await self._ws.send(json.dumps({
                "type": "auth",
                "access_token": self.token
            }))
            auth_ok = await self._ws.recv()
            text_logger.success("[WS] Авторизация прошла успешно")
        except Exception as e:
            text_logger.error(f"[WS] Ошибка авторизации: {e}")
            raise

    async def _listen(self):
        while self._running:
            try:
                msg = await self._ws.recv()
                data = json.loads(msg)

                # Ответ на команду
                if data.get("type") == "result" and "id" in data:
                    callback = self._pending_commands.pop(data["id"], None)
                    if callback:
                        callback(data.get("result"))

                # Событие
                elif data.get("type") == "event":
                    event_type = data["event"].get("event_type")
                    handler = self._event_handlers.get(event_type)
                    if handler:
                        handler(data["event"])

            except Exception as e:
                self._connected = False
                text_logger.error(f"[WS] Ошибка прослушивания: {e}")
                break

    def send_command(self, command_type: str, payload: Optional[Dict] = None,
                     callback: Optional[Callable[[Any], None]] = None):
        """Отправляет команду (через event loop в фоне)"""
        if not self._connected or not self._ws:
            text_logger.warning("[WS] Попытка отправки команды до установления соединения.")
            return

        asyncio.run_coroutine_threadsafe(
            self._send_and_register(command_type, payload, callback),
            self._loop
        )

    async def _send_and_register(self, command_type: str, payload: Optional[Dict],
                                 callback: Optional[Callable[[Any], None]]):
        msg_id = self._id_counter
        self._id_counter += 1
        message = {
            "id": msg_id,
            "type": command_type
        }
        if payload:
            message.update(payload)
        if callback:
            self._pending_commands[msg_id] = callback
        try:
            await self._ws.send(json.dumps(message))
        except Exception as e:
            text_logger.error(f"[WS] Ошибка при отправке команды: {e}")
            if msg_id in self._pending_commands:
                del self._pending_commands[msg_id]

    def subscribe_event(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Подписка на событие (например, state_changed)"""
        self._event_handlers[event_type] = handler
        self.send_command("subscribe_events", {"event_type": event_type})

    def is_connected(self) -> bool:
        return self._connected and self._ws is not None
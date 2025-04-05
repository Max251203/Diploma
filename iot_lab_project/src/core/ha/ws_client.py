import asyncio
import json
import websockets

class HomeAssistantWSClient:
    """WebSocket клиент для взаимодействия с Home Assistant"""
    
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self._id = 1
    
    def send_command(self, command_type, extra_payload=None):
        """Отправляет команду на сервер и возвращает результат"""
        return asyncio.run(self._send_and_receive(command_type, extra_payload or {}))
    
    async def _send_and_receive(self, command_type, extra_payload):
        """Асинхронно отправляет команду и получает ответ"""
        async with websockets.connect(self.url) as ws:
            # Авторизация
            await ws.recv()  # auth_required
            await ws.send(json.dumps({
                "type": "auth",
                "access_token": self.token
            }))
            await ws.recv()  # auth_ok
            
            # Формируем ID сообщения
            msg_id = self._id
            self._id += 1
            
            # Формируем и отправляем сообщение
            payload = {
                "id": msg_id,
                "type": command_type,
                **extra_payload
            }
            await ws.send(json.dumps(payload))
            
            # Ждем ответа с нужным ID
            while True:
                response = await ws.recv()
                data = json.loads(response)
                if data.get("id") == msg_id and data.get("type") == "result":
                    return data.get("result", [])
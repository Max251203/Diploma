import asyncio
import json
import websockets


class HomeAssistantWSClient:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.connection = None
        self._id = 1

    def send_command(self, command_type: str, extra_payload: dict = None):
        return asyncio.run(self._send_and_receive(command_type, extra_payload or {}))

    async def _send_and_receive(self, command_type: str, extra_payload: dict):
        async with websockets.connect(self.url) as ws:
            await ws.recv()  # auth_required
            await ws.send(json.dumps({
                "type": "auth",
                "access_token": self.token
            }))
            await ws.recv()  # auth_ok

            msg_id = self._id
            self._id += 1

            payload = {
                "id": msg_id,
                "type": command_type,
                **extra_payload
            }

            await ws.send(json.dumps(payload))

            while True:
                response = await ws.recv()
                data = json.loads(response)
                if data.get("id") == msg_id and data.get("type") == "result":
                    return data.get("result", [])
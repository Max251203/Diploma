import json
from typing import Dict, List, Any, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        # Активные соединения
        self.active_connections: List[WebSocket] = []
        # Соединения, сгруппированные по пользователям
        self.user_connections: Dict[int, List[WebSocket]] = {}
        # Соединения, сгруппированные по ролям
        self.role_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, role: str):
        """Подключение нового клиента"""
        await websocket.accept()
        self.active_connections.append(websocket)

        # Добавляем соединение в группу пользователя
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

        # Добавляем соединение в группу роли
        if role not in self.role_connections:
            self.role_connections[role] = []
        self.role_connections[role].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int, role: str):
        """Отключение клиента"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Удаляем соединение из группы пользователя
        if user_id in self.user_connections and websocket in self.user_connections[user_id]:
            self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Удаляем соединение из группы роли
        if role in self.role_connections and websocket in self.role_connections[role]:
            self.role_connections[role].remove(websocket)
            if not self.role_connections[role]:
                del self.role_connections[role]

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Отправка сообщения конкретному клиенту"""
        message["timestamp"] = datetime.now().isoformat()
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        """Отправка сообщения всем подключенным клиентам"""
        message["timestamp"] = datetime.now().isoformat()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def broadcast_to_user(self, user_id: int, message: Dict[str, Any]):
        """Отправка сообщения всем соединениям конкретного пользователя"""
        if user_id not in self.user_connections:
            return

        message["timestamp"] = datetime.now().isoformat()
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def broadcast_to_role(self, role: str, message: Dict[str, Any]):
        """Отправка сообщения всем пользователям с определенной ролью"""
        if role not in self.role_connections:
            return

        message["timestamp"] = datetime.now().isoformat()
        for connection in self.role_connections[role]:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def broadcast_device_update(self, device_id: str, state: Dict[str, Any]):
        """Отправка обновления состояния устройства всем клиентам"""
        message = {
            "type": "device_update",
            "device_id": device_id,
            "state": state,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)

    async def broadcast_lab_update(self, lab_id: int, action: str, data: Dict[str, Any]):
        """Отправка обновления лабораторной работы"""
        message = {
            "type": "lab_update",
            "lab_id": lab_id,
            "action": action,  # "created", "updated", "deleted"
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)

    async def broadcast_lab_result_update(self, result_id: int, user_id: int, action: str, data: Dict[str, Any]):
        """Отправка обновления результата лабораторной работы"""
        message = {
            "type": "lab_result_update",
            "result_id": result_id,
            "action": action,  # "submitted", "reviewed"
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        # Отправляем владельцу результата
        await self.broadcast_to_user(user_id, message)

        # Отправляем преподавателям и администраторам
        await self.broadcast_to_role("teacher", message)
        await self.broadcast_to_role("admin", message)

    async def broadcast_notification(self, user_id: int, title: str, message: str, level: str = "info"):
        """Отправка уведомления пользователю"""
        notification = {
            "type": "notification",
            "title": title,
            "message": message,
            "level": level,  # "info", "warning", "error", "success"
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_user(user_id, notification)

    async def broadcast_system_notification(self, title: str, message: str, level: str = "info", roles: List[str] = None):
        """Отправка системного уведомления всем или определенным ролям"""
        notification = {
            "type": "notification",
            "title": title,
            "message": message,
            "level": level,  # "info", "warning", "error", "success"
            "timestamp": datetime.now().isoformat()
        }

        if roles:
            for role in roles:
                await self.broadcast_to_role(role, notification)
        else:
            await self.broadcast(notification)

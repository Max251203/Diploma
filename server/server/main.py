import time
import webbrowser
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from threading import Thread

from config import API_HOST, API_PORT, LOCAL_IP, API_KEY, logger
import database
from routers import api_router
from services.mqtt_client import MQTTClient
from services.websocket import ConnectionManager
from utils.security import get_current_user

# Инициализация базы данных
database.init_db()

# Инициализация FastAPI
app = FastAPI(
    title="IoT Lab API",
    description="API для взаимодействия с IoT устройствами и управления лабораторными работами",
    version="1.0.0"
)

# Добавление CORS - разрешаем запросы с любых источников
app.add_middleware(
    CORSMiddleware,
    # Разрешаем все источники для доступа из локальной сети
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация менеджера WebSocket соединений
ws_manager = ConnectionManager()

# Подключение роутеров
app.include_router(api_router)

# Проверка статуса сервера


@app.get("/ping")
async def ping():
    """Простой endpoint для проверки доступности сервера"""
    return {"message": "pong"}

# Получение API ключа


@app.get("/api/key")
async def get_api_key():
    """Получить текущий API ключ (только для локального использования)"""
    return {"api_key": API_KEY, "note": "Храните этот ключ в безопасности и используйте для всех API запросов"}

# WebSocket для обновлений в реальном времени


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для получения обновлений в реальном времени"""
    # Получаем токен из параметров запроса
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return

    try:
        # Проверяем токен и получаем пользователя
        user = await get_current_user(token)

        # Подключаем WebSocket
        await ws_manager.connect(websocket, user["id"], user["role"])

        # Отправляем приветственное сообщение
        await ws_manager.send_personal_message(
            {
                "type": "connection_established",
                "message": "Соединение установлено",
                "user_id": user["id"],
                "role": user["role"]
            },
            websocket
        )

        try:
            # Ожидаем сообщения от клиента
            while True:
                data = await websocket.receive_json()
                # Обрабатываем сообщения от клиента
                if data.get("type") == "ping":
                    await ws_manager.send_personal_message({"type": "pong"}, websocket)
        except WebSocketDisconnect:
            # Отключаем WebSocket при разрыве соединения
            ws_manager.disconnect(websocket, user["id"], user["role"])
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid token")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")

# Функция для открытия браузера с документацией API


def open_api_docs():
    # Используем localhost вместо 0.0.0.0 для открытия в браузере
    url = f"http://localhost:{API_PORT}/docs"
    webbrowser.open(url)
    logger.info(f"Открыт браузер с документацией API: {url}")

# Основная функция


def main():
    # Вывод информации о доступе к API
    logger.info(f"API ключ: {API_KEY}")
    logger.info(f"API доступен по адресу: http://{LOCAL_IP}:{API_PORT}")
    logger.info(f"Документация API: http://{LOCAL_IP}:{API_PORT}/docs")
    logger.info(
        f"Для доступа к API с других устройств используйте заголовок 'X-API-Key: {API_KEY}'")

    # Запуск MQTT клиента в отдельном потоке
    mqtt_client = MQTTClient()
    mqtt_thread = mqtt_client.start()

    # Запускаем отдельный поток для открытия браузера после запуска сервера
    # Задержка в 2 секунды, чтобы сервер успел запуститься
    browser_thread = Thread(target=lambda: (time.sleep(2), open_api_docs()))
    browser_thread.daemon = True
    browser_thread.start()

    # Запуск FastAPI сервера
    logger.info(f"Запуск сервера на {API_HOST}:{API_PORT}")
    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    main()

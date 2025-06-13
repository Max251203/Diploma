import time
import webbrowser
import uvicorn
import subprocess
import os
import signal
import atexit
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from threading import Thread

from config import API_HOST, API_PORT, LOCAL_IP, API_KEY, logger
import database
from routers import api_router
from services.mqtt_client import MQTTClient
from services.websocket.ws_manager import ws_manager
from utils.security import get_current_user

# Пути к исполняемым файлам - укажите правильные пути для вашей системы
MOSQUITTO_PATH = r"C:\Program Files\mosquitto\mosquitto.exe"
ZIGBEE2MQTT_PATH = r"C:\zigbee2mqtt"

# Глобальные переменные для процессов
mosquitto_process = None
zigbee2mqtt_process = None


def start_mosquitto():
    """Запуск MQTT брокера Mosquitto"""
    global mosquitto_process
    logger.info("Запуск MQTT брокера Mosquitto...")

    # Проверяем существование файла
    if not os.path.exists(MOSQUITTO_PATH):
        logger.error(f"Mosquitto не найден по пути {MOSQUITTO_PATH}")
        return False

    try:
        mosquitto_process = subprocess.Popen([MOSQUITTO_PATH, "-v"],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
        logger.info("MQTT брокер Mosquitto запущен")
        return True
    except Exception as e:
        logger.error(f"Ошибка запуска Mosquitto: {e}")
        return False


def start_zigbee2mqtt():
    """Запуск Zigbee2MQTT"""
    global zigbee2mqtt_process
    logger.info("Запуск Zigbee2MQTT...")

    # Проверяем существование директории
    if not os.path.exists(ZIGBEE2MQTT_PATH):
        logger.error(
            f"Директория Zigbee2MQTT не найдена по пути {ZIGBEE2MQTT_PATH}")
        return False

    try:
        # Сохраняем текущую директорию
        current_dir = os.getcwd()

        # Переходим в директорию Zigbee2MQTT
        os.chdir(ZIGBEE2MQTT_PATH)

        # Запускаем Zigbee2MQTT через npm start или напрямую через node
        if os.path.exists(os.path.join(ZIGBEE2MQTT_PATH, "index.js")):
            zigbee2mqtt_process = subprocess.Popen(["node", "index.js"],
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE)
        else:
            zigbee2mqtt_process = subprocess.Popen(["npm", "start"],
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE)

        # Возвращаемся в исходную директорию
        os.chdir(current_dir)

        logger.info("Zigbee2MQTT запущен")
        return True
    except Exception as e:
        # Возвращаемся в исходную директорию в случае ошибки
        if 'current_dir' in locals():
            os.chdir(current_dir)

        logger.error(f"Ошибка запуска Zigbee2MQTT: {e}")
        return False


def stop_all_processes():
    """Остановка всех процессов при завершении работы сервера"""
    # Останавливаем Zigbee2MQTT
    if zigbee2mqtt_process:
        logger.info("Остановка Zigbee2MQTT...")
        try:
            zigbee2mqtt_process.terminate()
            zigbee2mqtt_process.wait(timeout=5)
        except:
            zigbee2mqtt_process.kill()
        logger.info("Zigbee2MQTT остановлен")

    # Останавливаем Mosquitto
    if mosquitto_process:
        logger.info("Остановка MQTT брокера Mosquitto...")
        try:
            mosquitto_process.terminate()
            mosquitto_process.wait(timeout=5)
        except:
            mosquitto_process.kill()
        logger.info("MQTT брокер Mosquitto остановлен")


# Регистрируем функцию для выполнения при завершении работы
atexit.register(stop_all_processes)

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

                # Подписка на устройство
                elif data.get("type") == "subscribe_device":
                    device_id = data.get("device_id")
                    if device_id:
                        await ws_manager.subscribe_to_device(websocket, device_id)

                # Подписка на лабораторную работу
                elif data.get("type") == "subscribe_lab":
                    lab_id = data.get("lab_id")
                    if lab_id:
                        await ws_manager.subscribe_to_lab(websocket, lab_id)

        except WebSocketDisconnect:
            # Отключаем WebSocket при разрыве соединения
            ws_manager.disconnect(websocket, user["id"], user["role"])

    except HTTPException:
        await websocket.close(code=1008, reason="Invalid token")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")

# Middleware для логирования запросов


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Логируем только API запросы
    if request.url.path.startswith("/api/"):
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({process_time:.2f}s)")

    return response

# Функция для открытия браузера с документацией API


def open_api_docs():
    # Используем localhost вместо 0.0.0.0 для открытия в браузере
    url = f"http://localhost:{API_PORT}/docs"
    webbrowser.open(url)
    logger.info(f"Открыт браузер с документацией API: {url}")

# Функция для периодической очистки истекших бронирований


def cleanup_expired_bookings_task():
    from services.booking import booking_service

    while True:
        try:
            booking_service.cleanup_expired_bookings()
        except Exception as e:
            logger.error(f"Ошибка при очистке истекших бронирований: {e}")

        # Проверяем каждые 5 минут
        time.sleep(300)

# Обработчик сигналов для корректного завершения


def signal_handler(sig, frame):
    logger.info("Получен сигнал завершения. Останавливаем все процессы...")
    stop_all_processes()
    exit(0)


# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Основная функция


def main():
    # Запускаем MQTT и Zigbee2MQTT
    mqtt_started = start_mosquitto()
    if mqtt_started:
        # Даем время на запуск Mosquitto
        time.sleep(2)

        zigbee_started = start_zigbee2mqtt()
        if zigbee_started:
            # Даем время на запуск Zigbee2MQTT
            time.sleep(5)
        else:
            logger.warning(
                "Не удалось запустить Zigbee2MQTT, сервер будет работать без него")
    else:
        logger.warning(
            "Не удалось запустить MQTT брокер, сервер будет работать без него")

    # Вывод информации о доступе к API
    logger.info(f"API ключ: {API_KEY}")
    logger.info(f"API доступен по адресу: http://{LOCAL_IP}:{API_PORT}")
    logger.info(f"Документация API: http://{LOCAL_IP}:{API_PORT}/docs")
    logger.info(
        f"Для доступа к API с других устройств используйте заголовок 'X-API-Key: {API_KEY}'")

    # Запуск MQTT клиента в отдельном потоке
    mqtt_client = MQTTClient()
    mqtt_thread = mqtt_client.start()

    # Запуск задачи очистки истекших бронирований
    cleanup_thread = Thread(target=cleanup_expired_bookings_task, daemon=True)
    cleanup_thread.start()

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

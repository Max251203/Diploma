import os
import uuid
import socket
import logging
from typing import Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получение локального IP адреса


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.warning(f"Не удалось определить локальный IP: {e}")
        return "0.0.0.0"


# Настройки MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_SUBSCRIBE = os.getenv("MQTT_TOPIC_SUBSCRIBE", "zigbee2mqtt/#")
MQTT_TOPIC_PUBLISH_PREFIX = os.getenv(
    "MQTT_TOPIC_PUBLISH_PREFIX", "zigbee2mqtt")

# Настройки базы данных
DB_PATH = os.getenv("DB_PATH", "iot_lab_data.db")

# Настройки API
API_KEY = os.getenv("API_KEY", str(uuid.uuid4()))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
LOCAL_IP = get_local_ip()

# Настройки JWT
SECRET_KEY = os.getenv(
    "SECRET_KEY", "your-secret-key-for-jwt-please-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа

# Глобальные кэши для хранения данных
devices_cache = {}  # Кэш устройств из bridge/devices
device_availability = {}  # Статус доступности устройств
device_states = {}  # Состояния устройств
network_info = {}  # Информация о сети Zigbee
groups_cache = {}  # Кэш групп устройств

# Глобальные переменные для отслеживания процесса сопряжения
pairing_mode_active = False
pairing_end_time = None
discovered_devices = {}  # Хранит обнаруженные, но еще не подключенные устройства

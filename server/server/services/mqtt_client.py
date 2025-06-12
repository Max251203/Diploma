import json
import paho.mqtt.client as mqtt
from typing import Callable, Dict, Any, Optional
from threading import Thread
import time
from datetime import datetime, timedelta
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_SUBSCRIBE, MQTT_TOPIC_PUBLISH_PREFIX,
    devices_cache, device_availability, device_states, network_info, groups_cache,
    pairing_mode_active, discovered_devices, logger
)
import database


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.connected = False

    def start(self):
        """Запуск MQTT клиента в отдельном потоке"""
        thread = Thread(target=self._connect_loop)
        thread.daemon = True
        thread.start()
        return thread

    def _connect_loop(self):
        """Цикл подключения к MQTT брокеру"""
        while True:
            try:
                logger.info(
                    f"Подключение к MQTT брокеру {MQTT_BROKER}:{MQTT_PORT}")
                self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
                self.client.loop_forever()
            except Exception as e:
                logger.error(f"Ошибка подключения к MQTT брокеру: {e}")
                time.sleep(5)  # Пауза перед повторной попыткой

    def on_connect(self, client, userdata, flags, rc):
        """Обработчик подключения к MQTT брокеру"""
        logger.info(f"Подключено к MQTT брокеру с кодом {rc}")
        self.connected = True

        # Подписки для кэширования данных
        client.subscribe(f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/devices")
        client.subscribe(f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/info")
        client.subscribe(f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/log")
        client.subscribe(f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/groups")
        client.subscribe(f"{MQTT_TOPIC_PUBLISH_PREFIX}/+/availability")
        client.subscribe(f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/event/#")

        # Подписка на все устройства для получения их состояний
        client.subscribe(f"{MQTT_TOPIC_PUBLISH_PREFIX}/+")

        # Запрашиваем начальные данные
        client.publish(
            f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/devices", "{}")
        client.publish(
            f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/groups", "{}")
        client.publish(
            f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/info", "{}")

        logger.info(f"Подписки на топики MQTT выполнены")

    def on_disconnect(self, client, userdata, rc):
        """Обработчик отключения от MQTT брокера"""
        logger.warning(f"Отключено от MQTT брокера с кодом {rc}")
        self.connected = False
        if rc != 0:
            logger.info("Попытка переподключения...")

    def on_message(self, client, userdata, msg):
        """Обработчик сообщений MQTT"""
        try:
            topic = msg.topic
            payload_str = msg.payload.decode()

            # Пропускаем пустые сообщения
            if not payload_str:
                return

            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                logger.warning(
                    f"Не удалось декодировать JSON из сообщения в топике {topic}")
                return

            # Обработка списка устройств
            if topic == f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/devices":
                self.update_devices_cache(payload)
                return

            # Обработка информации о сети
            if topic == f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/info":
                self.update_network_info(payload)
                return

            # Обработка групп
            if topic == f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/groups":
                self.update_groups_cache(payload)
                return

            # Обработка логов моста
            if topic == f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/log":
                self.handle_bridge_log(payload)
                return

            # Обработка событий моста
            if topic.startswith(f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/event/"):
                event_type = topic.split('/')[-1]
                self.handle_bridge_event(event_type, payload)
                return

            # Обработка доступности устройств
            if topic.endswith("/availability"):
                device_id = topic.split('/')[-2]
                device_availability[device_id] = payload
                logger.debug(
                    f"Обновлен статус доступности устройства {device_id}: {payload}")
                return

            # Обработка состояний устройств
            if topic.startswith(f"{MQTT_TOPIC_PUBLISH_PREFIX}/") and not topic.startswith(f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/"):
                device_id = topic.split('/')[-1]

                # Пропускаем ответы на команды set
                if topic.endswith("/set"):
                    return

                # Обновляем состояние устройства в кэше
                device_states[device_id] = payload

                # Сохраняем данные в БД
                database.save_to_db(device_id, payload)

                logger.debug(
                    f"Обновлено состояние устройства {device_id}: {payload}")
                return

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения MQTT: {e}")

    def update_devices_cache(self, devices_list):
        """Обновляет кэш устройств на основе полученного списка"""
        global devices_cache

        new_cache = {}
        for device in devices_list:
            device_id = device.get("ieee_address")
            if device_id:
                new_cache[device_id] = device

        devices_cache = new_cache
        logger.info(
            f"Обновлен кэш устройств, всего устройств: {len(devices_cache)}")

    def update_network_info(self, info_data):
        """Обновляет информацию о сети Zigbee"""
        global network_info
        network_info = info_data
        logger.info("Обновлена информация о сети Zigbee")

    def update_groups_cache(self, groups_list):
        """Обновляет кэш групп устройств"""
        global groups_cache

        new_cache = {}
        for group in groups_list:
            group_id = group.get("id")
            if group_id:
                new_cache[group_id] = group

        groups_cache = new_cache

        # Синхронизируем с локальной БД
        self.sync_groups_with_db()

        logger.info(f"Обновлен кэш групп, всего групп: {len(groups_cache)}")

    def sync_groups_with_db(self):
        """Синхронизирует группы из Zigbee2MQTT с локальной БД"""
        try:
            conn = database.get_db_connection()
            cursor = conn.cursor()

            # Получаем все группы из БД
            cursor.execute(
                "SELECT id, name, description, devices FROM device_groups")
            db_groups = cursor.fetchall()

            # Создаем словарь групп из БД по имени
            db_groups_by_name = {}
            for group in db_groups:
                db_groups_by_name[group[1]] = {
                    "id": group[0],
                    "description": group[2],
                    "devices": json.loads(group[3])
                }

            # Проверяем, нужно ли добавить новые группы из Zigbee2MQTT в БД
            for group_id, group in groups_cache.items():
                friendly_name = group.get("friendly_name")
                if friendly_name and friendly_name not in db_groups_by_name:
                    # Добавляем группу в БД
                    members = group.get("members", [])
                    devices = [member.get("ieee_address")
                               for member in members if member.get("ieee_address")]

                    cursor.execute(
                        "INSERT INTO device_groups (name, description, devices) VALUES (?, ?, ?)",
                        (friendly_name,
                         f"Группа {friendly_name}", json.dumps(devices))
                    )
                    logger.info(f"Добавлена новая группа {friendly_name} в БД")

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка синхронизации групп с БД: {e}")

    def handle_bridge_log(self, log_data):
        """Обрабатывает логи моста Zigbee"""
        message = log_data.get("message", "")
        level = log_data.get("level", "")

        # Обработка важных событий из логов
        if level in ["error", "warning"]:
            logger.warning(f"Zigbee2MQTT лог [{level}]: {message}")
        else:
            logger.debug(f"Zigbee2MQTT лог [{level}]: {message}")

    def handle_bridge_event(self, event_type, payload):
        """Обрабатывает события моста Zigbee"""
        global discovered_devices, pairing_mode_active

        # Обработка событий сопряжения
        if pairing_mode_active:
            if event_type == "device_interview":
                self.handle_device_interview(payload)
            elif event_type == "device_joined":
                self.handle_device_joined(payload)
            elif event_type == "device_announce":
                self.handle_device_announce(payload)

        # Запрашиваем обновление данных при важных событиях
        if event_type in ["device_joined", "device_interview", "device_leave", "device_removed"]:
            self.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/devices", "{}")

        if event_type in ["group_added", "group_removed", "group_updated"]:
            self.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/groups", "{}")

        logger.debug(f"Получено событие моста: {event_type}")

    def handle_device_interview(self, payload):
        """Обрабатывает событие интервью устройства (получение информации о возможностях)"""
        global discovered_devices

        device_id = payload.get("data", {}).get("ieee_address")
        status = payload.get("status")

        if not device_id:
            return
        if status == "started":
            logger.info(f"Начато интервью устройства {device_id}")
        elif status == "successful":
            # Устройство успешно прошло интервью и готово к использованию
            device_info = payload.get("data", {})
            discovered_devices[device_id] = device_info
            logger.info(
                f"Устройство {device_id} успешно прошло интервью и доступно для добавления")
        elif status == "failed":
            logger.error(
                f"Не удалось завершить интервью устройства {device_id}")

    def handle_device_joined(self, payload):
        """Обрабатывает событие подключения устройства к сети"""
        device_id = payload.get("ieee_address")
        if device_id:
            logger.info(f"Устройство {device_id} подключилось к сети")

    def handle_device_announce(self, payload):
        """Обрабатывает событие анонса устройства в сети"""
        device_id = payload.get("ieee_address")
        if device_id:
            logger.info(f"Устройство {device_id} анонсировало себя в сети")

    def send_command(self, device_id: str, command: Dict[str, Any]) -> bool:
        """Отправляет команду устройству"""
        if not self.connected:
            logger.warning("Попытка отправить команду без подключения к MQTT")
            return False

        try:
            result = self.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/{device_id}/set",
                json.dumps(command)
            )

            if result.rc != 0:
                logger.error(
                    f"Ошибка отправки команды устройству {device_id}: код {result.rc}")
                return False

            logger.info(
                f"Команда отправлена устройству {device_id}: {command}")
            return True
        except Exception as e:
            logger.error(
                f"Ошибка отправки команды устройству {device_id}: {e}")
            return False

    def request_devices(self):
        """Запрашивает обновление списка устройств"""
        if not self.connected:
            logger.warning(
                "Попытка запросить устройства без подключения к MQTT")
            return False

        try:
            result = self.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/devices", "{}")
            return result.rc == 0
        except Exception as e:
            logger.error(f"Ошибка запроса устройств: {e}")
            return False

    def request_groups(self):
        """Запрашивает обновление списка групп"""
        if not self.connected:
            logger.warning("Попытка запросить группы без подключения к MQTT")
            return False

        try:
            result = self.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/groups", "{}")
            return result.rc == 0
        except Exception as e:
            logger.error(f"Ошибка запроса групп: {e}")
            return False

    def request_network_info(self):
        """Запрашивает обновление информации о сети"""
        if not self.connected:
            logger.warning(
                "Попытка запросить информацию о сети без подключения к MQTT")
            return False

        try:
            result = self.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/info", "{}")
            return result.rc == 0
        except Exception as e:
            logger.error(f"Ошибка запроса информации о сети: {e}")
            return False

    def start_pairing(self, duration: int = 60) -> bool:
        """Включает режим сопряжения для добавления новых устройств"""
        global pairing_mode_active, pairing_end_time, discovered_devices

        if not self.connected:
            logger.warning(
                "Попытка включить режим сопряжения без подключения к MQTT")
            return False

        try:
            # Очищаем список обнаруженных устройств
            discovered_devices = {}

            # Отправляем команду в zigbee2mqtt для включения режима сопряжения
            result = self.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/permit_join",
                json.dumps({"value": True, "time": duration})
            )

            if result.rc != 0:
                logger.error(
                    f"Ошибка включения режима сопряжения: код {result.rc}")
                return False

            pairing_mode_active = True
            pairing_end_time = datetime.now() + timedelta(seconds=duration)

            logger.info(f"Режим сопряжения активирован на {duration} секунд")
            return True
        except Exception as e:
            logger.error(f"Ошибка при включении режима сопряжения: {e}")
            return False

    def stop_pairing(self) -> bool:
        """Отключает режим сопряжения"""
        global pairing_mode_active, pairing_end_time

        if not self.connected:
            logger.warning(
                "Попытка отключить режим сопряжения без подключения к MQTT")
            return False

        try:
            # Отправляем команду в zigbee2mqtt для отключения режима сопряжения
            result = self.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/permit_join",
                json.dumps({"value": False})
            )

            if result.rc != 0:
                logger.error(
                    f"Ошибка отключения режима сопряжения: код {result.rc}")
                return False

            pairing_mode_active = False
            pairing_end_time = None

            logger.info("Режим сопряжения отключен")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отключении режима сопряжения: {e}")
            return False

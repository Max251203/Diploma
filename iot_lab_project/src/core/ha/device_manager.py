from typing import List, Dict, Any, Callable
from core.ha.entity_manager import EntityManager
from core.ha.ws_client import HomeAssistantWSClient

class DeviceManager:
    """Менеджер для работы с устройствами Home Assistant"""
    
    def __init__(self, ws_client: HomeAssistantWSClient, entity_manager: EntityManager):
        self.ws = ws_client
        self.entity_manager = entity_manager

    def get_physical_devices(self, callback: Callable[[List[Dict[str, Any]]], None]):
        """
        Загружает список физических устройств с их сущностями.
        Результат передается в callback.
        """
        def on_devices_loaded(devices):
            entities = self.entity_manager.get_all()

            entity_map = {}
            for entity in entities:
                dev_id = entity.get("device_id")
                if dev_id:
                    entity_map.setdefault(dev_id, []).append(entity)

            physical_devices = []
            for dev in devices:
                dev_id = dev.get("id")
                if dev_id in entity_map:
                    physical_devices.append({
                        "id": dev_id,
                        "name": dev.get("name_by_user") or dev.get("name") or "Без названия",
                        "manufacturer": dev.get("manufacturer", "Неизвестно"),
                        "model": dev.get("model", "Неизвестно"),
                        "entities": entity_map[dev_id]
                    })

            callback(physical_devices)

        self.ws.send_command("config/device_registry/list", callback=on_devices_loaded)

    def get_categorized_devices(self, callback: Callable[[Dict[str, List[Dict[str, Any]]]], None]):
        """
        Загружает устройства и группирует их по категориям.
        Результат передается в callback.
        """
        def on_devices(devices):
            categories = {
                "Датчики": [],
                "Исполнительные устройства": [],
                "Системные": [],
                "Прочее": []
            }

            for device in devices:
                category = self._categorize_device(device)
                categories[category].append(device)

            callback(categories)

        self.get_physical_devices(callback=on_devices)

    def _categorize_device(self, device: Dict[str, Any]) -> str:
        entities = device["entities"]
        name = (device.get("name") or "").lower()
        model = (device.get("model") or "").lower()
        manufacturer = (device.get("manufacturer") or "").lower()
        full_name = f"{manufacturer} {model}".lower()

        known_actuators = ["xiaomi mi air", "xiaomi air purifier", "mi air purifier"]
        for keyword in known_actuators:
            if keyword in full_name or keyword in name:
                return "Исполнительные устройства"

        system_keywords = [
            "sun", "home assistant", "hacs", "zigbee2mqtt", "mosquitto",
            "terminal", "ssh", "file editor", "supervisor", "host",
            "core", "update", "tailscale"
        ]
        if any(s in name for s in system_keywords):
            return "Системные"

        if "add-on" in model or "add-on" in name or "integration" in name or "integration" in model:
            return "Системные"

        if any(e.get("entity_id", "").startswith(("light.", "switch.", "fan.", "cover."))
               for e in entities):
            return "Исполнительные устройства"

        sensor_classes = [
            "temperature", "humidity", "motion", "battery", "illuminance",
            "voltage", "power", "energy", "current", "water", "opening", "occupancy"
        ]
        if any(e.get("device_class") in sensor_classes or
               e.get("entity_id", "").startswith(("sensor.", "binary_sensor."))
               for e in entities):
            return "Датчики"

        return "Прочее"
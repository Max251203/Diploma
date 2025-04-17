from typing import List, Dict, Any, Callable, Optional
from core.ha.ws_client import HomeAssistantWSClient
from core.ha.rest_client import HomeAssistantRestClient

class EntityManager:
    """Менеджер для работы с сущностями Home Assistant"""

    def __init__(self, ws_client: HomeAssistantWSClient, rest_client: Optional[HomeAssistantRestClient] = None):
        self.ws = ws_client
        self.rest = rest_client
        self.entities: List[Dict[str, Any]] = []

        # Загружаем сущности при инициализации
        self._load_entities()

    def _load_entities(self):
        """Загружает список всех сущностей через WebSocket"""
        def callback(result):
            if isinstance(result, list):
                self.entities = result

        self.ws.send_command("config/entity_registry/list", callback=callback)

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает все сущности"""
        return self.entities

    def get_by_device(self, device_id: str) -> List[Dict[str, Any]]:
        """Возвращает сущности, связанные с указанным устройством"""
        return [e for e in self.entities if e.get("device_id") == device_id]

    def get_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Возвращает сущности указанного домена"""
        return [e for e in self.entities if e.get("entity_id", "").startswith(f"{domain}.")]

    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Возвращает сущность по ID"""
        for e in self.entities:
            if e.get("entity_id") == entity_id:
                return e
        return {}

    def control_entity(self, entity_id: str, service: str, data: Optional[Dict] = None):
        """Отправляет команду управления сущностью через WebSocket"""
        domain = entity_id.split('.')[0]
        service_data = {"entity_id": entity_id}

        if data:
            service_data.update(data)

        self.ws.send_command("call_service", {
            "domain": domain,
            "service": service,
            "service_data": service_data
        })

    def get_states(self, callback: Callable[[List[Dict[str, Any]]], None]):
        """Получает состояния всех сущностей через WebSocket"""
        self.ws.send_command("get_states", callback=callback)

    def get_entity_state(self, entity_id: str, callback: Callable[[Optional[Dict[str, Any]]], None]):
        """
        Получает состояние конкретной сущности.
        Использует REST API, если доступно, иначе WebSocket.
        """
        if self.rest:
            try:
                state = self.rest.get_state(entity_id)
                callback(state)
                return
            except Exception:
                pass

        def on_states_loaded(states):
            for state in states:
                if state.get("entity_id") == entity_id:
                    callback(state)
                    return
            callback(None)

        self.get_states(callback=on_states_loaded)

    def update_sensor(self, entity_id: str) -> bool:
        """
        Обновляет состояние датчика через REST API (если доступно).
        Возвращает True при отправке запроса.
        """
        if self.rest:
            return self.rest.update_entity(entity_id)

        try:
            self.ws.send_command("call_service", {
                "domain": "homeassistant",
                "service": "update_entity",
                "service_data": {"entity_id": entity_id}
            })
            return True
        except Exception:
            return False
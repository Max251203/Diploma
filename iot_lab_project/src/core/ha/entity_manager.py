from typing import List, Dict, Any

class EntityManager:
    """Менеджер для работы с сущностями Home Assistant"""
    
    def __init__(self, ws_client, rest_client=None):
        self.ws = ws_client
        self.rest = rest_client
        self.entities = self._load_entities()
    
    def _load_entities(self) -> List[Dict[str, Any]]:
        """Загружает список всех сущностей через WebSocket"""
        return self.ws.send_command("config/entity_registry/list")
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает список всех сущностей"""
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
    
    def control_entity(self, entity_id: str, service: str, data=None):
        """Отправляет команду управления сущностью через WebSocket"""
        domain = entity_id.split('.')[0]
        service_data = {"entity_id": entity_id}
        
        if data:
            service_data.update(data)
        
        return self.ws.send_command("call_service", {
            "domain": domain,
            "service": service,
            "service_data": service_data
        })
    
    def get_states(self):
        """Получает текущие состояния всех сущностей через WebSocket"""
        return self.ws.send_command("get_states")
    
    def get_entity_state(self, entity_id: str):
        """
        Получает состояние конкретной сущности
        Использует REST API для более быстрого точечного запроса
        """
        if self.rest:
            try:
                return self.rest.get_state(entity_id)
            except Exception:
                pass
        
        # Запасной вариант через WebSocket
        states = self.get_states()
        for state in states:
            if state.get("entity_id") == entity_id:
                return state
        return None
    
    def update_sensor(self, entity_id: str) -> bool:
        """
        Обновляет состояние датчика через REST API
        REST API более надежен для принудительного обновления датчиков
        """
        if self.rest:
            return self.rest.update_entity(entity_id)
        
        # Запасной вариант через WebSocket
        try:
            self.ws.send_command("call_service", {
                "domain": "homeassistant",
                "service": "update_entity",
                "service_data": {"entity_id": entity_id}
            })
            return True
        except Exception:
            return False
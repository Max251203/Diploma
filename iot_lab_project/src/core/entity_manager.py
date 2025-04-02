from typing import List, Dict, Any
from core.ws_client import HomeAssistantWSClient


class EntityManager:
    def __init__(self, ws_client: HomeAssistantWSClient):
        self.ws = ws_client
        self.entities = self._load_entities()

    def _load_entities(self) -> List[Dict[str, Any]]:
        return self.ws.send_command("config/entity_registry/list")

    def get_all(self) -> List[Dict[str, Any]]:
        return self.entities

    def get_by_device(self, device_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.entities if e.get("device_id") == device_id]

    def get_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        return [e for e in self.entities if e.get("entity_id", "").startswith(f"{domain}.")]

    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        for e in self.entities:
            if e.get("entity_id") == entity_id:
                return e
        return {}

    def format_entity(self, entity: Dict[str, Any]) -> str:
        eid = entity.get("entity_id", "unknown")
        name = entity.get("original_name", "—")
        domain = eid.split(".")[0]
        return f"[{domain.upper()}] {name} ({eid})"
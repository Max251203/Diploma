import os
import requests
from typing import List, Dict, Any
from core.ws_client import HomeAssistantWSClient


class EntityManager:
    def __init__(self, ws_client: HomeAssistantWSClient):
        self.ws = ws_client
        self.api_url = os.getenv("HA_API_URL")
        self.token = os.getenv("HA_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
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

    def get_state(self, entity_id: str) -> str:
        url = f"{self.api_url}/states/{entity_id}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get("state", "unknown")
            return "error"
        except Exception as e:
            return f"error: {e}"

    def turn_on(self, entity_id: str) -> bool:
        return self._call_service(entity_id, "turn_on")

    def turn_off(self, entity_id: str) -> bool:
        return self._call_service(entity_id, "turn_off")

    def toggle(self, entity_id: str) -> bool:
        return self._call_service(entity_id, "toggle")

    def _call_service(self, entity_id: str, action: str) -> bool:
        domain = entity_id.split(".")[0]
        url = f"{self.api_url}/services/{domain}/{action}"
        payload = {
            "entity_id": entity_id
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return response.status_code == 200
        except Exception:
            return False

    def format_entity(self, entity: Dict[str, Any]) -> str:
        eid = entity.get("entity_id", "unknown")
        name = entity.get("original_name", "—")
        domain = eid.split(".")[0]
        return f"[{domain.upper()}] {name} ({eid})"
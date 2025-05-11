import requests
from urllib.parse import urljoin

class HomeAssistantRestClient:
    """REST клиент для Home Assistant"""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_state(self, entity_id: str):
        """Получить состояние сущности"""
        url = urljoin(self.base_url, f"/api/states/{entity_id}")
        resp = requests.get(url, headers=self.headers, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def update_entity(self, entity_id: str) -> bool:
        """Отправить команду обновления сущности"""
        try:
            url = urljoin(self.base_url, "/api/services/homeassistant/update_entity")
            payload = {"entity_id": entity_id}
            resp = requests.post(url, json=payload, headers=self.headers, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            print(f"[REST] Ошибка при обновлении {entity_id}: {e}")
            return False
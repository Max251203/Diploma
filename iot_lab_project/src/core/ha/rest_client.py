import requests
from urllib.parse import urljoin

class HomeAssistantRestClient:
    """REST клиент для взаимодействия с Home Assistant"""
    
    def __init__(self, base_url, token):
        """
        Инициализирует REST клиент
        
        Args:
            base_url (str): Базовый URL Home Assistant (например, http://192.168.1.100:8123)
            token (str): Токен доступа
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_state(self, entity_id):
        """
        Получает состояние конкретной сущности
        
        Args:
            entity_id (str): ID сущности
        
        Returns:
            dict: Состояние сущности
        """
        url = urljoin(self.base_url, f"/api/states/{entity_id}")
        response = requests.get(url, headers=self.headers, timeout=5)
        response.raise_for_status()
        return response.json()
    
    def update_entity(self, entity_id):
        """
        Обновляет состояние сущности через REST API
        
        Args:
            entity_id (str): ID сущности для обновления
        
        Returns:
            bool: True если обновление успешно, иначе False
        """
        try:
            url = urljoin(self.base_url, f"/api/services/homeassistant/update_entity")
            payload = {"entity_id": entity_id}
            response = requests.post(url, json=payload, headers=self.headers, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Ошибка при обновлении {entity_id} через REST: {str(e)}")
            return False
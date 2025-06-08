from core.adapters.base_adapter import BaseAdapter
from core.ha.device_manager import DeviceManager
from core.ha.entity_manager import EntityManager
from core.ha.ws_client import HomeAssistantWSClient
from core.ha.rest_client import HomeAssistantRestClient
from typing import List, Dict


class HAAdapter(BaseAdapter):
    def __init__(self, ws_client: HomeAssistantWSClient, rest_client: HomeAssistantRestClient, entity_manager: EntityManager, device_manager: DeviceManager, name: str):
        super().__init__()
        self.ws = ws_client
        self.rest = rest_client
        self.entity_manager = entity_manager
        self.device_manager = device_manager
        self.name = name
        self.connected = self.ws.is_connected()

    def connect(self) -> bool:
        return self.connected

    def get_devices_by_category(self) -> Dict[str, List[Dict]]:
        result = {}

        def callback(data):
            result.update(data)
        self.device_manager.get_categorized_devices(callback)
        return result

    def get_device_details(self, device_id: str) -> Dict:
        return self.device_manager.entity_manager.get_entity(device_id)

    def send_command(self, entity_id: str, command: Dict) -> bool:
        domain = entity_id.split('.')[0]
        payload = {
            "domain": domain,
            "service": command.get("service"),
            "service_data": {
                "entity_id": entity_id
            }
        }
        if "data" in command:
            payload["service_data"].update(command["data"])

        try:
            self.ws.send_command("call_service", payload)
            return True
        except Exception:
            return False

    def get_connection_name(self) -> str:
        return self.name

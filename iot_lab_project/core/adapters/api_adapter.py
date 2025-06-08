from core.adapters.base_adapter import BaseAdapter
import requests
from typing import List, Dict


class APIAdapter(BaseAdapter):
    def __init__(self, name: str, url: str, api_key: str):
        super().__init__()
        self.name = name
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.headers = {"x-api-key": self.api_key}

    def connect(self) -> bool:
        try:
            res = requests.get(f"{self.url}/ping",
                               headers=self.headers, timeout=5)
            self.connected = res.ok
        except Exception:
            self.connected = False
        return self.connected

    def get_devices_by_category(self) -> Dict[str, List[Dict]]:
        try:
            res = requests.get(f"{self.url}/api/devices", headers=self.headers)
            if res.ok:
                json_data = res.json()
                return self._categorize(json_data.get("devices", {}))
        except Exception:
            pass
        return {}

    def _categorize(self, devices_dict: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        categories = {
            "Реле и переключатели": [],
            "Датчики": [],
            "Прочее": []
        }
        for device_id, device in devices_dict.items():
            dev_info = dict(device)
            dev_info["id"] = device_id
            dev_info["entity_id"] = device_id

            model = (dev_info.get("model") or "").lower()
            if "switch" in model or "relay" in model:
                categories["Реле и переключатели"].append(dev_info)
            elif "sensor" in model or "temp" in model or "hum" in model:
                categories["Датчики"].append(dev_info)
            else:
                categories["Прочее"].append(dev_info)

        return categories

    def get_device_details(self, device_id: str) -> Dict:
        try:
            res = requests.get(
                f"{self.url}/api/devices/{device_id}", headers=self.headers)
            if res.ok:
                return res.json()
        except Exception:
            pass
        return {}

    def send_command(self, device_id: str, command: Dict) -> bool:
        try:
            res = requests.post(
                f"{self.url}/api/devices/{device_id}/command",
                headers=self.headers,
                json={"command": command}
            )
            return res.ok
        except Exception:
            return False

    def get_connection_name(self) -> str:
        return self.name

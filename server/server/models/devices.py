from pydantic import BaseModel
from typing import Optional, Dict, List, Any


class CommandModel(BaseModel):
    command: Dict[str, Any]


class DeviceHistoryParams(BaseModel):
    limit: int = 100
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class GroupModel(BaseModel):
    name: str
    devices: List[str]
    description: Optional[str] = None


class AutomationTrigger(BaseModel):
    type: str  # device, time, etc.
    device_id: Optional[str] = None
    property: Optional[str] = None
    condition: Optional[str] = None  # eq, gt, lt
    value: Optional[Any] = None
    time: Optional[str] = None


class AutomationAction(BaseModel):
    type: str  # device_command, notification, etc.
    device_id: Optional[str] = None
    command: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class AutomationModel(BaseModel):
    name: str
    description: Optional[str] = None
    enabled: bool = True
    trigger: AutomationTrigger
    actions: List[AutomationAction]


class PairingMode(BaseModel):
    duration: int = 60  # Время в секундах, в течение которого будет активен режим сопряжения


class DeviceAddResponse(BaseModel):
    success: bool
    message: str
    device_id: Optional[str] = None
    device_info: Optional[Dict] = None

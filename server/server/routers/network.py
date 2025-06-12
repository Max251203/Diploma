from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from utils.security import get_current_active_user
from config import network_info
from services.mqtt_client import MQTTClient

router = APIRouter(
    prefix="/api/network",
    tags=["network"],
    responses={401: {"description": "Unauthorized"}},
)


@router.get("/info")
async def get_network_info(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получить информацию о сети Zigbee"""
    return network_info


@router.post("/refresh")
async def refresh_network_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    mqtt_client: MQTTClient = Depends(lambda: MQTTClient())
):
    """Принудительно обновить информацию о сети Zigbee"""
    success = mqtt_client.request_network_info()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка запроса обновления информации о сети"
        )

    return {
        "status": "success",
        "message": "Запрос на обновление информации о сети отправлен"
    }

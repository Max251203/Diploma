from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Any, Optional
import json
from models.devices import CommandModel, DeviceHistoryParams
from services import devices as devices_service
from utils.security import get_current_active_user
from config import devices_cache, device_states, API_KEY, groups_cache, MQTT_TOPIC_PUBLISH_PREFIX
from services.mqtt_client import MQTTClient

router = APIRouter(
    prefix="/api/devices",
    tags=["devices"],
    responses={401: {"description": "Unauthorized"}},
)


@router.get("/")
async def get_devices(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получение списка всех устройств и их текущих состояний"""
    return devices_service.get_all_devices()


@router.get("/{device_id}")
async def get_device(device_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получение текущего состояния конкретного устройства"""
    return devices_service.get_device(device_id)


@router.get("/{device_id}/history")
async def get_device_history(
    device_id: str,
    params: DeviceHistoryParams = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Получение истории показаний устройства"""
    return devices_service.get_device_history(
        device_id,
        params.limit,
        params.start_date,
        params.end_date
    )


@router.post("/{device_id}/command")
async def send_device_command(
    device_id: str,
    command_data: CommandModel,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    mqtt_client: MQTTClient = Depends(lambda: MQTTClient())
):
    """Отправить команду устройству"""
    if not command_data.command:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Команда не указана"
        )

    # Проверяем, что устройство существует
    if device_id not in devices_cache and device_id not in groups_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство или группа не найдены"
        )

    # Отправляем команду
    success = mqtt_client.send_command(device_id, command_data.command)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отправки команды"
        )

    return {
        "status": "success",
        "message": f"Команда отправлена устройству {device_id}"
    }


@router.post("/refresh")
async def refresh_devices(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    mqtt_client: MQTTClient = Depends(lambda: MQTTClient())
):
    """Принудительно обновить кэш устройств"""
    success = mqtt_client.request_devices()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка запроса обновления устройств"
        )

    return {
        "status": "success",
        "message": "Запрос на обновление списка устройств отправлен"
    }


@router.delete("/{device_id}")
async def remove_device(
    device_id: str,
    force: bool = Query(False),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    mqtt_client: MQTTClient = Depends(lambda: MQTTClient())
):
    """
    Удалить устройство из сети

    - force: Принудительное удаление устройства, даже если оно недоступно
    """
    # Проверяем, что пользователь имеет права администратора
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления устройств"
        )

    # Проверяем, что устройство существует
    if device_id not in devices_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено"
        )

    try:
        # Отправляем команду в zigbee2mqtt для удаления устройства
        mqtt_client.client.publish(
            f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/device/remove",
            json.dumps({"id": device_id, "force": force})
        )

        # Запрашиваем обновление списка устройств
        mqtt_client.request_devices()

        return {"success": True, "message": f"Устройство {device_id} удалено"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления устройства: {str(e)}"
        )

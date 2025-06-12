from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Any, Optional
import json
import time
from models.devices import GroupModel
from services import devices as devices_service
from utils.security import get_current_active_user
from config import MQTT_TOPIC_PUBLISH_PREFIX
from services.mqtt_client import MQTTClient

router = APIRouter(
    prefix="/api/groups",
    tags=["groups"],
    responses={401: {"description": "Unauthorized"}},
)


@router.get("/")
async def get_groups(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получить все группы устройств"""
    return devices_service.get_all_groups()


@router.get("/{group_id}")
async def get_group(group_id: int, current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получить группу по ID"""
    return devices_service.get_group(group_id)


@router.post("/")
async def create_group(
    group: GroupModel,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    mqtt_client: MQTTClient = Depends(lambda: MQTTClient())
):
    """Создать новую группу устройств"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для создания групп"
        )

    # Создаем группу в zigbee2mqtt
    try:
        mqtt_client.client.publish(
            f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/group/add",
            json.dumps({"friendly_name": group.name})
        )

        # Ждем небольшую паузу для обработки запроса
        time.sleep(0.5)

        # Добавляем устройства в группу
        for device_id in group.devices:
            mqtt_client.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/group/members/add",
                json.dumps({
                    "group": group.name,
                    "device": device_id
                })
            )

        # Запрашиваем обновление списка групп
        mqtt_client.request_groups()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания группы в zigbee2mqtt: {str(e)}"
        )

    # Создаем группу в локальной БД
    group_data = devices_service.create_group(
        group.name, group.devices, group.description)

    return group_data


@router.put("/{group_id}")
async def update_group(
    group_id: int,
    group: GroupModel,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    mqtt_client: MQTTClient = Depends(lambda: MQTTClient())
):
    """Обновить существующую группу устройств"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления групп"
        )

    # Получаем текущую информацию о группе
    current_group = devices_service.get_group(group_id)

    # Обновляем название группы в zigbee2mqtt, если оно изменилось
    try:
        if current_group["name"] != group.name:
            mqtt_client.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/group/rename",
                json.dumps({
                    "old": current_group["name"],
                    "new": group.name
                })
            )

        # Обновляем состав устройств
        current_devices = set(current_group["devices"])
        new_devices = set(group.devices)

        # Добавляем новые устройства в группу
        devices_to_add = new_devices - current_devices
        for device_id in devices_to_add:
            mqtt_client.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/group/members/add",
                json.dumps({
                    "group": group.name,
                    "device": device_id
                })
            )

        # Удаляем устройства из группы
        devices_to_remove = current_devices - new_devices
        for device_id in devices_to_remove:
            mqtt_client.client.publish(
                f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/group/members/remove",
                json.dumps({
                    "group": group.name,
                    "device": device_id
                })
            )

        # Запрашиваем обновление списка групп
        mqtt_client.request_groups()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления группы в zigbee2mqtt: {str(e)}"
        )

    # Обновляем группу в локальной БД
    updated_group = devices_service.update_group(group_id, {
        "name": group.name,
        "description": group.description,
        "devices": group.devices
    })

    return updated_group


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    mqtt_client: MQTTClient = Depends(lambda: MQTTClient())
):
    """Удалить группу устройств"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления групп"
        )

    # Получаем информацию о группе
    group = devices_service.get_group(group_id)

    # Удаляем группу из zigbee2mqtt
    try:
        mqtt_client.client.publish(
            f"{MQTT_TOPIC_PUBLISH_PREFIX}/bridge/request/group/remove",
            json.dumps({"group": group["name"]})
        )

        # Запрашиваем обновление списка групп
        mqtt_client.request_groups()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления группы из zigbee2mqtt: {str(e)}"
        )

    # Удаляем группу из локальной БД
    devices_service.delete_group(group_id)

    return {"status": "success", "message": f"Группа {group_id} удалена"}

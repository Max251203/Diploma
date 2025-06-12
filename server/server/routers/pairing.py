from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any
from datetime import datetime, timedelta
import time
from models.devices import PairingMode, DeviceAddResponse
from utils.security import get_current_active_user
from config import pairing_mode_active, pairing_end_time, discovered_devices, devices_cache
from services.mqtt_client import MQTTClient

router = APIRouter(
    prefix="/api/pairing",
    tags=["pairing"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/start")
async def start_pairing_mode(
    pairing_config: PairingMode,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    mqtt_client: MQTTClient = Depends(lambda: MQTTClient())
):
    """Включить режим сопряжения для добавления новых устройств"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для включения режима сопряжения"
        )

    global pairing_mode_active, pairing_end_time, discovered_devices

    if pairing_mode_active:
        return {"success": True, "message": "Режим сопряжения уже активен"}

    # Включаем режим сопряжения
    success = mqtt_client.start_pairing(pairing_config.duration)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка включения режима сопряжения"
        )

    # Запускаем таймер для автоматического отключения режима сопряжения
    background_tasks.add_task(
        lambda: (time.sleep(pairing_config.duration),
                 mqtt_client.stop_pairing())
    )

    return {
        "success": True,
        "message": f"Режим сопряжения активирован на {pairing_config.duration} секунд",
        "expires_at": pairing_end_time.isoformat() if pairing_end_time else None
    }


@router.get("/status")
async def get_pairing_status(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Получить текущий статус режима сопряжения и список обнаруженных устройств"""
    global pairing_mode_active, pairing_end_time, discovered_devices

    if not pairing_mode_active:
        return {
            "active": False,
            "message": "Режим сопряжения неактивен",
            "discovered_devices": []
        }

    time_left = (pairing_end_time - datetime.now()
                 ).total_seconds() if pairing_end_time else 0
    if time_left <= 0:
        pairing_mode_active = False
        return {
            "active": False,
            "message": "Режим сопряжения завершен",
            "discovered_devices": []
        }

    return {
        "active": True,
        "time_left": time_left,
        "expires_at": pairing_end_time.isoformat() if pairing_end_time else None,
        "discovered_devices": [
            {
                "id": device_id,
                "info": device_info
            } for device_id, device_info in discovered_devices.items()
        ]
    }


@router.post("/stop")
async def stop_pairing_mode(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    mqtt_client: MQTTClient = Depends(lambda: MQTTClient())
):
    """Принудительно отключить режим сопряжения"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для отключения режима сопряжения"
        )

    global pairing_mode_active, pairing_end_time

    if not pairing_mode_active:
        return {"success": True, "message": "Режим сопряжения уже неактивен"}

    # Отключаем режим сопряжения
    success = mqtt_client.stop_pairing()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отключения режима сопряжения"
        )

    return {"success": True, "message": "Режим сопряжения отключен"}


@router.post("/devices/add/{device_id}", response_model=DeviceAddResponse)
async def add_device(
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    mqtt_client: MQTTClient = Depends(lambda: MQTTClient())
):
    """Добавить обнаруженное устройство в сеть"""
    # Проверяем, что пользователь имеет права администратора или преподавателя
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для добавления устройств"
        )

    global discovered_devices

    if device_id not in discovered_devices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено в списке обнаруженных устройств"
        )

    # Запрашиваем обновление списка устройств для подтверждения
    mqtt_client.request_devices()

    # Ждем небольшую паузу для обновления кэша
    time.sleep(0.5)

    # Проверяем, есть ли устройство в кэше
    if device_id in devices_cache:
        device_info = devices_cache[device_id]

        # Удаляем устройство из списка обнаруженных, так как оно теперь подключено
        if device_id in discovered_devices:
            del discovered_devices[device_id]

        return {
            "success": True,
            "message": f"Устройство {device_id} успешно добавлено",
            "device_id": device_id,
            "device_info": device_info
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Устройство не найдено в сети после добавления"
        )

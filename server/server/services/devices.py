from typing import Dict, List, Any, Optional
from fastapi import HTTPException, status
from config import devices_cache, device_states, device_availability, groups_cache
import database
import json


def get_all_devices() -> Dict[str, Dict[str, Any]]:
    """Получение всех устройств с их состояниями"""
    devices_info = {}
    for device_id, device in devices_cache.items():
        # Объединяем информацию из разных кэшей
        device_info = {
            **device,
            "state": device_states.get(device_id, {}),
            "available": device_availability.get(device_id, {"state": "unknown"}).get("state", "unknown")
        }
        devices_info[device_id] = device_info

    return devices_info


def get_device(device_id: str) -> Dict[str, Any]:
    """Получение информации об устройстве по ID"""
    if device_id not in devices_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено"
        )

    # Объединяем информацию из разных кэшей
    device_info = {
        **devices_cache[device_id],
        "state": device_states.get(device_id, {}),
        "available": device_availability.get(device_id, {"state": "unknown"}).get("state", "unknown")
    }

    return device_info


def get_device_history(device_id: str, limit: int = 100, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Получение истории показаний устройства"""
    if device_id not in devices_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Устройство не найдено"
        )

    conn = database.get_db_connection()
    cursor = conn.cursor()

    query = "SELECT timestamp, data FROM sensor_data WHERE device_id = ?"
    params = [device_id]

    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)

    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    history = [{"timestamp": row["timestamp"],
                "data": json.loads(row["data"])} for row in rows]
    return history


def get_all_groups() -> List[Dict[str, Any]]:
    """Получение всех групп устройств"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, devices FROM device_groups")
    rows = cursor.fetchall()
    conn.close()

    local_groups = [
        {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "devices": json.loads(row["devices"])
        } for row in rows
    ]

    # Добавляем информацию из кэша Zigbee2MQTT
    for local_group in local_groups:
        for group_id, zigbee_group in groups_cache.items():
            if zigbee_group.get("friendly_name") == local_group["name"]:
                local_group["zigbee_info"] = zigbee_group
                break

    return local_groups


def create_group(name: str, devices: List[str], description: Optional[str] = None) -> Dict[str, Any]:
    """Создание новой группы устройств"""
    # Проверяем, что группа с таким именем не существует
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM device_groups WHERE name = ?", (name,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Группа с таким именем уже существует"
        )

    # Создаем группу в БД
    cursor.execute(
        "INSERT INTO device_groups (name, description, devices) VALUES (?, ?, ?)",
        (name, description or f"Группа {name}", json.dumps(devices))
    )
    group_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": group_id,
        "name": name,
        "description": description or f"Группа {name}",
        "devices": devices
    }


def update_group(group_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Обновление группы устройств"""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Проверяем существование группы
    cursor.execute("SELECT name FROM device_groups WHERE id = ?", (group_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )

    # Обновляем группу
    fields = []
    values = []

    if "name" in data and data["name"]:
        # Проверяем, что новое имя не занято
        if data["name"] != row["name"]:
            cursor.execute(
                "SELECT id FROM device_groups WHERE name = ?", (data["name"],))
            if cursor.fetchone():
                conn.close()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Группа с таким именем уже существует"
                )

        fields.append("name = ?")
        values.append(data["name"])

    if "description" in data:
        fields.append("description = ?")
        values.append(data["description"])

    if "devices" in data:
        fields.append("devices = ?")
        values.append(json.dumps(data["devices"]))

    if not fields:
        conn.close()
        return get_group(group_id)

    values.append(group_id)

    cursor.execute(
        f"UPDATE device_groups SET {', '.join(fields)} WHERE id = ?",
        values
    )
    conn.commit()
    conn.close()

    return get_group(group_id)


def delete_group(group_id: int) -> bool:
    """Удаление группы устройств"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM device_groups WHERE id = ?", (group_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )

    return True


def get_group(group_id: int) -> Dict[str, Any]:
    """Получение группы по ID"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, devices FROM device_groups WHERE id = ?", (group_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Группа не найдена"
        )

    group = {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "devices": json.loads(row["devices"])
    }

    # Добавляем информацию из кэша Zigbee2MQTT
    for group_id, zigbee_group in groups_cache.items():
        if zigbee_group.get("friendly_name") == group["name"]:
            group["zigbee_info"] = zigbee_group
            break

    return group

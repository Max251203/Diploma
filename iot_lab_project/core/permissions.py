# core/permissions.py

from enum import Enum


class RoleEnum(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


ROLE_LABELS = {
    RoleEnum.STUDENT: "Студент",
    RoleEnum.TEACHER: "Преподаватель",
    RoleEnum.ADMIN: "Администратор"
}

class Permission(str, Enum):
    MANAGE_USERS = "manage_users"
    VIEW_LOGS = "view_logs"
    ACCESS_DEVICES = "access_devices"
    ACCESS_LABS = "access_labs"

PERMISSION_LABELS = {
    Permission.MANAGE_USERS: "Управление пользователями",
    Permission.VIEW_LOGS: "Просмотр логов",
    Permission.ACCESS_DEVICES: "Доступ к устройствам",
    Permission.ACCESS_LABS: "Доступ к лабораторным"
}

ROLE_PERMISSIONS = {
    RoleEnum.STUDENT: {
        Permission.ACCESS_LABS,
        Permission.ACCESS_DEVICES,
        Permission.VIEW_LOGS,
    },
    RoleEnum.TEACHER: {
        Permission.ACCESS_LABS,
        Permission.ACCESS_DEVICES,
        Permission.VIEW_LOGS,
    },
    RoleEnum.ADMIN: {
        Permission.ACCESS_LABS,
        Permission.ACCESS_DEVICES,
        Permission.VIEW_LOGS,
        Permission.MANAGE_USERS,
    }
}

def get_role_label(role: str) -> str:
    try:
        return ROLE_LABELS[RoleEnum(role)]
    except Exception:
        return role

def get_all_roles() -> list[str]:
    return [r.value for r in RoleEnum]

def has_permission(role: str, permission: Permission) -> bool:
    try:
        return permission in ROLE_PERMISSIONS.get(RoleEnum(role), set())
    except Exception:
        return False
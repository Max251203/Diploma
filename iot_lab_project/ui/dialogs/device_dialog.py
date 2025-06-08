from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer
from typing import Dict
from core.adapters.base_adapter import BaseAdapter
from core.adapters.api_adapter import APIAdapter
import json
import requests


class DeviceDialog(QDialog):
    """Универсальное окно устройства (HA / API)"""

    def __init__(self, device: Dict, adapter: BaseAdapter, parent=None):
        super().__init__(parent)
        self.device = device
        self.adapter = adapter
        self.setWindowTitle(
            f"Устройство: {device.get('name', 'Без названия')}")
        self.setMinimumSize(600, 400)
        self._build_ui()
        self._load_state()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # === Блок информации ===
        info_frame = QWidget(objectName="deviceInfo")
        info_layout = QGridLayout(info_frame)

        info_layout.addWidget(QLabel("<b>Название:</b>"), 0, 0)
        info_layout.addWidget(QLabel(self.device.get("name", "—")), 0, 1)

        info_layout.addWidget(QLabel("<b>Модель:</b>"), 1, 0)
        info_layout.addWidget(QLabel(self.device.get("model", "—")), 1, 1)

        info_layout.addWidget(QLabel("<b>Производитель:</b>"), 2, 0)
        info_layout.addWidget(
            QLabel(self.device.get("manufacturer", "—")), 2, 1)

        device_id = self.device.get("id") or self.device.get("entity_id", "—")
        info_layout.addWidget(QLabel("<b>ID:</b>"), 3, 0)
        self.id_label = QLabel(device_id)
        info_layout.addWidget(self.id_label, 3, 1)

        layout.addWidget(info_frame)

        layout.addWidget(QLabel("<h3>Состояние:</h3>"))
        self.state_label = QLabel("Загрузка...")
        self.state_label.setWordWrap(True)
        layout.addWidget(self.state_label)

        # Панель управления (если доступно)
        if self._has_control():
            btn_row = QHBoxLayout()
            btn_on = QPushButton("Включить")
            btn_off = QPushButton("Выключить")
            btn_on.clicked.connect(lambda: self._send_command("on"))
            btn_off.clicked.connect(lambda: self._send_command("off"))
            btn_row.addWidget(btn_on)
            btn_row.addWidget(btn_off)
            layout.addLayout(btn_row)

        # История API
        self.history_label = QLabel("Загрузка истории...")
        layout.addWidget(QLabel("<h4>История (за последние 5):</h4>"))
        layout.addWidget(self.history_label)

    def _load_state(self):
        try:
            device_id = self.device.get("id") or self.device.get("entity_id")
            info = self.adapter.get_device_details(device_id)

            state = info.get("state", {})
            if isinstance(state, dict):
                text = ", ".join(f"{k}: {v}" for k, v in state.items())
            else:
                text = str(state)

            self.state_label.setText(text or "Нет данных")
        except Exception as e:
            self.state_label.setText("Ошибка: " + str(e))

        # История — только API
        if isinstance(self.adapter, APIAdapter):
            try:
                device_id = self.device.get(
                    "id") or self.device.get("entity_id")
                res = requests.get(
                    f"{self.adapter.url}/api/devices/{device_id}/history?limit=5",
                    headers={"x-api-key": self.adapter.api_key}
                )
                if res.ok:
                    history = res.json()
                    formatted = "\n".join(
                        f"{h['timestamp']}: {h['data']}" for h in history)
                    self.history_label.setText(formatted or "Пусто")
                else:
                    self.history_label.setText(
                        f"Ошибка истории ({res.status_code})")
            except Exception as e:
                self.history_label.setText("История: " + str(e))
        else:
            # Если это не API
            self.history_label.setText("Для Home Assistant недоступно")

    def _send_command(self, action: str):
        device_id = self.device.get("id") or self.device.get("entity_id")
        cmd = {}

        if action == "on":
            cmd = {"state": "ON"}
        elif action == "off":
            cmd = {"state": "OFF"}

        try:
            success = self.adapter.send_command(device_id, cmd)
            if success:
                self.state_label.setText("Команда отправлена")
                QTimer.singleShot(1000, self._load_state)
            else:
                self.state_label.setText("Ошибка отправки")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def _has_control(self) -> bool:
        model = (self.device.get("model") or "").lower()
        entity_id = self.device.get("id") or self.device.get("entity_id", "")
        if any(x in model for x in ["plug", "switch", "light", "relay"]):
            return True
        if entity_id.startswith(("switch.", "light.")):
            return True
        return False

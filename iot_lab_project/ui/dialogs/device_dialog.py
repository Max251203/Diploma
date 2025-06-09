from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import QTimer, Qt
from typing import Dict
from core.adapters.base_adapter import BaseAdapter
from core.adapters.ha_adapter import HAAdapter
from ui.widgets.entity_widget import EntityWidget, EntityState
from core.workers.state_loader import StateLoaderThread


class DeviceDialog(QDialog):
    """Диалог отображения информации об устройстве и его сущностях"""

    def __init__(self, device: Dict, adapter: BaseAdapter, parent=None):
        super().__init__(parent)
        self.device = device
        self.adapter = adapter
        self.entity_widgets = {}

        self.setWindowTitle(
            f"Устройство: {device.get('name', 'Без названия')}")
        self.setMinimumSize(600, 400)

        # Получаем список ID сущностей для HA устройств
        self.entity_ids = []
        if isinstance(adapter, HAAdapter) and "entities" in device:
            self.entity_ids = [e.get("entity_id")
                               for e in device['entities'] if e.get("entity_id")]

        self._build_ui()
        self._load_states()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # === Блок информации об устройстве ===
        info_frame = QFrame(objectName="deviceInfo")
        info_layout = QGridLayout(info_frame)

        info_layout.addWidget(QLabel("<b>Название:</b>"), 0, 0)
        info_layout.addWidget(QLabel(self.device.get("name", "—")), 0, 1)

        info_layout.addWidget(QLabel("<b>Производитель:</b>"), 1, 0)
        info_layout.addWidget(
            QLabel(self.device.get("manufacturer", "—")), 1, 1)

        info_layout.addWidget(QLabel("<b>Модель:</b>"), 2, 0)
        info_layout.addWidget(QLabel(self.device.get("model", "—")), 2, 1)

        device_id = self.device.get("id") or self.device.get("entity_id", "—")
        info_layout.addWidget(QLabel("<b>ID:</b>"), 3, 0)
        info_layout.addWidget(QLabel(device_id), 3, 1)

        # Кнопка обновления для датчиков
        has_sensors = False
        if "entities" in self.device:
            has_sensors = any(e.get("entity_id", "").startswith(("sensor.", "binary_sensor."))
                              for e in self.device['entities'])

        if has_sensors:
            refresh_btn = QPushButton("Опросить", objectName="refreshButton")
            refresh_btn.clicked.connect(self._load_states)
            info_layout.addWidget(refresh_btn, 4, 0, 1, 2)

        layout.addWidget(info_frame)

        # === Состояние для API устройств ===
        if "entities" not in self.device:
            layout.addWidget(QLabel("<h3>Состояние:</h3>"))
            state = self.device.get("state", {})
            if isinstance(state, dict):
                state_text = ", ".join(f"{k}: {v}" for k, v in state.items())
            else:
                state_text = str(state)

            self.state_label = QLabel(f"Состояние: {state_text}")
            self.state_label.setWordWrap(True)
            layout.addWidget(self.state_label)

            # Кнопки управления для API устройств
            if self._is_controllable():
                control_layout = QHBoxLayout()

                btn_on = QPushButton("Включить")
                btn_on.setObjectName("btnEntityOn")
                btn_on.clicked.connect(lambda: self._send_command("on"))

                btn_off = QPushButton("Выключить")
                btn_off.setObjectName("btnEntityOff")
                btn_off.clicked.connect(lambda: self._send_command("off"))

                control_layout.addWidget(btn_on)
                control_layout.addWidget(btn_off)
                layout.addLayout(control_layout)

            # История для API устройств
            if hasattr(self.adapter, "url") and hasattr(self.adapter, "api_key"):
                layout.addWidget(QLabel("<h4>История (за последние 5):</h4>"))
                self.history_label = QLabel("Загрузка истории...")
                layout.addWidget(self.history_label)
                self._load_history()

            return  # Для API устройств не отображаем сущности

        # === Список сущностей для HA устройств ===
        layout.addWidget(QLabel("<h3>Сущности и их состояния:</h3>"))

        self.panel_container = QWidget(objectName="entitiesBox")
        panel_layout = QVBoxLayout(self.panel_container)
        panel_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        scroll_content = QWidget()
        self.entity_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)

        panel_layout.addWidget(scroll_area)
        layout.addWidget(self.panel_container)

        for entity in self.device.get("entities", []):
            entity_id = entity.get("entity_id")
            if not entity_id:
                continue
            widget = EntityWidget(entity)
            widget.control_requested.connect(self._handle_control)
            self.entity_layout.addWidget(widget)
            self.entity_widgets[entity_id] = widget

        self.entity_layout.addStretch()

    def _is_controllable(self) -> bool:
        """Проверяет, можно ли управлять устройством"""
        # Проверяем по модели
        model = (self.device.get("model") or "").lower()
        if any(x in model for x in ["plug", "switch", "light", "relay"]):
            return True

        # Проверяем по ID
        entity_id = self.device.get("id") or self.device.get("entity_id", "")
        if entity_id.startswith(("switch.", "light.", "fan.")):
            return True

            # Проверяем по сущностям
        entities = self.device.get("entities", [])
        for entity in entities:
            entity_id = entity.get("entity_id", "")
            if entity_id.startswith(("switch.", "light.", "fan.")):
                return True

        return False

    def _send_command(self, action: str):
        """Отправляет команду управления устройством"""
        device_id = self.device.get("id") or self.device.get("entity_id")

        # Формируем команду в зависимости от типа устройства
        command = {}
        if action == "on":
            command = {"service": "turn_on", "data": {"state": "ON"}}
        elif action == "off":
            command = {"service": "turn_off", "data": {"state": "OFF"}}

        try:
            success = self.adapter.send_command(device_id, command)
            if success:
                self.state_label.setText("Команда отправлена")
                QTimer.singleShot(1000, self._load_states)
            else:
                self.state_label.setText("Ошибка отправки")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def _load_states(self):
        """Загружает состояния устройств"""
        # Для HA устройств
        if isinstance(self.adapter, HAAdapter) and self.entity_ids:
            for widget in self.entity_widgets.values():
                widget.set_state(EntityState.LOADING)

            self.state_loader = StateLoaderThread(
                self.adapter.entity_manager, self.entity_ids)
            self.state_loader.states_loaded.connect(self._update_states)
            self.state_loader.error.connect(self._handle_error)
            self.state_loader.start()

        # Для API устройств
        elif hasattr(self.adapter, "get_device_details") and hasattr(self, "state_label"):
            try:
                device_id = self.device.get(
                    "id") or self.device.get("entity_id")
                info = self.adapter.get_device_details(device_id)

                state = info.get("state", {})
                if isinstance(state, dict):
                    state_text = ", ".join(
                        f"{k}: {v}" for k, v in state.items())
                else:
                    state_text = str(state)

                self.state_label.setText(f"Состояние: {state_text}")

                # Обновляем историю, если есть
                if hasattr(self, "history_label"):
                    self._load_history()
            except Exception as e:
                self.state_label.setText(f"Ошибка: {e}")

    def _load_history(self):
        """Загружает историю устройства для API"""
        if not hasattr(self.adapter, "url") or not hasattr(self.adapter, "api_key"):
            return

        try:
            import requests
            device_id = self.device.get("id") or self.device.get("entity_id")
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
            self.history_label.setText(f"Ошибка: {e}")

    def _update_states(self, state_map: Dict[str, dict]):
        """Обновляет состояния сущностей для HA устройств"""
        for entity_id, widget in self.entity_widgets.items():
            widget.update_state(state_map.get(entity_id))

    def _handle_error(self, error: str):
        """Обрабатывает ошибки загрузки состояний"""
        QMessageBox.warning(
            self, "Ошибка", f"Не удалось получить состояния: {error}")

    def _handle_control(self, entity_id: str, action: str):
        """Обрабатывает команды управления сущностями для HA устройств"""
        try:
            if isinstance(self.adapter, HAAdapter):
                domain = entity_id.split('.')[0]
                self.adapter.ws.send_command("call_service", {
                    "domain": domain,
                    "service": action,
                    "service_data": {"entity_id": entity_id}
                })
                QTimer.singleShot(500, self._load_states)
            else:
                command = {"service": action}
                success = self.adapter.send_command(entity_id, command)
                if success:
                    QTimer.singleShot(500, self._load_states)
                else:
                    raise Exception("Ошибка отправки команды")
        except Exception as e:
            QMessageBox.warning(
                self, "Ошибка", f"Не удалось выполнить действие: {e}")

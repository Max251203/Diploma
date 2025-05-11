from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import QTimer
from typing import Dict
from core.workers.state_loader import StateLoaderThread
from ui.widgets.entity_widget import EntityWidget, EntityState

class DeviceDialog(QDialog):
    """Диалог отображения информации об устройстве и его сущностях"""

    def __init__(self, device: Dict, entity_manager, parent=None):
        super().__init__(parent)
        self.device = device
        self.entity_manager = entity_manager
        self.entity_widgets: Dict[str, EntityWidget] = {}

        self.setWindowTitle(f"Устройство: {device['name']}")
        self.setMinimumSize(600, 400)

        self.entity_ids = [e.get("entity_id") for e in device['entities'] if e.get("entity_id")]
        self._build_ui()
        self._load_states()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # === Блок информации об устройстве ===
        info_frame = QFrame(objectName="deviceInfo")
        info_layout = QGridLayout(info_frame)

        info_layout.addWidget(QLabel("<b>Название:</b>"), 0, 0)
        info_layout.addWidget(QLabel(self.device["name"]), 0, 1)
        info_layout.addWidget(QLabel("<b>Производитель:</b>"), 1, 0)
        info_layout.addWidget(QLabel(self.device["manufacturer"]), 1, 1)
        info_layout.addWidget(QLabel("<b>Модель:</b>"), 2, 0)
        info_layout.addWidget(QLabel(self.device["model"]), 2, 1)
        info_layout.addWidget(QLabel("<b>ID:</b>"), 3, 0)
        info_layout.addWidget(QLabel(self.device["id"]), 3, 1)

        if any(e.get("entity_id", "").startswith(("sensor.", "binary_sensor.")) for e in self.device['entities']):
            refresh_btn = QPushButton("Опросить", objectName="refreshButton")
            refresh_btn.clicked.connect(self._load_states)
            info_layout.addWidget(refresh_btn, 4, 0, 1, 2)

        layout.addWidget(info_frame)
        layout.addWidget(QLabel("<h3>Сущности и их состояния:</h3>"))

        # === Список сущностей ===
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

        for entity in self.device["entities"]:
            entity_id = entity.get("entity_id")
            if not entity_id:
                continue
            widget = EntityWidget(entity)
            widget.control_requested.connect(self._handle_control)
            self.entity_layout.addWidget(widget)
            self.entity_widgets[entity_id] = widget

        self.entity_layout.addStretch()

    def _load_states(self):
        for widget in self.entity_widgets.values():
            widget.set_state(EntityState.LOADING)

        self.state_loader = StateLoaderThread(self.entity_manager, self.entity_ids)
        self.state_loader.states_loaded.connect(self._update_states)
        self.state_loader.error.connect(self._handle_error)
        self.state_loader.start()

    def _update_states(self, state_map: Dict[str, dict]):
        for entity_id, widget in self.entity_widgets.items():
            widget.update_state(state_map.get(entity_id))

    def _handle_error(self, error: str):
        QMessageBox.warning(self, "Ошибка", f"Не удалось получить состояния: {error}")

    def _handle_control(self, entity_id: str, action: str):
        try:
            domain = entity_id.split('.')[0]
            self.entity_manager.ws.send_command("call_service", {
                "domain": domain,
                "service": action,
                "service_data": {"entity_id": entity_id}
            })
            QTimer.singleShot(500, self._load_states)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить действие: {e}")
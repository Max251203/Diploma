from enum import Enum
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap


class EntityState(Enum):
    LOADING = "loading"
    READY = "ready"
    UNAVAILABLE = "unavailable"


class EntityWidget(QFrame):
    """Виджет для отображения сущности"""
    control_requested = Signal(str, str)

    def __init__(self, entity, parent=None):
        super().__init__(parent)
        self.entity = entity
        self.entity_id = entity.get("entity_id", "unknown")
        self.entity_type = self.entity_id.split('.')[0]
        self.state_data = None

        self.setObjectName("entityItem")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setup_ui()
        self.set_state(EntityState.LOADING)

    def setup_ui(self):
        layout = QGridLayout(self)

        entity_name = self.entity.get(
            "original_name", self.entity.get("name", "—"))
        name_label = QLabel(f"<b>{entity_name}</b>")
        name_label.setObjectName("entityNameLabel")
        layout.addWidget(name_label, 0, 0, 1, 2)

        id_label = QLabel(f"ID: {self.entity_id}")
        id_label.setObjectName("entityIdLabel")
        layout.addWidget(id_label, 1, 0, 1, 2)

        self.state_label = QLabel()
        self.state_label.setObjectName("entityStateLabel")
        self.state_label.setFixedHeight(24)
        layout.addWidget(self.state_label, 2, 0, 1, 2)

        if self.entity_type in ["light", "switch", "fan"]:
            self._add_toggle_controls(layout)
        elif self.entity_type == "cover":
            self._add_cover_controls(layout)

    def set_state(self, state, data=None):
        if data is not None:
            self.state_data = data

        if state == EntityState.LOADING:
            self._show_loading_state()
        elif state == EntityState.UNAVAILABLE:
            self._show_unavailable_state()
        elif state == EntityState.READY and self.state_data:
            self._show_entity_state()

    def update_state(self, state_data):
        if not state_data:
            self.set_state(EntityState.UNAVAILABLE)
        else:
            self.set_state(EntityState.READY, state_data)

    def _show_loading_state(self):
        self.state_label.setText("Состояние: 🔄 Загрузка...")
        self.state_label.setProperty("stateType", "loading")

    def _show_unavailable_state(self):
        self.state_label.setText("Состояние: недоступно")
        self.state_label.setProperty("stateType", "unavailable")

    def _show_entity_state(self):
        state = self.state_data.get("state", "unknown")
        attributes = self.state_data.get("attributes", {})
        formatted = self._format_state(state, attributes)
        self.state_label.setText(f"Состояние: {formatted}")
        self.state_label.setProperty("stateType", "normal")

    def _format_state(self, state, attributes):
        if self.entity_type == "sensor":
            unit = attributes.get("unit_of_measurement", "")
            return f"{state} {unit}"
        elif self.entity_type in ["binary_sensor", "switch", "light"]:
            return "Включено" if state == "on" else "Выключено"
        elif self.entity_type == "cover":
            return "Открыто" if state == "open" else "Закрыто"
        else:
            return state

    def _add_toggle_controls(self, layout):
        control_frame = QFrame()
        control_frame.setObjectName("entityControlFrame")
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 5, 0, 0)

        btn_on = QPushButton("Включить")
        btn_on.setObjectName("btnEntityOn")

        btn_off = QPushButton("Выключить")
        btn_off.setObjectName("btnEntityOff")

        btn_on.clicked.connect(
            lambda: self.control_requested.emit(self.entity_id, "turn_on"))
        btn_off.clicked.connect(
            lambda: self.control_requested.emit(self.entity_id, "turn_off"))

        control_layout.addWidget(btn_on)
        control_layout.addWidget(btn_off)

        layout.addWidget(control_frame, 3, 0, 1, 2)

    def _add_cover_controls(self, layout):
        control_frame = QFrame()
        control_frame.setObjectName("entityControlFrame")
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 5, 0, 0)

        btn_open = QPushButton("Открыть")
        btn_open.setObjectName("btnEntityOn")

        btn_close = QPushButton("Закрыть")
        btn_close.setObjectName("btnEntityOff")

        btn_open.clicked.connect(
            lambda: self.control_requested.emit(self.entity_id, "open_cover"))
        btn_close.clicked.connect(
            lambda: self.control_requested.emit(self.entity_id, "close_cover"))

        control_layout.addWidget(btn_open)
        control_layout.addWidget(btn_close)

        layout.addWidget(control_frame, 3, 0, 1, 2)

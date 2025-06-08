from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, Signal


class DeviceCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, device_data: dict, parent=None):
        super().__init__(parent)
        self.device = device_data
        self.setObjectName("deviceCard")
        self.setCursor(Qt.PointingHandCursor)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        inner = QWidget(objectName="deviceInner")
        layout = QVBoxLayout(inner)
        layout.setAlignment(Qt.AlignTop)

        layout.addWidget(
            QLabel(f"<b>{self.device.get('name', 'Без названия')}</b>"))
        model = self.device.get("model", "—")
        manuf = self.device.get("manufacturer", "")
        layout.addWidget(QLabel(f"{manuf} {model}".strip()))

        state = self.device.get("state", {})
        if isinstance(state, dict):
            state_text = ", ".join(f"{k}: {v}" for k, v in state.items())
        else:
            state_text = str(state)

        layout.addWidget(QLabel(f"Состояние: {state_text}"))
        layout.addWidget(
            QLabel(f"ID: {self.device.get('id') or self.device.get('entity_id')}"))

        outer.addWidget(inner)
        self.setMinimumSize(200, 120)
        self.setMaximumHeight(150)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.device)

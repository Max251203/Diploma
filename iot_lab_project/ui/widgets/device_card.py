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

        # Название устройства
        layout.addWidget(
            QLabel(f"<b>{self.device.get('name', 'Без названия')}</b>"))

        # Модель и производитель
        model = self.device.get("model", "—")
        manuf = self.device.get("manufacturer", "")
        layout.addWidget(QLabel(f"{manuf} {model}".strip()))

        # Количество сущностей или состояние
        entities = self.device.get("entities", [])
        if entities:
            layout.addWidget(QLabel(f"Сущности: {len(entities)}"))
        else:
            # Состояние для API устройств
            state = self.device.get("state", {})
            if isinstance(state, dict) and state:
                state_text = ", ".join(f"{k}: {v}" for k, v in state.items())
                self.state_label = QLabel(f"Состояние: {state_text}")
                layout.addWidget(self.state_label)
            elif isinstance(state, str) and state:
                self.state_label = QLabel(f"Состояние: {state}")
                layout.addWidget(self.state_label)

        outer.addWidget(inner)
        self.setMinimumSize(200, 120)
        self.setMaximumHeight(150)

    def update_state(self, state_data):
        """Обновляет отображение состояния устройства"""
        if not hasattr(self, 'state_label') or not state_data:
            return

        state = state_data.get("state", {})
        if isinstance(state, dict):
            state_text = ", ".join(f"{k}: {v}" for k, v in state.items())
        else:
            state_text = str(state)

        self.state_label.setText(f"Состояние: {state_text}")

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.device)

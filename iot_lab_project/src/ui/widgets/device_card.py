from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal

class DeviceCard(QFrame):
    """Карточка для отображения устройства"""
    clicked = Signal(dict)

    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
        self.setObjectName("deviceCard")
        self.setup_ui()

    def setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)

        name_label = QLabel(f"<b>{self.device['name']}</b>")
        layout.addWidget(name_label)

        info = f"{self.device['manufacturer']} {self.device['model']}"
        layout.addWidget(QLabel(info))

        entities_count = len(self.device['entities'])
        layout.addWidget(QLabel(f"Сущности: {entities_count}"))

        self.setMinimumSize(200, 120)
        self.setMaximumHeight(150)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.device)
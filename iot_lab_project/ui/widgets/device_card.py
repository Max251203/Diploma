from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, Signal

class DeviceCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
        self.setObjectName("deviceCard")
        self.setCursor(Qt.PointingHandCursor)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        inner = QWidget(objectName="deviceInner")
        layout = QVBoxLayout(inner)
        layout.setAlignment(Qt.AlignTop)

        layout.addWidget(QLabel(f"<b>{self.device['name']}</b>"))
        layout.addWidget(QLabel(f"{self.device['manufacturer']} {self.device['model']}"))
        layout.addWidget(QLabel(f"Сущности: {len(self.device['entities'])}"))

        outer.addWidget(inner)
        self.setMinimumSize(200, 120)
        self.setMaximumHeight(150)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.device)
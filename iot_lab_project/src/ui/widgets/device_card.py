from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
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

        # Внешний layout для deviceCard
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)  # создаёт "рамку"

        # Внутренний контейнер
        inner_widget = QWidget()
        inner_widget.setObjectName("deviceInner")
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        name_label = QLabel(f"<b>{self.device['name']}</b>")
        inner_layout.addWidget(name_label)

        info = f"{self.device['manufacturer']} {self.device['model']}"
        inner_layout.addWidget(QLabel(info))

        entities_count = len(self.device['entities'])
        inner_layout.addWidget(QLabel(f"Сущности: {entities_count}"))

        outer_layout.addWidget(inner_widget)

        self.setMinimumSize(200, 120)
        self.setMaximumHeight(150)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.device)
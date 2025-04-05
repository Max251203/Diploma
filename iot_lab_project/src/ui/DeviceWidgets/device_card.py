from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal

class DeviceCard(QFrame):
    """Карточка для отображения устройства"""
    clicked = Signal(dict)  # Сигнал, передающий данные устройства при клике
    
    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
        self.setup_ui()
        
    def setup_ui(self):
        # Устанавливаем objectName для применения стилей из QSS
        self.setObjectName("DeviceCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setCursor(Qt.PointingHandCursor)
        
        # Создаем layout
        layout = QVBoxLayout(self)
        
        # Название устройства
        name_label = QLabel(f"<b>{self.device['name']}</b>")
        name_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(name_label)
        
        # Производитель и модель
        info_label = QLabel(f"{self.device['manufacturer']} {self.device['model']}")
        layout.addWidget(info_label)
        
        # Количество сущностей
        entities_label = QLabel(f"Сущности: {len(self.device['entities'])}")
        layout.addWidget(entities_label)
        
        # Минимальный размер для карточки
        self.setMinimumSize(200, 120)
        self.setMaximumHeight(150)
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.device)
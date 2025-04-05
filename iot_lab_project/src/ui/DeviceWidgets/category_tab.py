from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PySide6.QtCore import Signal
from ui.DeviceWidgets.flow_layout import FlowLayout
from ui.DeviceWidgets.device_card import DeviceCard

class CategoryTab(QWidget):
    """Вкладка для категории устройств"""
    deviceSelected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Основной layout
        self.main_layout = QVBoxLayout(self)
        
        # Создаем область прокрутки
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # Создаем контейнер для карточек
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        
        # Добавляем flow layout для карточек
        self.flow_layout = FlowLayout()
        self.container_layout.addLayout(self.flow_layout)
        self.container_layout.addStretch()
        
        self.scroll_area.setWidget(self.container)
        self.main_layout.addWidget(self.scroll_area)
    
    def set_devices(self, devices):
        """Устанавливает устройства для отображения"""
        # Очищаем текущие карточки
        for i in reversed(range(self.flow_layout.count())): 
            widget = self.flow_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Добавляем новые карточки
        for device in devices:
            card = DeviceCard(device)
            card.clicked.connect(self.deviceSelected.emit)
            self.flow_layout.addWidget(card)
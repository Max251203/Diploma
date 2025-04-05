# Исправленная версия categorized_devices_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                              QListWidgetItem, QStackedWidget, QScrollArea)
from PySide6.QtCore import Signal, Qt
from ui.DeviceWidgets.flow_layout import FlowLayout
from ui.DeviceWidgets.device_card import DeviceCard

class CategorizedDevicesWidget(QWidget):
    """Виджет для отображения устройств по категориям с вертикальным списком категорий"""
    deviceSelected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Инициализируем словарь для устройств
        self.devices_by_category = {}
        self.setup_ui()
        
    def setup_ui(self):
        # Основной горизонтальный layout
        self.main_layout = QHBoxLayout(self)
        
        # Список категорий слева
        self.category_list = QListWidget()
        self.category_list.setObjectName("categoryList")
        self.category_list.setMinimumWidth(180)
        self.category_list.setMaximumWidth(220)
        self.main_layout.addWidget(self.category_list)
        
        # Контейнер для устройств справа
        self.device_container = QWidget()
        self.device_container.setObjectName("deviceContainer")
        self.device_scroll = QScrollArea()
        self.device_scroll.setWidgetResizable(True)
        self.device_scroll.setWidget(self.device_container)
        self.main_layout.addWidget(self.device_scroll)
        
        # Flow layout для устройств
        self.device_layout = QVBoxLayout(self.device_container)
        self.flow_layout = FlowLayout()
        self.device_layout.addLayout(self.flow_layout)
        self.device_layout.addStretch()
        
        # Категории
        self.categories = ["Датчики", "Исполнительные устройства", "Системные", "Прочее"]
        for category in self.categories:
            item = QListWidgetItem(category)
            self.category_list.addItem(item)
        
        # Подключаем сигнал изменения выбранной категории
        self.category_list.currentRowChanged.connect(self.change_category)
        self.category_list.setCurrentRow(0)  # Выбираем первую категорию по умолчанию
    
    def change_category(self, index):
        """Изменяет отображаемую категорию устройств"""
        if index < 0 or index >= len(self.categories):
            return
            
        category = self.categories[index]
        self.display_category(category)
    
    def display_category(self, category):
        """Отображает устройства выбранной категории"""
        # Очищаем текущие карточки
        self._clear_device_cards()
        
        # Если категория есть в словаре, отображаем устройства
        if category in self.devices_by_category:
            devices = self.devices_by_category[category]
            for device in devices:
                self._add_device_card(device)
    
    def update_devices(self, categorized_devices):
        """Обновляет списки устройств по категориям"""
        # Сохраняем устройства по категориям
        self.devices_by_category = categorized_devices
        
        # Отображаем текущую выбранную категорию
        current_row = self.category_list.currentRow()
        if current_row >= 0:
            self.change_category(current_row)
    
    def _clear_device_cards(self):
        """Очищает все карточки устройств"""
        for i in reversed(range(self.flow_layout.count())): 
            widget = self.flow_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
    
    def _add_device_card(self, device):
        """Добавляет карточку устройства"""
        card = DeviceCard(device)
        card.clicked.connect(self.deviceSelected.emit)
        self.flow_layout.addWidget(card)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QListWidgetItem, QScrollArea, QLabel)
from PySide6.QtCore import Signal, Qt
from ui.widgets.flow_layout import FlowLayout
from ui.widgets.device_card import DeviceCard

class DevicesPanel(QWidget):
    """Панель отображения устройств по категориям"""
    device_selected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices_by_category = {}
        self.categories = ["Датчики", "Исполнительные устройства", "Системные", "Прочее"]
        self.setup_ui()
    
    def setup_ui(self):
        # Основной горизонтальный layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Список категорий
        self.category_list = QListWidget()
        self.category_list.setObjectName("categoryList")
        self.category_list.setMinimumWidth(180)
        self.category_list.setMaximumWidth(220)
        
        for category in self.categories:
            item = QListWidgetItem(category)
            self.category_list.addItem(item)
        
        self.category_list.currentRowChanged.connect(self._on_category_changed)
        layout.addWidget(self.category_list)
        
        # Создаем контейнер для устройств
        self.device_container = QWidget()
        self.device_container.setObjectName("deviceContainer")
        
        # Создаем layout для контейнера
        self.device_layout = QVBoxLayout(self.device_container)
        self.device_layout.setContentsMargins(10, 10, 10, 10)
        
        # Создаем flow layout для карточек устройств
        self.flow_layout = FlowLayout()
        self.device_layout.addLayout(self.flow_layout)
        self.device_layout.addStretch()
        
        # Создаем область прокрутки
        self.device_scroll = QScrollArea()
        self.device_scroll.setObjectName("deviceScroll")
        self.device_scroll.setWidgetResizable(True)
        
        # Устанавливаем контейнер в область прокрутки
        self.device_scroll.setWidget(self.device_container)
        
        # Добавляем область прокрутки в основной layout
        layout.addWidget(self.device_scroll)
        
        # Выбираем первую категорию
        self.category_list.setCurrentRow(0)
    
    def update_devices(self, categorized_devices):
        """Обновляет список устройств"""
        self.devices_by_category = categorized_devices
        self._display_current_category()
    
    def _on_category_changed(self, index):
        """Обработчик изменения выбранной категории"""
        self._display_current_category()
    
    def _display_current_category(self):
        """Отображает устройства текущей категории"""
        # Очищаем текущие карточки
        self._clear_device_cards()
        
        # Получаем текущую категорию
        index = self.category_list.currentRow()
        if index < 0 or index >= len(self.categories):
            return
            
        category = self.categories[index]
        
        # Отображаем устройства категории
        if category in self.devices_by_category:
            for device in self.devices_by_category[category]:
                self._add_device_card(device)
    
    def clear_devices(self):
        """Очищает все устройства"""
        self._clear_device_cards()

    def show_loading_indicator(self, message):
        """Показывает индикатор загрузки"""
        loading_label = QLabel(message)
        loading_label.setObjectName("loadingLabel")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("font-weight: bold; color: orange; font-size: 14px;")
        self.flow_layout.addWidget(loading_label)

    def _clear_device_cards(self):
        """Очищает все карточки устройств"""
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _add_device_card(self, device):
        """Добавляет карточку устройства"""
        card = DeviceCard(device)
        card.clicked.connect(self.device_selected.emit)
        self.flow_layout.addWidget(card)
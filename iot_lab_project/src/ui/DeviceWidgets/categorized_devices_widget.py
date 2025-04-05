from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Signal
from ui.DeviceWidgets.category_tab import CategoryTab

class CategorizedDevicesWidget(QWidget):
    """Виджет для отображения устройств по категориям"""
    deviceSelected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        self.category_tabs = {}
        
        # Создаем вкладки для категорий
        categories = ["Датчики", "Исполнительные устройства", "Системные", "Прочее"]
        for category in categories:
            tab = CategoryTab()
            tab.deviceSelected.connect(self.deviceSelected.emit)
            self.category_tabs[category] = tab
            self.tab_widget.addTab(tab, category)
    
    def update_devices(self, categorized_devices):
        """Обновляет списки устройств по категориям"""
        for category, devices in categorized_devices.items():
            if category in self.category_tabs:
                self.category_tabs[category].set_devices(devices)
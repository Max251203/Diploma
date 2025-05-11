from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QScrollArea, QLabel
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Signal, Qt
from ui.widgets.flow_layout import FlowLayout
from ui.widgets.device_card import DeviceCard

class DevicesPanel(QWidget):
    device_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices_by_category = {}
        self.categories = ["Датчики", "Исполнительные устройства", "Системные", "Прочее"]
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.category_list = QListWidget(objectName="categoryList")
        self.category_list.setMinimumWidth(180)
        self.category_list.setMaximumWidth(220)
        layout.addWidget(self.category_list)

        icons = {
            "Датчики": "sensor.png",
            "Исполнительные устройства": "actuator.png",
            "Системные": "system.png",
            "Прочее": "other.png"
        }
        for cat in self.categories:
            item = QListWidgetItem(QIcon(f":/icon/icons/{icons[cat]}"), cat)
            self.category_list.addItem(item)

        self.category_list.currentRowChanged.connect(self._show_category)

        panel = QWidget(objectName="devicesBox")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        self.scroll_content = QWidget()
        self.flow_layout = FlowLayout(self.scroll_content)
        scroll_area.setWidget(self.scroll_content)

        panel_layout.addWidget(scroll_area)
        layout.addWidget(panel)

        self.category_list.setCurrentRow(0)

    def update_devices(self, categorized_devices):
        self.devices_by_category = categorized_devices
        self._show_category()

    def _show_category(self, index=None):
        self._clear()
        index = self.category_list.currentRow()
        if index < 0 or index >= len(self.categories):
            return
        cat = self.categories[index]
        for dev in self.devices_by_category.get(cat, []):
            card = DeviceCard(dev)
            card.clicked.connect(self.device_selected.emit)
            self.flow_layout.addWidget(card)

    def show_loading_indicator(self, message):
        label = QLabel()
        label.setObjectName("loadingLabel")
        label.setAlignment(Qt.AlignCenter)
        label.setPixmap(QPixmap(":/icon/icons/loading.png"))
        label.setToolTip(message)
        self.flow_layout.addWidget(label)

    def clear_devices(self):
        self._clear()

    def _clear(self):
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QScrollArea, QLabel
)
from PySide6.QtGui import QIcon, QPixmap
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
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        # === Список категорий ===
        self.category_list = QListWidget()
        self.category_list.setObjectName("categoryList")
        self.category_list.setMinimumWidth(180)
        self.category_list.setMaximumWidth(220)

        self.category_icons = {
            "Датчики": QIcon(":/icon/icons/sensor.png"),
            "Исполнительные устройства": QIcon(":/icon/icons/actuator.png"),
            "Системные": QIcon(":/icon/icons/system.png"),
            "Прочее": QIcon(":/icon/icons/other.png")
        }

        for category in self.categories:
            item = QListWidgetItem(self.category_icons[category], category)
            self.category_list.addItem(item)

        self.category_list.currentRowChanged.connect(self._on_category_changed)
        main_layout.addWidget(self.category_list)

        # === Центральная панель с устройствами ===
        panel_container = QWidget()
        panel_container.setObjectName("devicesBox")
        panel_layout = QVBoxLayout(panel_container)
        panel_layout.setContentsMargins(10, 10, 10, 10)

        # === ScrollArea внутри панели ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        # === Вложенный контейнер с FlowLayout ===
        scroll_content = QWidget()
        self.flow_layout = FlowLayout(scroll_content)

        scroll_area.setWidget(scroll_content)
        panel_layout.addWidget(scroll_area)

        self.panel_container = panel_container
        self.scroll_content = scroll_content

        main_layout.addWidget(panel_container)

        # Выбираем первую категорию
        self.category_list.setCurrentRow(0)

    def update_devices(self, categorized_devices):
        """Обновляет список устройств"""
        self.devices_by_category = categorized_devices
        self._display_current_category()

    def _on_category_changed(self, index):
        self._display_current_category()

    def _display_current_category(self):
        self._clear_device_cards()

        index = self.category_list.currentRow()
        if index < 0 or index >= len(self.categories):
            return

        category = self.categories[index]
        if category in self.devices_by_category:
            for device in self.devices_by_category[category]:
                self._add_device_card(device)

    def clear_devices(self):
        self._clear_device_cards()

    def show_loading_indicator(self, message):
        """Показывает индикатор загрузки"""
        loading_label = QLabel()
        loading_label.setObjectName("loadingLabel")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setPixmap(QPixmap(":/icon/icons/loading.png"))
        loading_label.setToolTip(message)
        self.flow_layout.addWidget(loading_label)

    def _clear_device_cards(self):
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_device_card(self, device):
        card = DeviceCard(device)
        card.clicked.connect(self.device_selected.emit)
        self.flow_layout.addWidget(card)
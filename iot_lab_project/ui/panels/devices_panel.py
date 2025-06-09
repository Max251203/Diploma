from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, Signal
from ui.widgets.flow_layout import FlowLayout
from ui.widgets.device_card import DeviceCard
from core.logger import get_logger


class DevicesPanel(QWidget):
    device_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices_by_category = {}
        self.categories = []
        self.logger = get_logger()
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.category_list = QListWidget(objectName="categoryList")
        self.category_list.setMinimumWidth(180)
        self.category_list.setMaximumWidth(220)
        self.category_list.currentRowChanged.connect(self._show_category)
        layout.addWidget(self.category_list)

        # Правая часть: скролл с карточками
        self.panel = QWidget(objectName="devicesBox")
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)

        self.scroll_content = QWidget()
        self.flow_layout = FlowLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        panel_layout.addWidget(self.scroll_area)
        layout.addWidget(self.panel)

    def update_devices(self, categorized_devices: dict):
        """Обновить устройства, сгруппированные по категориям"""
        self.logger.info(
            f"Обновление панели устройств: получено {len(categorized_devices)} категорий")
        self.devices_by_category = categorized_devices

        # Определяем порядок категорий
        ordered_categories = []

        # Сначала добавляем категории в определенном порядке, если они есть
        for category in ["Датчики", "Исполнительные устройства", "Системные"]:
            if category in categorized_devices:
                ordered_categories.append(category)

        # Затем добавляем все остальные категории, кроме "Прочее"
        for category in categorized_devices:
            if category not in ordered_categories and category != "Прочее":
                ordered_categories.append(category)

        # В конце добавляем "Прочее", если есть
        if "Прочее" in categorized_devices:
            ordered_categories.append("Прочее")

        self.categories = ordered_categories

        self.category_list.clear()
        for cat in self.categories:
            icon = self._get_icon_for_category(cat)
            item = QListWidgetItem(icon, cat)
            self.category_list.addItem(item)
            self.logger.info(
                f"Добавлена категория: {cat} с {len(categorized_devices[cat])} устройствами")

        # Первая категория по умолчанию
        if self.categories:
            self.category_list.setCurrentRow(0)
        else:
            self.logger.warning("Не получено ни одной категории устройств")

    def _get_icon_for_category(self, category: str) -> QIcon:
        # Прямое сопоставление категорий с иконками
        if category == "Системные":
            return QIcon(":/icon/icons/system.png")
        elif category == "Датчики":
            return QIcon(":/icon/icons/sensor.png")
        elif category == "Исполнительные устройства":
            return QIcon(":/icon/icons/actuator.png")
        elif category == "Группы":
            return QIcon(":/icon/icons/group.png")
        elif category == "Прочее":
            return QIcon(":/icon/icons/other.png")

        # Если точное совпадение не найдено, используем поиск по ключевым словам
        cat = category.lower()
        if "датчик" in cat or "sensor" in cat:
            return QIcon(":/icon/icons/sensor.png")
        elif "исполнитель" in cat or "реле" in cat or "переключатель" in cat or "actuator" in cat:
            return QIcon(":/icon/icons/actuator.png")
        elif "система" in cat or "system" in cat:
            return QIcon(":/icon/icons/system.png")
        elif "группа" in cat or "group" in cat:
            return QIcon(":/icon/icons/group.png")
        else:
            return QIcon(":/icon/icons/other.png")

    def _show_category(self, index=None):
        self._clear()

        if index is None or index < 0 or index >= len(self.categories):
            return

        category = self.categories[index]
        devices = self.devices_by_category.get(category, [])
        for device in devices:
            card = DeviceCard(device)
            card.clicked.connect(self.device_selected.emit)
            self.flow_layout.addWidget(card)

    def show_loading_indicator(self, message="Загрузка..."):
        self._clear()
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

    def update_device_state(self, device_id: str, state_data: dict):
        """Обновляет состояние устройства по его ID"""
        for i in range(self.flow_layout.count()):
            widget = self.flow_layout.itemAt(i).widget()
            if isinstance(widget, DeviceCard):
                if widget.device.get("id") == device_id or widget.device.get("entity_id") == device_id:
                    widget.update_state(state_data)
                    break

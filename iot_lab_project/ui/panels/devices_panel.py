from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QPushButton, QMessageBox
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, Signal, QTimer
from ui.widgets.flow_layout import FlowLayout
from ui.widgets.device_card import DeviceCard
from core.logger import get_logger
from core.api import api_client
from core.api.api_worker import GetDevicesWorker


class DevicesPanel(QWidget):
    device_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices_by_category = {}
        self.categories = []
        self.logger = get_logger()
        self._workers = []  # Список для хранения рабочих потоков
        self._build_ui()

        # Запускаем таймер для отложенной загрузки устройств
        QTimer.singleShot(1000, self.refresh_devices)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.category_list = QListWidget(objectName="categoryList")
        self.category_list.setMinimumWidth(180)
        self.category_list.setMaximumWidth(220)
        self.category_list.currentRowChanged.connect(self._show_category)
        layout.addWidget(self.category_list)

        # Правая панель: скролл с карточками
        self.panel = QWidget(objectName="devicesBox")
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)

        # Кнопка обновления
        refresh_btn = QPushButton("Обновить устройства")
        refresh_btn.clicked.connect(self.refresh_devices)
        panel_layout.addWidget(refresh_btn)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)

        self.scroll_content = QWidget()
        self.flow_layout = FlowLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        panel_layout.addWidget(self.scroll_area)
        layout.addWidget(self.panel)

    def refresh_devices(self):
        """Обновление списка устройств"""
        try:
            # Показываем индикатор загрузки
            self.clear_devices()
            self.show_loading_indicator("Загрузка устройств...")

            # Проверяем подключение к API
            if not api_client.is_connected():
                self.logger.warning("Нет активного подключения к API")
                self.show_loading_indicator("Нет подключения к серверу")
                return

            # Используем API Worker для асинхронной загрузки
            worker = GetDevicesWorker(api_client)
            worker.result_ready.connect(self._on_devices_loaded)
            worker.error_occurred.connect(self._show_error)
            self._workers.append(worker)  # Сохраняем ссылку на поток
            worker.start()

            self.logger.info("Запрос на получение устройств отправлен")
        except Exception as e:
            self.logger.error(f"Ошибка при запросе устройств: {e}")
            self.show_loading_indicator(f"Ошибка: {e}")

    def _on_devices_loaded(self, devices):
        """Обработка загруженных устройств"""
        if not devices:
            self.clear_devices()
            self.show_loading_indicator("Нет доступных устройств")
            self.logger.warning(
                "Не удалось загрузить устройства или список пуст")
            return

        # Преобразуем устройства в формат, понятный для DevicesPanel
        categorized_devices = self._categorize_devices(devices)

        # Обновляем панель устройств
        self.update_devices(categorized_devices)
        self.logger.success(
            f"Устройства успешно загружены: {len(devices)} устройств")

        # Очищаем завершенные рабочие потоки
        self._cleanup_workers()

    def _categorize_devices(self, devices):
        """Категоризация устройств"""
        categories = {
            "Датчики": [],
            "Исполнительные устройства": [],
            "Системные": [],
            "Прочее": []
        }

        for device_id, device in devices.items():
            # Добавляем ID устройства в данные
            device_data = dict(device)
            device_data["id"] = device_id

            # Определяем категорию устройства
            category = self._determine_device_category(device_data)
            categories[category].append(device_data)

        return categories

    def _determine_device_category(self, device):
        """Определение категории устройства"""
        # Проверяем по модели
        model = (device.get("model") or "").lower()
        name = (device.get("name") or "").lower()

        # Проверяем по типу устройства
        if "sensor" in model or "temp" in model or "hum" in model or "motion" in model:
            return "Датчики"

        if "switch" in model or "relay" in model or "light" in model or "plug" in model:
            return "Исполнительные устройства"

        # Проверяем по имени
        if "sensor" in name or "датчик" in name:
            return "Датчики"

        if "switch" in name or "relay" in name or "light" in name or "plug" in name:
            return "Исполнительные устройства"

        # Проверяем по состоянию
        state = device.get("state", {})
        if isinstance(state, dict):
            if "temperature" in state or "humidity" in state or "motion" in state:
                return "Датчики"

            if "state" in state and state["state"] in ["ON", "OFF"]:
                return "Исполнительные устройства"

        # По умолчанию
        return "Прочее"

    def update_devices(self, categorized_devices: dict):
        """Обновить устройства, сгруппированные по категориям"""
        self.logger.info(
            f"Обновление панели устройств: получено {len(categorized_devices)} категорий")
        self.devices_by_category = categorized_devices

        # Определяем порядок категорий
        ordered_categories = []

        # Сначала добавляем категории в определенном порядке, если они есть
        for category in ["Датчики", "Исполнительные устройства", "Системные"]:
            if category in categorized_devices and categorized_devices[category]:
                ordered_categories.append(category)

        # Затем добавляем все остальные категории, кроме "Прочее"
        for category in categorized_devices:
            if category not in ordered_categories and category != "Прочее" and categorized_devices[category]:
                ordered_categories.append(category)

        # В конце добавляем "Прочее", если есть
        if "Прочее" in categorized_devices and categorized_devices["Прочее"]:
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
            self.show_loading_indicator("Нет доступных устройств")

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
        label.setText(message)
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

    def _show_error(self, error: str):
        """Отображение ошибки"""
        self.logger.error(f"Ошибка при загрузке устройств: {error}")
        self.show_loading_indicator(f"Ошибка: {error}")

        # Очищаем завершенные рабочие потоки
        self._cleanup_workers()

    def _cleanup_workers(self):
        """Очистка завершенных рабочих потоков"""
        for worker in self._workers[:]:
            if not worker.isRunning():
                worker.deleteLater()
                self._workers.remove(worker)

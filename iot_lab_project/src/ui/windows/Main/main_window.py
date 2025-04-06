from PySide6.QtWidgets import QMainWindow, QLabel, QMessageBox, QDialog
from PySide6.QtCore import QFile, QTextStream
from ui.windows.Main.main_ui import Ui_MainWindow 
from ui.windows.Connection.connection_dialog import ConnectionDialog
from ui.windows.Device.device_dialog import DeviceDialog
from ui.panels.devices_panel import DevicesPanel
from core.db.connection_db import HAConnectionDB
from core.workers.connection_worker import ConnectionWorker
from core.workers.device_loader import DeviceLoader
from utils.logger import Logger

class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setGeometry(100, 100, 900, 600)
        self.setWindowTitle("IoT Лаборатория")

        # Инициализация логгера
        self.logger = Logger(console_output=False)

        # Инициализация переменных
        self.ws_client = None
        self.entity_manager = None
        self.device_manager = None
        self.selected_connection = None
        self.db = HAConnectionDB()

        # Настройка интерфейса
        self.setup_ui()

        # Загрузка подключений
        self.load_connections()
        self.update_connection_status(disconnected=True)

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.ui.btnConnectSettings.clicked.connect(self.open_connection_settings)
        self.ui.btnConnect.clicked.connect(self.connect_to_selected)
        self.ui.btnGetDevices.clicked.connect(self.load_devices)

        # Настройка панели устройств
        self.setup_devices_panel()

    def setup_devices_panel(self):
        """Настройка панели устройств"""
        layout = self.ui.layoutDeviceList
        layout.setContentsMargins(0, 0, 0, 0)

        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.devices_panel = DevicesPanel()
        self.devices_panel.device_selected.connect(self.open_device_details)
        layout.addWidget(self.devices_panel)

    def load_connections(self):
        """Загружает список подключений в комбобокс"""
        current_id = self.selected_connection["id"] if self.selected_connection else None
        connections = self.db.get_all_connections()

        self.ui.comboConnections.clear()
        selected_index = 0

        for index, conn in enumerate(connections):
            self.ui.comboConnections.addItem(conn["name"], conn)
            if conn["id"] == current_id:
                selected_index = index

        self.ui.comboConnections.setCurrentIndex(selected_index)

    def open_connection_settings(self):
        """Открывает диалог настроек подключения"""
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_connections()

    def connect_to_selected(self):
        """Подключается к выбранному серверу Home Assistant"""
        index = self.ui.comboConnections.currentIndex()
        if index == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение из списка.")
            return

        connection_data = self.ui.comboConnections.itemData(index)
        if not connection_data:
            QMessageBox.warning(self, "Ошибка", "Данные подключения не найдены.")
            return

        self.selected_connection = connection_data
        self.ui.connectionStatus.setText("🔄 Подключение...")

        self.logger.info("Подключение к Home Assistant...")
        self._update_logs()

        self.connection_worker = ConnectionWorker(
            self.selected_connection["url"], 
            self.selected_connection["token"]
        )
        self.connection_worker.connection_success.connect(self.on_connected)
        self.connection_worker.connection_failed.connect(self.on_connection_error)
        self.connection_worker.start()

    def on_connected(self, ws_client, rest_client, entity_manager, device_manager, ws_url):
        """Обработчик успешного подключения"""
        self.ws_client = ws_client
        self.rest_client = rest_client
        self.entity_manager = entity_manager
        self.device_manager = device_manager

        self.update_connection_status(success=True)
        self.logger.success(f"Подключение успешно установлено: {ws_url}")
        self._update_logs()

    def on_connection_error(self, error_message):
        """Обработчик ошибки подключения"""
        self.update_connection_status(disconnected=True)
        self.logger.error(f"Ошибка подключения: {error_message}")
        self._update_logs()

    def update_connection_status(self, success=False, disconnected=False):
        """Обновляет статус подключения в UI"""
        if disconnected:
            self.ui.connectionStatus.setText("❌ Не подключено")
        elif success:
            self.ui.connectionStatus.setText("✅ Подключено")

    def load_devices(self):
        """Загружает список устройств"""
        if not self.device_manager:
            self.logger.error("Устройства не загружены — нет подключения")
            self._update_logs()
            return

        self.logger.info("Загрузка устройств...")
        self._update_logs()

        self.devices_panel.clear_devices()
        self.devices_panel.show_loading_indicator("🔄 Загрузка устройств...")

        self.device_loader = DeviceLoader(self.device_manager)
        self.device_loader.devices_loaded.connect(self.display_devices)
        self.device_loader.error.connect(self.on_device_load_error)
        self.device_loader.start()

    def display_devices(self, categorized):
        """Отображает загруженные устройства"""
        self.devices_panel.update_devices(categorized)

        total_devices = sum(len(devices) for devices in categorized.values())
        self.logger.success(f"Устройства загружены ({total_devices} шт.)")
        self._update_logs()

    def on_device_load_error(self, error):
        """Обработчик ошибки загрузки устройств"""
        self.logger.error(f"Ошибка загрузки устройств: {error}")
        self._update_logs()

    def open_device_details(self, device):
        """Открывает диалог с подробной информацией об устройстве"""
        dialog = DeviceDialog(device, self.entity_manager, parent=self)
        dialog.exec()

    def _update_logs(self):
        """Обновляет отображение логов в UI"""
        self.ui.textEditLogs.setPlainText(self.logger.get_text_log())
        self.ui.textEditLogs.verticalScrollBar().setValue(
            self.ui.textEditLogs.verticalScrollBar().maximum()
        )
from sys import argv, exit
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QMessageBox, QDialog
from ui.main_ui import Ui_MainWindow
from core.ws_client import HomeAssistantWSClient
from core.device_manager import DeviceManager
from core.entity_manager import EntityManager
from ui.connection_settings_window import ConnectionSettingsWindow
from core.db_manager import HAConnectionDB
from urllib.parse import urlparse


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setGeometry(100, 100, 900, 600)
        self.setWindowTitle("IoT Лаборатория")

        self.ws_client = None
        self.entity_manager = None
        self.device_manager = None

        self.db = HAConnectionDB()
        self.selected_connection = None

        # Подключение сигналов
        self.ui.btnGetDevices.clicked.connect(self.load_devices)
        self.ui.btnConnectSettings.clicked.connect(self.open_connection_settings)
        self.ui.btnConnect.clicked.connect(self.connect_to_selected)

        # Загрузка подключений
        self.load_connection_list()
        self.update_connection_status(disconnected=True)

    def load_connection_list(self):
        """Загрузка списка подключений в comboBox"""
        current_id = self.selected_connection["id"] if self.selected_connection else None

        self.connections = self.db.get_all_connections()
        self.ui.comboConnections.clear()

        selected_index = 0
        for index, conn in enumerate(self.connections):
            self.ui.comboConnections.addItem(conn["name"], conn)
            if conn["id"] == current_id:
                selected_index = index

        self.ui.comboConnections.setCurrentIndex(selected_index)

    def format_websocket_url(self, raw_url: str) -> str:
        parsed = urlparse(raw_url)
        if parsed.scheme == 'https':
            scheme = 'wss'
        else:
            scheme = 'ws'
        netloc = parsed.netloc or parsed.path
        return f"{scheme}://{netloc}/api/websocket"

    def format_rest_url(self, raw_url: str) -> str:
        parsed = urlparse(raw_url)
        if parsed.scheme not in ['http', 'https']:
            raw_url = "http://" + raw_url
            parsed = urlparse(raw_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def open_connection_settings(self):
        """Открыть окно настроек подключения"""
        dialog = ConnectionSettingsWindow(parent=self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.load_connection_list()

    def connect_to_selected(self):
        """Получить выбранное подключение и подключиться к HA"""
        index = self.ui.comboConnections.currentIndex()
        if index == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение из списка.")
            return

        connection_data = self.ui.comboConnections.itemData(index)
        if not connection_data:
            QMessageBox.warning(self, "Ошибка", "Данные подключения не найдены.")
            return

        self.selected_connection = connection_data
        self.connect_to_ha()

    def connect_to_ha(self):
        if not self.selected_connection:
            self.log("❌ Подключение не выбрано")
            self.update_connection_status(disconnected=True)
            return

        raw_url = self.selected_connection["url"]
        token = self.selected_connection["token"]

        ws_url = self.format_websocket_url(raw_url)
        rest_url = self.format_rest_url(raw_url)

        try:
            self.ws_client = HomeAssistantWSClient(ws_url, token)
            self.entity_manager = EntityManager(self.ws_client, rest_url, token)
            self.device_manager = DeviceManager(self.ws_client, self.entity_manager)

            self.device_manager.get_physical_devices()

            self.update_connection_status(url=rest_url, success=True)
            self.log(f"✅ Подключено к {rest_url}")

        except Exception as e:
            self.update_connection_status(disconnected=True)
            self.log(f"❌ Ошибка подключения: {e}")

    def update_connection_status(self, url="неизвестен", success=False, disconnected=False):
        if disconnected:
            self.ui.labelConnectionStatus.setText("❌ Не подключено")
            self.ui.labelConnectionStatus.setStyleSheet("color: red; font-weight: bold;")
            self.ui.labelConnectionUrl.setText("URL: неизвестен")
            return

        if success:
            self.ui.labelConnectionStatus.setText("✅ Подключено к Home Assistant")
            self.ui.labelConnectionStatus.setStyleSheet("color: green; font-weight: bold;")
            self.ui.labelConnectionUrl.setText(f"URL: {url}")

    def load_devices(self):
        if not self.device_manager:
            self.log("❌ Устройства не загружены — нет подключения")
            return

        categorized = self.device_manager.get_categorized_devices()
        layout = self.ui.layoutDeviceList

        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for category, devices in categorized.items():
            if not devices:
                continue

            label = QLabel(f"<b>{category} ({len(devices)})</b>")
            layout.addWidget(label)

            for device in devices:
                text = f"<b>{device['name']}</b> | {device['manufacturer']} {device['model']}"
                dev_label = QLabel(text)
                dev_label.setStyleSheet("margin-left: 10px;")
                layout.addWidget(dev_label)

        self.log("✅ Устройства загружены")

    def log(self, message: str):
        old_text = self.ui.textEditLogs.toPlainText()
        new_text = f"{old_text}\n{message}" if old_text else message
        self.ui.textEditLogs.setPlainText(new_text)
        self.ui.textEditLogs.verticalScrollBar().setValue(
            self.ui.textEditLogs.verticalScrollBar().maximum()
        )


if __name__ == "__main__":
    app = QApplication(argv)
    win = MainWindow()
    win.show()
    exit(app.exec())
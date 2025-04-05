from sys import argv, exit
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QMessageBox, QDialog
)
from PySide6.QtCore import QFile, QTextStream
from ui.MainWindow.main_ui import Ui_MainWindow
from ui.ConnectionSettingsWindow.connection_settings_window import ConnectionSettingsWindow
from ui.DeviceWidgets.categorized_devices_widget import CategorizedDevicesWidget
from ui.DeviceWidgets.device_detail_dialog import DeviceDetailDialog
from core.db_manager import HAConnectionDB
from core.connection_worker import ConnectionWorker
from core.device_loader import DeviceLoader

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setGeometry(100, 100, 900, 600)
        self.setWindowTitle("IoT")

        self.ws_client = None
        self.entity_manager = None
        self.device_manager = None

        self.db = HAConnectionDB()
        self.selected_connection = None

        self.connection_worker = None
        self.device_loader = None
        
        # Добавляем виджет для отображения устройств
        self.categorized_devices_widget = None
        self.setup_device_view()

        # Подключение сигналов
        self.ui.btnGetDevices.clicked.connect(self.load_devices)
        self.ui.btnConnectSettings.clicked.connect(self.open_connection_settings)
        self.ui.btnConnect.clicked.connect(self.connect_to_selected)

        # Загрузка подключений
        self.load_connection_list()
        self.update_connection_status(disconnected=True)

    def setup_device_view(self):
        # Удаляем текущий контент
        layout = self.ui.layoutDeviceList
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Создаем и добавляем виджет категоризированных устройств
        self.categorized_devices_widget = CategorizedDevicesWidget()
        self.categorized_devices_widget.deviceSelected.connect(self.open_device_details)
        layout.addWidget(self.categorized_devices_widget)

    def load_connection_list(self):
        current_id = self.selected_connection["id"] if self.selected_connection else None
        self.connections = self.db.get_all_connections()
        self.ui.comboConnections.clear()

        selected_index = 0
        for index, conn in enumerate(self.connections):
            self.ui.comboConnections.addItem(conn["name"], conn)
            if conn["id"] == current_id:
                selected_index = index

        self.ui.comboConnections.setCurrentIndex(selected_index)

    def open_connection_settings(self):
        dialog = ConnectionSettingsWindow(parent=self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.load_connection_list()

    def connect_to_selected(self):
        index = self.ui.comboConnections.currentIndex()
        if index == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите подключение из списка.")
            return

        connection_data = self.ui.comboConnections.itemData(index)
        if not connection_data:
            QMessageBox.warning(self, "Ошибка", "Данные подключения не найдены.")
            return

        self.selected_connection = connection_data

        self.ui.labelConnectionInfo.setText("🔄 Подключение...")
        self.start_connection_thread()

    def start_connection_thread(self):
        url = self.selected_connection["url"]
        token = self.selected_connection["token"]

        self.log("🔄 Подключение...")

        self.connection_worker = ConnectionWorker(url, token)
        self.connection_worker.connection_success.connect(self.on_connected)
        self.connection_worker.connection_failed.connect(self.on_connection_error)
        self.connection_worker.start()

    def on_connected(self, ws_client, entity_manager, device_manager, ws_url):
        self.ws_client = ws_client
        self.entity_manager = entity_manager
        self.device_manager = device_manager

        self.update_connection_status(success=True)
        self.log(f"✅ Подключение успешно установлено: {ws_url}")

    def on_connection_error(self, error_message):
        self.update_connection_status(disconnected=True)
        self.log(f"❌ Ошибка подключения: {error_message}")

    def update_connection_status(self, success=False, disconnected=False):
        if disconnected:
            self.ui.labelConnectionInfo.setText("❌ Не подключено")
            return

        if success:
            self.ui.labelConnectionInfo.setText("✅ Подключено к:")

    def load_devices(self):
        if not self.device_manager:
            self.log("❌ Устройства не загружены — нет подключения")
            return

        self.log("📦 Загрузка устройств...")
        
        # Показываем индикатор загрузки
        if self.categorized_devices_widget:
            for category, tab in self.categorized_devices_widget.category_tabs.items():
                loading_label = QLabel("🔄 Загрузка устройств...")
                loading_label.setStyleSheet("font-weight: bold; color: orange;")
                tab.flow_layout.addWidget(loading_label)

        # Запускаем загрузку в отдельном потоке
        self.device_loader = DeviceLoader(self.device_manager)
        self.device_loader.devices_loaded.connect(self.display_devices)
        self.device_loader.error.connect(self.on_device_load_error)
        self.device_loader.start()

    def display_devices(self, categorized):
        """Отображает устройства по категориям"""
        if self.categorized_devices_widget:
            self.categorized_devices_widget.update_devices(categorized)
        self.log("✅ Устройства загружены")

    def on_device_load_error(self, error):
        self.log(f"❌ Ошибка загрузки устройств: {error}")

    def open_device_details(self, device):
        """Открывает окно с подробной информацией об устройстве"""
        dialog = DeviceDetailDialog(device, self.entity_manager, parent=self)
        dialog.exec()

    def log(self, message: str):
        old_text = self.ui.textEditLogs.toPlainText()
        new_text = f"{old_text}\n{message}" if old_text else message
        self.ui.textEditLogs.setPlainText(new_text)
        self.ui.textEditLogs.verticalScrollBar().setValue(
            self.ui.textEditLogs.verticalScrollBar().maximum()
        )


def load_stylesheet():
    file = QFile(":/style/style.qss")
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        return stream.readAll()
    return ""

if __name__ == "__main__":
    app = QApplication(argv)
    app.setStyleSheet(load_stylesheet())
    win = MainWindow()
    win.show()
    exit(app.exec())
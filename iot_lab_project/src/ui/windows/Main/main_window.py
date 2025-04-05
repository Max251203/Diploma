from PySide6.QtWidgets import (QMainWindow, QLabel, QMessageBox, 
                             QDialog, QVBoxLayout, QComboBox)
from PySide6.QtCore import QFile, QTextStream
from ui.windows.Main.main_ui import Ui_MainWindow
from ui.windows.Connection.connection_dialog import ConnectionDialog
from ui.windows.Device.device_dialog import DeviceDialog
from ui.panels.devices_panel import DevicesPanel
from core.db.connection_db import HAConnectionDB
from core.workers.connection_worker import ConnectionWorker
from core.workers.device_loader import DeviceLoader

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.setGeometry(100, 100, 900, 600)
        self.setWindowTitle("IoT Лаборатория")
        
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
        # Подключение сигналов
        self.ui.btnConnectSettings.clicked.connect(self.open_connection_settings)
        self.ui.btnConnect.clicked.connect(self.connect_to_selected)
        self.ui.btnGetDevices.clicked.connect(self.load_devices)
        
        # Настройка панели устройств
        self.setup_devices_panel()
    
    def setup_devices_panel(self):
        """Настройка панели устройств"""
        layout = self.ui.layoutDeviceList
        
        # Удаляем текущее содержимое
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Создаем панель устройств
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
        self.ui.labelConnectionInfo.setText("🔄 Подключение...")
        self.log("🔄 Подключение...")
        
        # Запускаем подключение в отдельном потоке
        self.connection_worker = ConnectionWorker(
            self.selected_connection["url"], 
            self.selected_connection["token"]
        )
        self.connection_worker.connection_success.connect(self.on_connected)
        self.connection_worker.connection_failed.connect(self.on_connection_error)
        self.connection_worker.start()
    
    def on_connected(self, ws_client, entity_manager, device_manager, ws_url):
        """Обработчик успешного подключения"""
        self.ws_client = ws_client
        self.entity_manager = entity_manager
        self.device_manager = device_manager
        
        self.update_connection_status(success=True)
        self.log(f"✅ Подключение успешно установлено: {ws_url}")
    
    def on_connection_error(self, error_message):
        """Обработчик ошибки подключения"""
        self.update_connection_status(disconnected=True)
        self.log(f"❌ Ошибка подключения: {error_message}")
    
    def update_connection_status(self, success=False, disconnected=False):
        """Обновляет статус подключения в UI"""
        if disconnected:
            self.ui.labelConnectionInfo.setText("❌ Не подключено")
        elif success:
            self.ui.labelConnectionInfo.setText("✅ Подключено")
    
    def load_devices(self):
        """Загружает список устройств"""
        if not self.device_manager:
            self.log("❌ Устройства не загружены — нет подключения")
            return
        
        self.log("📦 Загрузка устройств...")
        
        # Запускаем загрузку в отдельном потоке
        self.device_loader = DeviceLoader(self.device_manager)
        self.device_loader.devices_loaded.connect(self.display_devices)
        self.device_loader.error.connect(self.on_device_load_error)
        self.device_loader.start()
    
    def display_devices(self, categorized):
        """Отображает загруженные устройства"""
        self.devices_panel.update_devices(categorized)
        self.log("✅ Устройства загружены")
    
    def on_device_load_error(self, error):
        """Обработчик ошибки загрузки устройств"""
        self.log(f"❌ Ошибка загрузки устройств: {error}")
    
    def open_device_details(self, device):
        """Открывает диалог с подробной информацией об устройстве"""
        dialog = DeviceDialog(device, self.entity_manager, parent=self)
        dialog.exec()
    
    def log(self, message):
        """Добавляет сообщение в лог"""
        current_text = self.ui.textEditLogs.toPlainText()
        new_text = f"{current_text}\n{message}" if current_text else message
        self.ui.textEditLogs.setPlainText(new_text)
        self.ui.textEditLogs.verticalScrollBar().setValue(
            self.ui.textEditLogs.verticalScrollBar().maximum()
        )
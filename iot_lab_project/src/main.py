import os
from sys import argv, exit
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from ui.main_ui import Ui_MainWindow
from core.ws_client import HomeAssistantWSClient
from core.device_manager import DeviceManager
from core.entity_manager import EntityManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setGeometry(100, 100, 900, 600)
        self.setWindowTitle("IoT Лаборатория")

        load_dotenv()
        self.ws_url = os.getenv("HA_WS_URL")
        self.token = os.getenv("HA_TOKEN")

        self.ws_client = None
        self.entity_manager = None
        self.device_manager = None

        self.ui.btnGetDevices.clicked.connect(self.load_devices)
        self.connect_to_ha()

    def connect_to_ha(self):
        if not self.ws_url or not self.token:
            self.ui.labelConnectionStatus.setText("❌ Нет подключения")
            self.ui.labelConnectionStatus.setStyleSheet("color: red; font-weight: bold;")
            self.ui.labelConnectionUrl.setText("URL: неизвестен")
            self.log("❌ Не заданы переменные HA_WS_URL и HA_TOKEN в .env")
            return
        try:
            self.ws_client = HomeAssistantWSClient(self.ws_url, self.token)
            self.entity_manager = EntityManager(self.ws_client)
            self.device_manager = DeviceManager(self.ws_client, self.entity_manager)

            self.device_manager.get_physical_devices()

            self.ui.labelConnectionStatus.setText("✅ Подключено к Home Assistant")
            self.ui.labelConnectionStatus.setStyleSheet("color: green; font-weight: bold;")
            self.ui.labelConnectionUrl.setText(f"URL: {self.ws_url}")
            self.log(f"✅ Подключено к {self.ws_url}")
        except Exception as e:
            self.ui.labelConnectionStatus.setText("❌ Ошибка подключения")
            self.ui.labelConnectionStatus.setStyleSheet("color: red; font-weight: bold;")
            self.ui.labelConnectionUrl.setText("URL: неизвестен")
            self.log(f"❌ Ошибка подключения: {e}")

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
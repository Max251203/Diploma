from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QListWidget, QHBoxLayout, QMessageBox, QTabWidget, QWidget, QLabel
)
from PySide6.QtCore import QSettings
from core.api import api_client


class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки подключений")
        self.setMinimumSize(600, 400)

        self._build_ui()
        self._load_connections()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # === Вкладка подключения к серверу === #
        self.tab_server = QWidget()
        self.tabs.addTab(self.tab_server, "Сервер")

        server_layout = QVBoxLayout(self.tab_server)

        server_form = QFormLayout()
        self.server_url = QLineEdit()
        self.server_url.setPlaceholderText("http://localhost:8000")
        server_form.addRow("URL сервера:", self.server_url)

        self.server_api_key = QLineEdit()
        self.server_api_key.setPlaceholderText("API ключ")
        server_form.addRow("API ключ:", self.server_api_key)

        server_layout.addLayout(server_form)

        server_buttons = QHBoxLayout()
        self.server_save = QPushButton("Сохранить")
        self.server_save.clicked.connect(self._save_server)
        self.server_test = QPushButton("Проверить соединение")
        self.server_test.clicked.connect(self._test_server)
        self.server_clear = QPushButton("Очистить")
        self.server_clear.clicked.connect(self._clear_server_form)
        server_buttons.addWidget(self.server_save)
        server_buttons.addWidget(self.server_test)
        server_buttons.addWidget(self.server_clear)
        server_layout.addLayout(server_buttons)

        # === Вкладка подключения к Home Assistant === #
        self.tab_ha = QWidget()
        self.tabs.addTab(self.tab_ha, "Home Assistant")

        ha_layout = QVBoxLayout(self.tab_ha)

        ha_form = QFormLayout()
        self.ha_name = QLineEdit()
        self.ha_url = QLineEdit()
        self.ha_token = QLineEdit()
        ha_form.addRow("Имя:", self.ha_name)
        ha_form.addRow("URL:", self.ha_url)
        ha_form.addRow("Token:", self.ha_token)
        ha_layout.addLayout(ha_form)

        ha_buttons = QHBoxLayout()
        self.ha_save = QPushButton("Сохранить")
        self.ha_save.clicked.connect(self._save_ha)
        self.ha_test = QPushButton("Проверить соединение")
        self.ha_test.clicked.connect(self._test_ha)
        self.ha_clear = QPushButton("Очистить")
        self.ha_clear.clicked.connect(self._clear_ha_form)
        ha_buttons.addWidget(self.ha_save)
        ha_buttons.addWidget(self.ha_test)
        ha_buttons.addWidget(self.ha_clear)
        ha_layout.addLayout(ha_buttons)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _load_connections(self):
        # Загрузка настроек сервера
        settings = QSettings("IoTLab", "Connection")
        self.server_url.setText(settings.value("url", ""))
        self.server_api_key.setText(settings.value("api_key", ""))

        # Загрузка настроек Home Assistant
        ha_settings = QSettings("IoTLab", "HomeAssistant")
        self.ha_name.setText(ha_settings.value("name", ""))
        self.ha_url.setText(ha_settings.value("url", ""))
        self.ha_token.setText(ha_settings.value("token", ""))

    def _save_server(self):
        url = self.server_url.text().strip()
        api_key = self.server_api_key.text().strip()

        if not url or not api_key:
            return QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")

        settings = QSettings("IoTLab", "Connection")
        settings.setValue("url", url)
        settings.setValue("api_key", api_key)

        QMessageBox.information(
            self, "Сохранено", "Настройки сервера сохранены.")
        self.accept()

    def _test_server(self):
        url = self.server_url.text().strip()
        api_key = self.server_api_key.text().strip()

        if not url or not api_key:
            return QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")

        api_client.configure(url, api_key)

        if api_client.check_connection():
            QMessageBox.information(
                self, "Успех", "Соединение с сервером установлено.")
        else:
            QMessageBox.critical(
                self, "Ошибка", "Не удалось подключиться к серверу.")

    def _clear_server_form(self):
        self.server_url.clear()
        self.server_api_key.clear()

    def _save_ha(self):
        name = self.ha_name.text().strip()
        url = self.ha_url.text().strip()
        token = self.ha_token.text().strip()

        if not name or not url or not token:
            return QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")

        ha_settings = QSettings("IoTLab", "HomeAssistant")
        ha_settings.setValue("name", name)
        ha_settings.setValue("url", url)
        ha_settings.setValue("token", token)

        QMessageBox.information(
            self, "Сохранено", "Настройки Home Assistant сохранены.")
        self.accept()

    def _test_ha(self):
        url = self.ha_url.text().strip()
        token = self.ha_token.text().strip()

        if not url or not token:
            return QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните URL и токен.")

        try:
            import requests
            response = requests.get(
                f"{url}/api/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            if response.status_code == 200:
                QMessageBox.information(
                    self, "Успех", "Соединение с Home Assistant установлено.")
            else:
                QMessageBox.critical(
                    self, "Ошибка", f"Ошибка подключения: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", f"Ошибка подключения: {str(e)}")

    def _clear_ha_form(self):
        self.ha_name.clear()
        self.ha_url.clear()
        self.ha_token.clear()

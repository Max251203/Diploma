from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QLabel, QMessageBox, QApplication, QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt
from core.api import api_client
from db.connection_db import HAConnectionDB


class ServerConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение к серверу")
        self.setFixedSize(400, 270)
        self.db = HAConnectionDB()
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("Подключение к серверу IoT Lab")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 14pt; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        form = QFormLayout()
        form.setSpacing(16)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название подключения")
        self.name_edit.setMinimumHeight(28)
        form.addRow("Название:", self.name_edit)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("http://localhost:8000")
        self.url_edit.setMinimumHeight(28)
        form.addRow("URL сервера:", self.url_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("API ключ")
        self.api_key_edit.setMinimumHeight(28)
        form.addRow("API ключ:", self.api_key_edit)

        main_layout.addLayout(form)

        # Кнопки внизу — горизонтально, с отступом
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setContentsMargins(0, 18, 0, 0)

        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.setMinimumHeight(30)
        self.connect_btn.clicked.connect(self._connect)
        btn_layout.addWidget(self.connect_btn)

        self.settings_btn = QPushButton("Расширенные настройки")
        self.settings_btn.setMinimumHeight(30)
        self.settings_btn.clicked.connect(self._open_full_settings)
        btn_layout.addWidget(self.settings_btn)

        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

    def _load_settings(self):
        api_connections = self.db.get_all_custom_api_connections()
        if api_connections:
            conn = api_connections[0]
            self.name_edit.setText(conn["name"])
            self.url_edit.setText(conn["url"])
            self.api_key_edit.setText(conn["api_key"])

    def _connect(self):
        self.connect_btn.setEnabled(False)
        QApplication.processEvents()
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        if not name or not url or not api_key:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            self.connect_btn.setEnabled(True)
            return
        api_connections = self.db.get_all_custom_api_connections()
        if api_connections:
            conn_id = api_connections[0]["id"]
            self.db.update_custom_api_connection(conn_id, name, url, api_key)
        else:
            self.db.add_custom_api_connection(name, url, api_key)
        api_client.configure(url, api_key)
        try:
            if api_client.check_connection():
                QMessageBox.information(
                    self, "Успех", "Соединение с сервером установлено.")
                self.accept()
            else:
                QMessageBox.critical(
                    self, "Ошибка", "Не удалось подключиться к серверу. Проверьте URL и API ключ.")
                self.connect_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", f"Ошибка подключения: {str(e)}")
            self.connect_btn.setEnabled(True)

    def _open_full_settings(self):
        from ui.dialogs.connection_dialog import ConnectionDialog
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._load_settings()
            api_connections = self.db.get_all_custom_api_connections()
            if api_connections:
                conn = api_connections[0]
                url = conn["url"]
                api_key = conn["api_key"]
                api_client.configure(url, api_key)
                if api_client.check_connection():
                    self.accept()

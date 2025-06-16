from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QLabel, QMessageBox, QApplication
)
from PySide6.QtCore import QSettings
from core.api import api_client
from db.connection_db import HAConnectionDB


class ServerConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение к серверу")
        self.setFixedSize(400, 200)

        self.db = HAConnectionDB()

        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title_label = QLabel("Подключение к серверу IoT Lab")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # Форма для ввода данных
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название подключения")
        form.addRow("Название:", self.name_edit)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("http://localhost:8000")
        form.addRow("URL сервера:", self.url_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("API ключ")
        form.addRow("API ключ:", self.api_key_edit)

        layout.addLayout(form)

        # Кнопки
        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.clicked.connect(self._connect)
        layout.addWidget(self.connect_btn)

        # Кнопка для открытия полных настроек
        self.settings_btn = QPushButton("Расширенные настройки")
        self.settings_btn.clicked.connect(self._open_full_settings)
        layout.addWidget(self.settings_btn)

    def _load_settings(self):
        """Загрузка сохраненных настроек"""
        api_connections = self.db.get_all_custom_api_connections()

        if api_connections:
            # Берем первое подключение из списка
            conn = api_connections[0]
            self.name_edit.setText(conn["name"])
            self.url_edit.setText(conn["url"])
            self.api_key_edit.setText(conn["api_key"])

    def _connect(self):
        """Подключение к серверу"""
        # Отключаем кнопку, чтобы предотвратить повторные нажатия
        self.connect_btn.setEnabled(False)
        QApplication.processEvents()  # Обрабатываем события, чтобы UI обновился

        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        api_key = self.api_key_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название подключения")
            self.connect_btn.setEnabled(True)
            return

        if not url:
            QMessageBox.warning(self, "Ошибка", "Введите URL сервера")
            self.connect_btn.setEnabled(True)
            return

        if not api_key:
            QMessageBox.warning(self, "Ошибка", "Введите API ключ")
            self.connect_btn.setEnabled(True)
            return

        # Сохраняем подключение в базу данных
        api_connections = self.db.get_all_custom_api_connections()
        if api_connections:
            # Обновляем существующее подключение
            conn_id = api_connections[0]["id"]
            self.db.update_custom_api_connection(conn_id, name, url, api_key)
        else:
            # Создаем новое подключение
            self.db.add_custom_api_connection(name, url, api_key)

        # Настраиваем API клиент
        api_client.configure(url, api_key)

        # Проверяем соединение
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
        """Открытие полного диалога настроек подключений"""
        from ui.dialogs.connection_dialog import ConnectionDialog
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Перезагружаем настройки
            self._load_settings()

            # Если есть активное подключение, проверяем его
            api_connections = self.db.get_all_custom_api_connections()
            if api_connections:
                conn = api_connections[0]
                url = conn["url"]
                api_key = conn["api_key"]

                # Настраиваем API клиент
                api_client.configure(url, api_key)

                # Проверяем соединение
                if api_client.check_connection():
                    self.accept()

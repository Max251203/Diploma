from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QListWidget, QHBoxLayout, QMessageBox, QTabWidget, QWidget, QLabel
)
from db.connection_db import HAConnectionDB
from core.api import api_client


class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки подключений")
        self.setMinimumSize(600, 400)

        self.db = HAConnectionDB()

        self.selected_ha_id = None
        self.selected_api_id = None
        self.ha_connections = []
        self.api_connections = []

        self._build_ui()
        self._load_connections()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # === Вкладка подключения к Home Assistant === #
        self.tab_ha = QWidget()
        self.tabs.addTab(self.tab_ha, "Home Assistant")

        ha_layout = QVBoxLayout(self.tab_ha)

        self.ha_list = QListWidget()
        self.ha_list.itemClicked.connect(self._on_ha_selected)
        ha_layout.addWidget(QLabel("Подключения Home Assistant"))
        ha_layout.addWidget(self.ha_list)

        self.ha_form = QFormLayout()
        self.ha_name = QLineEdit()
        self.ha_url = QLineEdit()
        self.ha_token = QLineEdit()
        self.ha_form.addRow("Имя:", self.ha_name)
        self.ha_form.addRow("URL:", self.ha_url)
        self.ha_form.addRow("Token:", self.ha_token)
        ha_layout.addLayout(self.ha_form)

        ha_buttons = QHBoxLayout()
        self.ha_save = QPushButton("Сохранить")
        self.ha_save.clicked.connect(self._save_ha)
        self.ha_delete = QPushButton("Удалить")
        self.ha_delete.clicked.connect(self._delete_ha)
        self.ha_clear = QPushButton("Очистить")
        self.ha_clear.clicked.connect(self._clear_ha_form)
        ha_buttons.addWidget(self.ha_save)
        ha_buttons.addWidget(self.ha_delete)
        ha_buttons.addWidget(self.ha_clear)
        ha_layout.addLayout(ha_buttons)

        # === Вкладка подключения к API серверу === #
        self.tab_api = QWidget()
        self.tabs.addTab(self.tab_api, "Настраиваемый API (FastAPI)")

        api_layout = QVBoxLayout(self.tab_api)

        self.api_list = QListWidget()
        self.api_list.itemClicked.connect(self._on_api_selected)
        api_layout.addWidget(QLabel("Подключения API серверов"))
        api_layout.addWidget(self.api_list)

        self.api_form = QFormLayout()
        self.api_name = QLineEdit()
        self.api_url = QLineEdit()
        self.api_key = QLineEdit()
        self.api_form.addRow("Имя:", self.api_name)
        self.api_form.addRow("URL:", self.api_url)
        self.api_form.addRow("API Key:", self.api_key)
        api_layout.addLayout(self.api_form)

        api_buttons = QHBoxLayout()
        self.api_save = QPushButton("Сохранить")
        self.api_save.clicked.connect(self._save_api)
        self.api_delete = QPushButton("Удалить")
        self.api_delete.clicked.connect(self._delete_api)
        self.api_clear = QPushButton("Очистить")
        self.api_clear.clicked.connect(self._clear_api_form)
        api_buttons.addWidget(self.api_save)
        api_buttons.addWidget(self.api_delete)
        api_buttons.addWidget(self.api_clear)
        api_layout.addLayout(api_buttons)

    # === Загрузка из БД ===

    def _load_connections(self):
        # Загрузка HA
        self.ha_connections = self.db.get_all_connections()
        self.ha_list.clear()
        for conn in self.ha_connections:
            self.ha_list.addItem(conn["name"])
        self._clear_ha_form()

        # Загрузка API
        self.api_connections = self.db.get_all_custom_api_connections()
        self.api_list.clear()
        for conn in self.api_connections:
            self.api_list.addItem(conn["name"])
        self._clear_api_form()

    # === HA Логика ===

    def _on_ha_selected(self, item):
        index = self.ha_list.row(item)
        conn = self.ha_connections[index]
        self.selected_ha_id = conn["id"]
        self.ha_name.setText(conn["name"])
        self.ha_url.setText(conn["url"])
        self.ha_token.setText(conn["token"])

    def _save_ha(self):
        name = self.ha_name.text().strip()
        url = self.ha_url.text().strip()
        token = self.ha_token.text().strip()

        if not name or not url or not token:
            return QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")

        if self.selected_ha_id:
            self.db.update_connection(self.selected_ha_id, name, url, token)
            QMessageBox.information(
                self, "Обновлено", "HA подключение обновлено.")
        else:
            self.db.add_connection(name, url, token)
            QMessageBox.information(
                self, "Добавлено", "Новое HA подключение добавлено.")

        self._load_connections()

    def _delete_ha(self):
        if not self.selected_ha_id:
            return QMessageBox.warning(self, "Ошибка", "Выберите подключение для удаления.")

        confirm = QMessageBox.question(self, "Подтверждение", "Удалить выбранное HA подключение?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.db.delete_connection(self.selected_ha_id)
            QMessageBox.information(self, "Удалено", "Подключение удалено.")
            self._load_connections()

    def _clear_ha_form(self):
        self.selected_ha_id = None
        self.ha_name.clear()
        self.ha_url.clear()
        self.ha_token.clear()
        self.ha_list.clearSelection()

    # === API Логика ===

    def _on_api_selected(self, item):
        index = self.api_list.row(item)
        conn = self.api_connections[index]
        self.selected_api_id = conn["id"]
        self.api_name.setText(conn["name"])
        self.api_url.setText(conn["url"])
        self.api_key.setText(conn["api_key"])

    def _save_api(self):
        name = self.api_name.text().strip()
        url = self.api_url.text().strip()
        key = self.api_key.text().strip()

        if not name or not url or not key:
            return QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")

        if self.selected_api_id:
            self.db.update_custom_api_connection(
                self.selected_api_id, name, url, key)
            QMessageBox.information(
                self, "Обновлено", "API подключение обновлено.")
        else:
            self.db.add_custom_api_connection(name, url, key)
            QMessageBox.information(
                self, "Добавлено", "Новое API подключение добавлено.")

        self._load_connections()

        # Если это активное подключение, обновляем API клиент
        if self.api_list.currentRow() == 0:  # Первое в списке
            api_client.configure(url, key)
            api_client.check_connection()

        # Закрываем диалог после сохранения
        self.accept()

    def _delete_api(self):
        if not self.selected_api_id:
            return QMessageBox.warning(self, "Ошибка", "Выберите API подключение для удаления.")

        confirm = QMessageBox.question(self, "Подтверждение", "Удалить выбранное API подключение?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.db.delete_custom_api_connection(self.selected_api_id)
            QMessageBox.information(self, "Удалено", "Подключение удалено.")
            self._load_connections()

    def _clear_api_form(self):
        self.selected_api_id = None
        self.api_name.clear()
        self.api_url.clear()
        self.api_key.clear()
        self.api_list.clearSelection()

    def get_active_api_connection(self):
        """Получение активного API подключения (первого в списке)"""
        if self.api_connections:
            return self.api_connections[0]
        return None

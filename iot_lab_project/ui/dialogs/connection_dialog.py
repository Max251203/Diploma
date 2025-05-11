from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QListWidget, QHBoxLayout, QMessageBox
)
from db.connection_db import HAConnectionDB

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки подключений")
        self.setMinimumSize(600, 400)

        self.db = HAConnectionDB()
        self.selected_id = None
        self.connections = []

        self._build_ui()
        self._load_connections()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_selected)
        layout.addWidget(self.list_widget)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.url_edit = QLineEdit()
        self.token_edit = QLineEdit()
        form.addRow("Имя:", self.name_edit)
        form.addRow("URL:", self.url_edit)
        form.addRow("Token:", self.token_edit)
        layout.addLayout(form)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self._save_connection)

        self.remove_btn = QPushButton("Удалить")
        self.remove_btn.clicked.connect(self._remove_connection)

        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.clicked.connect(self._clear_form)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

    def _load_connections(self):
        self.connections = self.db.get_all_connections()
        self.list_widget.clear()
        for conn in self.connections:
            self.list_widget.addItem(conn["name"])
        self._clear_form()

    def _on_item_selected(self, item):
        index = self.list_widget.row(item)
        conn = self.connections[index]
        self.selected_id = conn["id"]
        self.name_edit.setText(conn["name"])
        self.url_edit.setText(conn["url"])
        self.token_edit.setText(conn["token"])

    def _save_connection(self):
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        token = self.token_edit.text().strip()

        if not name or not url or not token:
            return QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")

        if self.selected_id:
            self.db.update_connection(self.selected_id, name, url, token)
            QMessageBox.information(self, "Обновлено", "Подключение обновлено.")
        else:
            self.db.add_connection(name, url, token)
            QMessageBox.information(self, "Добавлено", "Новое подключение добавлено.")

        self._load_connections()
        self.accept()

    def _remove_connection(self):
        if not self.selected_id:
            return QMessageBox.warning(self, "Ошибка", "Выберите подключение для удаления.")

        confirm = QMessageBox.question(self, "Подтверждение", "Удалить выбранное подключение?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.db.delete_connection(self.selected_id)
            QMessageBox.information(self, "Удалено", "Подключение удалено.")
            self._load_connections()
            self.accept()

    def _clear_form(self):
        self.selected_id = None
        self.name_edit.clear()
        self.url_edit.clear()
        self.token_edit.clear()
        self.list_widget.clearSelection()
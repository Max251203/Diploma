from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QListWidget, QLineEdit, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
from core.db.connection_db import HAConnectionDB

class ConnectionDialog(QDialog):
    """Диалог для управления подключениями к Home Assistant"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки подключений")
        self.setMinimumSize(600, 400)
        
        self.db = HAConnectionDB()
        self.selected_connection_id = None
        self.connections = []
        
        self.setup_ui()
        self.load_connections()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Список подключений
        self.connections_list = QListWidget()
        self.connections_list.itemClicked.connect(self._on_connection_selected)
        layout.addWidget(self.connections_list)
        
        # Форма редактирования
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        form_layout.addRow("Имя:", self.name_edit)
        
        self.url_edit = QLineEdit()
        form_layout.addRow("URL:", self.url_edit)
        
        self.token_edit = QLineEdit()
        form_layout.addRow("Token:", self.token_edit)
        
        layout.addLayout(form_layout)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self._save_connection)
        
        self.remove_button = QPushButton("Удалить")
        self.remove_button.clicked.connect(self._remove_connection)
        
        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self._clear_form)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
    
    def load_connections(self):
        """Загружает список подключений из базы данных"""
        self.connections = self.db.get_all_connections()
        self.connections_list.clear()
        
        for conn in self.connections:
            self.connections_list.addItem(conn["name"])
        
        self._clear_form()
    
    def _on_connection_selected(self, item):
        """Обработчик выбора подключения из списка"""
        index = self.connections_list.row(item)
        connection = self.connections[index]
        self.selected_connection_id = connection["id"]
        
        self.name_edit.setText(connection["name"])
        self.url_edit.setText(connection["url"])
        self.token_edit.setText(connection["token"])
    
    def _save_connection(self):
        """Сохраняет текущее подключение"""
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        token = self.token_edit.text().strip()
        
        if not name or not url or not token:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return
        
        if self.selected_connection_id:
            self.db.update_connection(self.selected_connection_id, name, url, token)
            QMessageBox.information(self, "Обновлено", "Подключение обновлено.")
        else:
            self.db.add_connection(name, url, token)
            QMessageBox.information(self, "Добавлено", "Новое подключение добавлено.")
        
        self.load_connections()
        self.accept()
    
    def _remove_connection(self):
        """Удаляет выбранное подключение"""
        if not self.selected_connection_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите подключение для удаления.")
            return
        
        confirm = QMessageBox.question(
            self, "Подтверждение", "Удалить выбранное подключение?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.db.delete_connection(self.selected_connection_id)
            QMessageBox.information(self, "Удалено", "Подключение удалено.")
            self.load_connections()
            self.accept()
    
    def _clear_form(self):
        """Очищает форму редактирования"""
        self.selected_connection_id = None
        self.name_edit.clear()
        self.url_edit.clear()
        self.token_edit.clear()
        self.connections_list.clearSelection()
from PySide6.QtWidgets import QDialog, QMessageBox
from ui.connection_settings_ui import Ui_ConnectionSettingsWindow
from core.db_manager import HAConnectionDB
from config import ALLOW_TOKEN_EDIT


class ConnectionSettingsWindow(QDialog, Ui_ConnectionSettingsWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.db = HAConnectionDB()
        self.selected_connection_id = None
        self.selected_connection_data = None

        self.tokenEdit.setDisabled(not ALLOW_TOKEN_EDIT)

        # Подключаем сигналы
        self.connectionsList.itemClicked.connect(self.on_connection_selected)
        self.saveButton.clicked.connect(self.save_connection)
        self.removeButton.clicked.connect(self.remove_connection)
        self.clearButton.clicked.connect(self.clear_fields)

        self.update_connection_list()

    def update_connection_list(self):
        """Загрузить список подключений"""
        self.connections = self.db.get_all_connections()
        self.connectionsList.clear()
        for conn in self.connections:
            self.connectionsList.addItem(conn["name"])
        self.clear_fields()

    def on_connection_selected(self, item):
        """При выборе элемента загрузить его данные"""
        index = self.connectionsList.row(item)
        connection = self.connections[index]
        self.selected_connection_id = connection["id"]
        self.selected_connection_data = connection

        self.nameEdit.setText(connection["name"])
        self.urlEdit.setText(connection["url"])
        self.tokenEdit.setText(connection["token"])

    def save_connection(self):
        """Сохранить или добавить подключение"""
        name = self.nameEdit.text().strip()
        url = self.urlEdit.text().strip()
        token = self.tokenEdit.text().strip()

        if not name or not url or not token:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return

        if self.selected_connection_id:
            # Обновление
            self.db.update_connection(self.selected_connection_id, name, url, token)
            QMessageBox.information(self, "Обновлено", "Подключение обновлено.")
        else:
            # Добавление
            self.db.add_connection(name, url, token)
            QMessageBox.information(self, "Добавлено", "Новое подключение добавлено.")

        self.update_connection_list()
        self.accept()  # Сообщаем родителю, что были изменения

    def remove_connection(self):
        """Удалить выбранное подключение"""
        if not self.selected_connection_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите подключение для удаления.")
            return

        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить выбранное подключение?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_connection(self.selected_connection_id)
            QMessageBox.information(self, "Удалено", "Подключение успешно удалено.")
            self.update_connection_list()
            self.accept()

    def clear_fields(self):
        """Очистить поля и сбросить выбор"""
        self.selected_connection_id = None
        self.selected_connection_data = None
        self.nameEdit.clear()
        self.urlEdit.clear()
        self.tokenEdit.clear()
        self.connectionsList.clearSelection()
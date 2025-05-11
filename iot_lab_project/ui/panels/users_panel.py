from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QHeaderView, QMessageBox, QDialog
from db.users_db import UserDB
from ui.dialogs.user_dialog import UserDialog

class UsersPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = UserDB()
        self.users = []
        self._build_ui()
        self._load_users()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Логин", "ФИО", "Роль"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.btn_add = QPushButton("Добавить пользователя", clicked=self._add_user)
        self.btn_edit = QPushButton("Редактировать", clicked=self._edit_user)
        self.btn_delete = QPushButton("Удалить", clicked=self._delete_user)

        buttons.addWidget(self.btn_add)
        buttons.addWidget(self.btn_edit)
        buttons.addWidget(self.btn_delete)
        buttons.addStretch()
        layout.addLayout(buttons)

    def _load_users(self):
        self.users = self.db.get_all_users()
        self.table.setRowCount(len(self.users))

        for i, user in enumerate(self.users):
            self.table.setItem(i, 0, QTableWidgetItem(user["login"]))
            fio = f"{user.get('last_name', '')} {user.get('first_name', '')} {user.get('middle_name', '')}".strip()
            self.table.setItem(i, 1, QTableWidgetItem(fio))

            combo = QComboBox()
            combo.addItems(["student", "teacher", "admin"])
            combo.setCurrentText(user["role"])
            combo.setMinimumHeight(28)
            combo.currentTextChanged.connect(lambda role, uid=user["id"]: self._change_role(uid, role))
            self.table.setCellWidget(i, 2, combo)

    def _get_selected_user(self):
        index = self.table.currentRow()
        if index < 0:
            return None
        return self.db.get_user_by_login(self.table.item(index, 0).text())

    def _change_role(self, user_id, new_role):
        self.db.update_user_role(user_id, new_role)
        QMessageBox.information(self, "Роль изменена", f"Назначена роль: {new_role}")

    def _add_user(self):
        dialog = UserDialog(mode="add", parent=self)
        dialog.user_saved.connect(self._on_user_saved)
        if dialog.exec() == QDialog.Accepted:
            self._load_users()

    def _edit_user(self):
        user = self._get_selected_user()
        if not user:
            return QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
        dialog = UserDialog(mode="edit", user_data=user, parent=self)
        dialog.user_saved.connect(self._on_user_saved)
        if dialog.exec() == QDialog.Accepted:
            self._load_users()

    def _on_user_saved(self, user):
        # Всегда обновлять профиль в главном окне, если это текущий пользователь
        mainwin = self.parent()
        if hasattr(mainwin, "update_user_profile") and user["login"] == mainwin.user_data.get("login"):
            mainwin.update_user_profile(user)
        # Уведомление об успешном изменении
        QMessageBox.information(self, "Успех", "Данные пользователя успешно обновлены!")

    def _delete_user(self):
        user = self._get_selected_user()
        if not user:
            return QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
        current_login = self.parent().user_data["login"] if hasattr(self.parent(), "user_data") else None
        if user["login"] == current_login:
            return QMessageBox.warning(self, "Ошибка", "Нельзя удалить себя")
        if QMessageBox.question(self, "Подтверждение", f"Удалить пользователя: {user['login']}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_user(user["id"])
            self._load_users()
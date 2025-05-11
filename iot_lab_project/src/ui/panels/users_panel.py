from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QDialog, QHeaderView
)
from PySide6.QtCore import Qt
from core.db.users_db import UserDB
from ui.windows.User.user_dialog import UserDialog


class UsersPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = UserDB()
        self.users = []

        self.layout = QVBoxLayout(self)
        self._init_ui()
        self.load_users()

    def _init_ui(self):
        # === Таблица пользователей ===
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

        self.layout.addWidget(self.table)

        # === Кнопки ===
        buttons_layout = QHBoxLayout()

        self.btn_add_user = QPushButton("Добавить пользователя")
        self.btn_add_user.clicked.connect(self.add_user)

        self.btn_edit = QPushButton("Редактировать")
        self.btn_edit.clicked.connect(self.edit_selected_user)

        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.clicked.connect(self.delete_selected_user)

        buttons_layout.addWidget(self.btn_add_user)
        buttons_layout.addWidget(self.btn_edit)
        buttons_layout.addWidget(self.btn_delete)
        buttons_layout.addStretch()

        self.layout.addLayout(buttons_layout)

    def load_users(self):
        self.users = self.db.get_all_users()
        self.table.setRowCount(len(self.users))

        for row, user in enumerate(self.users):
            self.table.setItem(row, 0, QTableWidgetItem(user["login"]))

            fio = f"{user.get('last_name', '')} {user.get('first_name', '')} {user.get('middle_name', '')}".strip()
            self.table.setItem(row, 1, QTableWidgetItem(fio))

            combo = QComboBox()
            combo.addItems(["student", "teacher", "admin"])
            combo.setCurrentText(user["role"])
            combo.setMinimumHeight(28)
            combo.setMaximumHeight(30)
            combo.currentTextChanged.connect(lambda role, uid=user["id"]: self.change_role(uid, role))
            self.table.setCellWidget(row, 2, combo)

    def get_selected_user(self):
        selected = self.table.currentRow()
        if selected < 0:
            return None
        login_item = self.table.item(selected, 0)
        if not login_item:
            return None
        return self.db.get_user_by_login(login_item.text())

    def change_role(self, user_id, new_role):
        self.db.update_user_role(user_id, new_role)
        QMessageBox.information(self, "Роль изменена", f"Назначена роль: {new_role}")

    def add_user(self):
        dialog = UserDialog(mode="add", parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_users()

    def edit_selected_user(self):
        user = self.get_selected_user()
        if not user:
            return QMessageBox.warning(self, "Ошибка", "Выберите пользователя для редактирования")
        dialog = UserDialog(mode="edit", user_data=user, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_users()

    def delete_selected_user(self):
        user = self.get_selected_user()
        if not user:
            return QMessageBox.warning(self, "Ошибка", "Выберите пользователя")

        if user["role"] == "admin":
            return QMessageBox.warning(self, "Ошибка", "Нельзя удалить администратора")

        confirm = QMessageBox.question(
            self, "Подтверждение", f"Удалить пользователя: {user['login']}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.db.delete_user(user["id"])
            self.load_users()
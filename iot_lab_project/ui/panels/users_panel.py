from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox,
    QHeaderView, QMessageBox, QDialog
)
from PySide6.QtCore import Qt
from db.users_db import UserDB
from ui.dialogs.user_dialog import UserDialog
from core.permissions import get_all_roles, get_role_label

class UsersPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = UserDB()
        self.users = []
        self.current_user_id = (
            parent.user_data.get("id")
            if parent and hasattr(parent, "user_data")
            else None
        )
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

            is_self = user["id"] == self.current_user_id

            if is_self:
                item = QTableWidgetItem(f"{get_role_label(user['role'])} (ВЫ)")
                item.setForeground(Qt.yellow)
                item.setFont(self.table.horizontalHeader().font())
                self.table.setItem(i, 2, item)
            else:
                combo = QComboBox()
                combo.addItems(get_all_roles())
                combo.setCurrentText(user["role"])
                combo.setMinimumHeight(26)
                combo.setStyleSheet("margin:1px; padding:1px;")
                combo.currentTextChanged.connect(lambda role, uid=user["id"]: self._change_role(uid, role))
                self.table.setCellWidget(i, 2, combo)

    def _get_selected_user(self):
        index = self.table.currentRow()
        if index < 0:
            return None
        login_item = self.table.item(index, 0)
        if not login_item:
            return None
        return self.db.get_user_by_login(login_item.text())

    def _change_role(self, user_id, new_role):
        self.db.update_user_role(user_id, new_role)
        QMessageBox.information(self, "Роль обновлена", f"Назначена роль: {get_role_label(new_role)}")

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

    def _delete_user(self):
        user = self._get_selected_user()
        if not user:
            return QMessageBox.warning(self, "Ошибка", "Выберите пользователя")

        if user["id"] == self.current_user_id:
            return QMessageBox.warning(self, "Ошибка", "Вы не можете удалить своего пользователя!")

        confirm = QMessageBox.question(
            self, "Подтверждение", f"Удалить пользователя: {user['login']}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.db.delete_user(user["id"])
            self._load_users()

    def _on_user_saved(self, user):
        mainwin = self.window()
        if hasattr(mainwin, "update_user_profile"):
            mainwin.update_user_profile(user)

        # Обязательно обновить ID текущего пользователя после изменений!
        self.current_user_id = (
            self.parent().user_data.get("id")
            if hasattr(self.parent(), "user_data")
            else self.current_user_id
        )

        self._load_users()
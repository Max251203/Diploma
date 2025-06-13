from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox,
    QHeaderView, QMessageBox, QDialog
)
from PySide6.QtCore import Qt
from core.api import api_client
from core.api.api_worker import (
    GetUsersWorker, UpdateUserWorker, DeleteUserWorker
)
from ui.dialogs.user_dialog import UserDialog
from core.permissions import get_all_roles, get_role_label


class UsersPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.btn_add = QPushButton(
            "Добавить пользователя", clicked=self._add_user)
        self.btn_edit = QPushButton("Редактировать", clicked=self._edit_user)
        self.btn_delete = QPushButton("Удалить", clicked=self._delete_user)

        buttons.addWidget(self.btn_add)
        buttons.addWidget(self.btn_edit)
        buttons.addWidget(self.btn_delete)
        buttons.addStretch()

        layout.addLayout(buttons)

    def _load_users(self):
        """Загрузка списка пользователей через API"""
        worker = GetUsersWorker(api_client)
        worker.result_ready.connect(self._on_users_loaded)
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _on_users_loaded(self, users):
        """Обработка загруженных пользователей"""
        if users is None:
            QMessageBox.warning(
                self, "Ошибка", "Не удалось загрузить пользователей")
            return

        self.users = users
        self.table.setRowCount(len(self.users))

        for i, user in enumerate(self.users):
            self.table.setItem(i, 0, QTableWidgetItem(user["login"]))

            fio = f"{user.get('last_name', '')} {user.get('first_name', '')} {user.get('middle_name', '')}".strip(
            )
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
                combo.currentTextChanged.connect(
                    lambda role, uid=user["id"]: self._change_role(uid, role))
                self.table.setCellWidget(i, 2, combo)

    def _get_selected_user(self):
        index = self.table.currentRow()
        if index < 0:
            return None
        return self.users[index] if index < len(self.users) else None

    def _change_role(self, user_id, new_role):
        """Изменение роли пользователя через API"""
        worker = UpdateUserWorker(api_client, user_id, {"role": new_role})
        worker.result_ready.connect(
            lambda user: self._on_role_updated(user, new_role))
        worker.error_occurred.connect(self._show_error)
        worker.start()

    def _on_role_updated(self, user, new_role):
        """Обработка успешного обновления роли"""
        if user:
            QMessageBox.information(self, "Роль обновлена",
                                    f"Назначена роль: {get_role_label(new_role)}")
            # Обновляем список пользователей
            self._load_users()
        else:
            QMessageBox.warning(
                self, "Ошибка", "Не удалось обновить роль пользователя")

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
            worker = DeleteUserWorker(api_client, user["id"])
            worker.result_ready.connect(
                lambda success: self._on_user_deleted(success, user))
            worker.error_occurred.connect(self._show_error)
            worker.start()

    def _on_user_deleted(self, success, user):
        """Обработка результата удаления пользователя"""
        if success:
            QMessageBox.information(
                self, "Успех", f"Пользователь {user['login']} удален")
            self._load_users()
        else:
            QMessageBox.warning(
                self, "Ошибка", "Не удалось удалить пользователя")

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

    def _show_error(self, error):
        """Отображение ошибки"""
        QMessageBox.warning(self, "Ошибка", error)

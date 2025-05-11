from PySide6.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QComboBox, QHBoxLayout, QToolButton, QWidget
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from db.users_db import UserDB

class UserDialog(QDialog):
    def __init__(self, mode="profile", user_data=None, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.setWindowTitle(self._get_title(mode))
        self.mode = mode
        self.user_data = user_data or {}
        self.db = UserDB()

        self._build_ui()
        self._fill_fields()

    def _get_title(self, mode):
        return {
            "profile": "Редактирование профиля",
            "edit": "Редактирование пользователя",
            "add": "Добавление пользователя"
        }.get(mode, "Пользователь")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.login_edit = QLineEdit(placeholderText="Введите логин")
        form.addRow("Логин:", self.login_edit)

        self.lastname_edit = QLineEdit(placeholderText="Фамилия")
        self.firstname_edit = QLineEdit(placeholderText="Имя")
        self.middlename_edit = QLineEdit(placeholderText="Отчество")
        form.addRow("Фамилия:", self.lastname_edit)
        form.addRow("Имя:", self.firstname_edit)
        form.addRow("Отчество:", self.middlename_edit)

        self.password_edit, self.toggle_btn = self._create_password_field()
        form.addRow("Пароль:", self._wrap_with_icon(self.password_edit, self.toggle_btn))

        self.role_combo = QComboBox()
        self.role_combo.addItems(["student", "teacher", "admin"])
        if self.mode != "profile":
            form.addRow("Роль:", self.role_combo)

        layout.addLayout(form)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self._save_user)
        layout.addWidget(self.save_btn)

    def _create_password_field(self):
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.Password)
        btn = QToolButton()
        btn.setIcon(QIcon(":/icon/icons/eye.png"))
        btn.setIconSize(QSize(20, 20))
        btn.setCheckable(True)
        btn.toggled.connect(lambda checked: self._toggle_password_visibility(edit, btn, checked))
        return edit, btn

    def _wrap_with_icon(self, field, icon_btn):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(field)
        layout.addWidget(icon_btn)
        container = QWidget()
        container.setLayout(layout)
        return container

    def _toggle_password_visibility(self, field, btn, visible):
        field.setEchoMode(QLineEdit.Normal if visible else QLineEdit.Password)
        icon = QIcon(":/icon/icons/eye_off.png") if visible else QIcon(":/icon/icons/eye.png")
        btn.setIcon(icon)

    def _fill_fields(self):
        self.login_edit.setText(self.user_data.get("login", ""))
        self.lastname_edit.setText(self.user_data.get("last_name", ""))
        self.firstname_edit.setText(self.user_data.get("first_name", ""))
        self.middlename_edit.setText(self.user_data.get("middle_name", ""))
        if self.mode == "edit":
            self.role_combo.setCurrentText(self.user_data.get("role", "student"))

    def _save_user(self):
        login = self.login_edit.text().strip()
        last = self.lastname_edit.text().strip()
        first = self.firstname_edit.text().strip()
        middle = self.middlename_edit.text().strip()
        password = self.password_edit.text().strip()
        role = self.role_combo.currentText() if self.mode != "profile" else self.user_data.get("role", "student")

        if not login or not last or not first:
            return QMessageBox.warning(self, "Ошибка", "Поля логин, имя и фамилия обязательны")

        if self.mode == "add" and not password:
            return QMessageBox.warning(self, "Ошибка", "Пароль обязателен при создании пользователя")

        try:
            if self.mode == "add":
                self.db.add_user(login, password, last, first, middle, role)
            else:
                self.db.update_user_info(
                    user_id=self.user_data["id"],
                    login=login,
                    last_name=last,
                    first_name=first,
                    middle_name=middle,
                    new_password=password if password else None,
                    role=role
                )
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QComboBox, QHBoxLayout, QToolButton, QWidget
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from core.db.users_db import UserDB


class UserDialog(QDialog):
    def __init__(self, mode="profile", user_data=None, parent=None):
        super().__init__(parent)
        self.mode = mode  # "profile", "edit", "add"
        self.db = UserDB()
        self.user_data = user_data or {}
        self.setMinimumSize(400, 400)
        self.setWindowTitle(self._get_title())
        self.password_visible = False

        self._build_ui()
        self._fill_fields()

    def _get_title(self):
        return {
            "profile": "Редактирование профиля",
            "edit": "Редактирование пользователя",
            "add": "Добавление пользователя"
        }.get(self.mode, "Пользователь")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Введите логин")
        form.addRow("Логин:", self.login_edit)

        self.lastname_edit = QLineEdit()
        self.lastname_edit.setPlaceholderText("Фамилия")
        form.addRow("Фамилия:", self.lastname_edit)

        self.firstname_edit = QLineEdit()
        self.firstname_edit.setPlaceholderText("Имя")
        form.addRow("Имя:", self.firstname_edit)

        self.middlename_edit = QLineEdit()
        self.middlename_edit.setPlaceholderText("Отчество")
        form.addRow("Отчество:", self.middlename_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Новый пароль (опционально)")
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.toggle_btn = QToolButton()
        self.toggle_btn.setIcon(QIcon(":/icon/icons/eye.png"))
        self.toggle_btn.setIconSize(QSize(20, 20))
        self.toggle_btn.clicked.connect(self.toggle_password_visibility)

        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_edit)
        password_layout.addWidget(self.toggle_btn)

        password_widget = QWidget()
        password_widget.setLayout(password_layout)
        form.addRow("Пароль:", password_widget)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["student", "teacher", "admin"])
        if self.mode == "profile":
            self.role_combo.setVisible(False)
        else:
            form.addRow("Роль:", self.role_combo)

        layout.addLayout(form)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_user)
        layout.addWidget(self.save_btn)

    def _fill_fields(self):
        self.login_edit.setText(self.user_data.get("login", ""))
        self.lastname_edit.setText(self.user_data.get("last_name", ""))
        self.firstname_edit.setText(self.user_data.get("first_name", ""))
        self.middlename_edit.setText(self.user_data.get("middle_name", ""))
        if self.mode == "edit" and "role" in self.user_data:
            self.role_combo.setCurrentText(self.user_data["role"])

    def toggle_password_visibility(self):
        self.password_visible = not self.password_visible
        mode = QLineEdit.Normal if self.password_visible else QLineEdit.Password
        self.password_edit.setEchoMode(mode)
        icon = QIcon(":/icon/icons/eye_off.png") if self.password_visible else QIcon(":/icon/icons/eye.png")
        self.toggle_btn.setIcon(icon)

    def save_user(self):
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
                    new_password=password,
                    role=role
                )
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
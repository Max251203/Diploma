from PySide6.QtWidgets import (
    QDialog, QLineEdit, QLabel, QPushButton, QVBoxLayout, QFormLayout,
    QHBoxLayout, QToolButton, QMessageBox, QWidget
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from db.users_db import UserDB


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход / Регистрация")
        self.setFixedSize(400, 220)
        self.setObjectName("loginDialog")

        self.db = UserDB()
        self.user_data = None
        self.is_register_mode = False

        self._build_ui()
        self._set_register_mode(False)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.form = QFormLayout()
        self.form.setSpacing(12)

        self.login_edit = QLineEdit(placeholderText="Введите логин")
        self.form.addRow("Логин:", self.login_edit)

        self.password_edit, self.toggle_password_btn = self._create_password_field(
            "Введите пароль")
        self.form.addRow("Пароль:", self._wrap_with_icon(
            self.password_edit, self.toggle_password_btn))

        self.repeat_edit, self.toggle_repeat_btn = self._create_password_field(
            "Повторите пароль")
        self.row_repeat = self._wrap_with_icon(
            self.repeat_edit, self.toggle_repeat_btn)
        self.form.addRow("Повтор пароля:", self.row_repeat)

        self.lastname_edit = QLineEdit(placeholderText="Введите фамилию")
        self.form.addRow("Фамилия:", self.lastname_edit)
        self.firstname_edit = QLineEdit(placeholderText="Введите имя")
        self.form.addRow("Имя:", self.firstname_edit)
        self.middlename_edit = QLineEdit(placeholderText="Введите отчество")
        self.form.addRow("Отчество:", self.middlename_edit)

        layout.addLayout(self.form)

        self.submit_btn = QPushButton("Войти")
        self.submit_btn.clicked.connect(self._on_submit)

        self.toggle_mode_btn = QPushButton("У меня нет аккаунта")
        self.toggle_mode_btn.clicked.connect(self._toggle_mode)

        layout.addSpacing(10)
        layout.addWidget(self.submit_btn)
        layout.addWidget(self.toggle_mode_btn)
        layout.addStretch()

    def _create_password_field(self, placeholder=""):
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.Password)
        edit.setPlaceholderText(placeholder)
        btn = QToolButton()
        btn.setIcon(QIcon(":/icon/icons/eye.png"))
        btn.setIconSize(QSize(20, 20))
        btn.setCheckable(True)
        btn.toggled.connect(lambda checked, e=edit,
                            b=btn: self._toggle_password(checked, e, b))
        return edit, btn

    def _wrap_with_icon(self, line_edit, icon_button):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(line_edit)
        layout.addWidget(icon_button)
        container = QWidget()
        container.setLayout(layout)
        return container

    def _toggle_password(self, visible, line_edit, button):
        line_edit.setEchoMode(
            QLineEdit.Normal if visible else QLineEdit.Password)
        icon = QIcon(
            ":/icon/icons/eye_off.png") if visible else QIcon(":/icon/icons/eye.png")
        button.setIcon(icon)

    def _toggle_mode(self):
        self._set_register_mode(not self.is_register_mode)
        self.toggle_mode_btn.clearFocus()
        self.toggle_mode_btn.setDown(False)

    def _set_register_mode(self, register: bool):
        self.is_register_mode = register

        self.form.labelForField(self.row_repeat).setVisible(register)
        self.row_repeat.setVisible(register)
        self.form.labelForField(self.lastname_edit).setVisible(register)
        self.lastname_edit.setVisible(register)
        self.form.labelForField(self.firstname_edit).setVisible(register)
        self.firstname_edit.setVisible(register)
        self.form.labelForField(self.middlename_edit).setVisible(register)
        self.middlename_edit.setVisible(register)

        self.submit_btn.setText("Зарегистрироваться" if register else "Войти")
        self.toggle_mode_btn.setText(
            "Уже есть аккаунт" if register else "У меня нет аккаунта")
        self.setFixedSize(400, 460 if register else 220)

    def _on_submit(self):
        login = self.login_edit.text().strip()
        password = self.password_edit.text()
        if self.is_register_mode:
            repeat = self.repeat_edit.text()
            last = self.lastname_edit.text().strip()
            first = self.firstname_edit.text().strip()
            middle = self.middlename_edit.text().strip()

            if not login or not password or not repeat or not last or not first or not middle:
                return QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            if password != repeat:
                return QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            try:
                self.db.add_user(login, password, last, first, middle)
                QMessageBox.information(self, "Успех", "Вы зарегистрированы!")
                self._set_register_mode(False)
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка", str(e))
        else:
            if not login or not password:
                return QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            user = self.db.authenticate_user(login, password)
            if user:
                self.user_data = user
                self.accept()
            else:
                QMessageBox.warning(
                    self, "Ошибка", "Неверный логин или пароль")

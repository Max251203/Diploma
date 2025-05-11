from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFormLayout,
    QMessageBox, QWidget, QToolButton, QHBoxLayout
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from core.db.users_db import UserDB


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход / Регистрация")
        self.setFixedSize(400, 460)
        self.setObjectName("loginDialog")

        self.db = UserDB()
        self.is_register_mode = False
        self.password_visible = False
        self.repeat_visible = False

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setSpacing(12)

        # Логин
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Введите логин")
        self.login_label = QLabel("Логин:")
        self.form_layout.addRow(self.login_label, self.login_edit)

        # Пароль
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Введите пароль")
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.toggle_password_btn = QToolButton()
        self.toggle_password_btn.setIcon(QIcon(":/icon/icons/eye.png"))
        self.toggle_password_btn.setIconSize(QSize(20, 20))
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)

        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_edit)
        password_layout.addWidget(self.toggle_password_btn)

        password_widget = QWidget()
        password_widget.setLayout(password_layout)
        self.password_label = QLabel("Пароль:")
        self.form_layout.addRow(self.password_label, password_widget)

        # Повтор пароля
        self.repeat_edit = QLineEdit()
        self.repeat_edit.setPlaceholderText("Повторите пароль")
        self.repeat_edit.setEchoMode(QLineEdit.Password)

        self.toggle_repeat_btn = QToolButton()
        self.toggle_repeat_btn.setIcon(QIcon(":/icon/icons/eye.png"))
        self.toggle_repeat_btn.setIconSize(QSize(20, 20))
        self.toggle_repeat_btn.clicked.connect(self.toggle_repeat_visibility)

        repeat_layout = QHBoxLayout()
        repeat_layout.addWidget(self.repeat_edit)
        repeat_layout.addWidget(self.toggle_repeat_btn)

        repeat_widget = QWidget()
        repeat_widget.setLayout(repeat_layout)
        self.repeat_label = QLabel("Повтор пароля:")
        self.form_layout.addRow(self.repeat_label, repeat_widget)

        # ФИО
        self.lastname_edit = QLineEdit()
        self.lastname_edit.setPlaceholderText("Введите фамилию")
        self.lastname_label = QLabel("Фамилия:")
        self.form_layout.addRow(self.lastname_label, self.lastname_edit)

        self.firstname_edit = QLineEdit()
        self.firstname_edit.setPlaceholderText("Введите имя")
        self.firstname_label = QLabel("Имя:")
        self.form_layout.addRow(self.firstname_label, self.firstname_edit)

        self.middlename_edit = QLineEdit()
        self.middlename_edit.setPlaceholderText("Введите отчество")
        self.middlename_label = QLabel("Отчество:")
        self.form_layout.addRow(self.middlename_label, self.middlename_edit)

        # Кнопки
        self.submit_btn = QPushButton("Войти")
        self.submit_btn.clicked.connect(self.on_submit)

        self.toggle_mode_btn = QPushButton("У меня нет аккаунта")
        self.toggle_mode_btn.clicked.connect(self.toggle_mode)

        main_layout.addWidget(self.form_container)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.submit_btn)
        main_layout.addWidget(self.toggle_mode_btn)
        main_layout.addStretch()

        self.set_register_mode(False)

    def toggle_password_visibility(self):
        self.password_visible = not self.password_visible
        mode = QLineEdit.Normal if self.password_visible else QLineEdit.Password
        self.password_edit.setEchoMode(mode)
        icon = QIcon(":/icon/icons/eye_off.png") if self.password_visible else QIcon(":/icon/icons/eye.png")
        self.toggle_password_btn.setIcon(icon)

    def toggle_repeat_visibility(self):
        self.repeat_visible = not self.repeat_visible
        mode = QLineEdit.Normal if self.repeat_visible else QLineEdit.Password
        self.repeat_edit.setEchoMode(mode)
        icon = QIcon(":/icon/icons/eye_off.png") if self.repeat_visible else QIcon(":/icon/icons/eye.png")
        self.toggle_repeat_btn.setIcon(icon)

    def toggle_mode(self):
        self.set_register_mode(not self.is_register_mode)

    def set_register_mode(self, is_register):
        self.is_register_mode = is_register

        self.repeat_edit.setVisible(is_register)
        self.repeat_label.setVisible(is_register)
        self.toggle_repeat_btn.setVisible(is_register)

        self.lastname_edit.setVisible(is_register)
        self.firstname_edit.setVisible(is_register)
        self.middlename_edit.setVisible(is_register)

        self.lastname_label.setVisible(is_register)
        self.firstname_label.setVisible(is_register)
        self.middlename_label.setVisible(is_register)

        self.submit_btn.setText("Зарегистрироваться" if is_register else "Войти")
        self.toggle_mode_btn.setText("Уже есть аккаунт" if is_register else "У меня нет аккаунта")

    def on_submit(self):
        login = self.login_edit.text().strip()
        password = self.password_edit.text()

        if self.is_register_mode:
            repeat = self.repeat_edit.text()
            if password != repeat:
                return QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")

            fields = [
                self.lastname_edit.text().strip(),
                self.firstname_edit.text().strip(),
                self.middlename_edit.text().strip(),
            ]
            if not login or not password or not all(fields):
                return QMessageBox.warning(self, "Ошибка", "Заполните все поля")

            try:
                self.db.add_user(login, password, *fields)
                QMessageBox.information(self, "Успех", "Вы успешно зарегистрированы")
                self.set_register_mode(False)
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка", str(e))
        else:
            user = self.db.authenticate_user(login, password)
            if user:
                self.user_data = user
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
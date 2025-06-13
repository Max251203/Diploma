from PySide6.QtWidgets import (
    QDialog, QLineEdit, QPushButton, QVBoxLayout, QFormLayout,
    QHBoxLayout, QToolButton, QMessageBox, QWidget, QCheckBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, QSettings
from core.api import api_client
from core.api.api_worker import LoginWorker, RegisterWorker


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход / Регистрация")
        self.setFixedSize(400, 300)
        self.user_data = None
        self.token = None
        self.is_register_mode = False
        self.is_guest_mode = False
        self._current_worker = None

        self._build_ui()
        self._set_register_mode(False)
        self._load_connection_settings()
        self._auto_connect()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.form = QFormLayout()
        self.form.setSpacing(12)

        self.login_edit = QLineEdit()
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

        self.lastname_edit = QLineEdit()
        self.form.addRow("Фамилия:", self.lastname_edit)
        self.firstname_edit = QLineEdit()
        self.form.addRow("Имя:", self.firstname_edit)
        self.middlename_edit = QLineEdit()
        self.form.addRow("Отчество:", self.middlename_edit)

        layout.addLayout(self.form)

        self.remember_cb = QCheckBox("Запомнить меня")
        self.remember_cb.setChecked(True)
        layout.addWidget(self.remember_cb)

        buttons_layout = QVBoxLayout()
        self.submit_btn = QPushButton("Войти")
        self.submit_btn.clicked.connect(self._on_submit)
        buttons_layout.addWidget(self.submit_btn)

        self.toggle_mode_btn = QPushButton("У меня нет аккаунта")
        self.toggle_mode_btn.clicked.connect(self._toggle_mode)
        buttons_layout.addWidget(self.toggle_mode_btn)

        self.guest_btn = QPushButton("Войти как гость")
        self.guest_btn.clicked.connect(self._login_as_guest)
        buttons_layout.addWidget(self.guest_btn)

        self.connection_btn = QPushButton("Настройки подключения")
        self.connection_btn.clicked.connect(self._open_connection_settings)
        buttons_layout.addWidget(self.connection_btn)

        layout.addLayout(buttons_layout)
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
        self.setFixedSize(400, 460 if register else 300)
        self.adjustSize()
        self.updateGeometry()

    def _load_connection_settings(self):
        settings = QSettings("IoTLab", "Connection")
        url = settings.value("url", "")
        api_key = settings.value("api_key", "")
        if url and api_key:
            api_client.configure(url, api_key)
            return True
        return False

    def _auto_connect(self):
        if api_client.check_connection():
            self.setWindowTitle("Вход / Регистрация - Подключено")
        else:
            self.setWindowTitle("Вход / Регистрация - Нет подключения")
            QMessageBox.warning(self, "Ошибка подключения",
                                "Не удалось подключиться к серверу. Проверьте настройки подключения.")

    def _open_connection_settings(self):
        from ui.dialogs.connection_dialog import ConnectionDialog
        dialog = ConnectionDialog(self)
        dialog.exec()
        self._load_connection_settings()
        self._auto_connect()

    def _on_submit(self):
        if not api_client.is_connected():
            QMessageBox.warning(self, "Ошибка подключения",
                                "Нет подключения к серверу. Проверьте настройки подключения.")
            return
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
            user_data = {
                "login": login,
                "password": password,
                "last_name": last,
                "first_name": first,
                "middle_name": middle,
                "role": "student"
            }
            self._current_worker = RegisterWorker(api_client, user_data)
            self._current_worker.result_ready.connect(
                self._on_register_success)
            self._current_worker.error_occurred.connect(self._show_error)
            self._current_worker.finished.connect(self._clear_worker)
            self._current_worker.start()
        else:
            if not login or not password:
                return QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            self._current_worker = LoginWorker(api_client, login, password)
            self._current_worker.result_ready.connect(self._on_login_success)
            self._current_worker.error_occurred.connect(self._show_error)
            self._current_worker.finished.connect(self._clear_worker)
            self._current_worker.start()

    def _clear_worker(self):
        self._current_worker = None

    def _on_login_success(self, result):
        if not result:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
            return
        self.user_data = result.get("user")
        self.token = result.get("access_token")
        api_client.set_token(self.token)
        if self.remember_cb.isChecked():
            settings = QSettings("IoTLab", "Auth")
            settings.setValue("token", self.token)
            settings.setValue("user_id", self.user_data.get("id"))
        self.accept()

    def _on_register_success(self, user):
        if not user:
            QMessageBox.warning(
                self, "Ошибка", "Не удалось зарегистрироваться")
            return
        QMessageBox.information(
            self, "Успех", "Вы успешно зарегистрированы! Теперь вы можете войти.")
        self._set_register_mode(False)
        self.login_edit.setText(user.get("login", ""))
        self.password_edit.clear()

    def _login_as_guest(self):
        if not api_client.is_connected():
            QMessageBox.warning(self, "Ошибка подключения",
                                "Нет подключения к серверу. Проверьте настройки подключения.")
            return
        self.user_data = {
            "id": 0,
            "login": "guest",
            "role": "guest",
            "last_name": "Гость",
            "first_name": "",
            "middle_name": ""
        }
        api_client.set_token("")
        self.is_guest_mode = True
        self.accept()

    def _show_error(self, error):
        QMessageBox.critical(self, "Ошибка", error)

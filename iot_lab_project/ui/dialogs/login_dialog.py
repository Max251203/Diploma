from PySide6.QtWidgets import (
    QDialog, QLineEdit, QPushButton, QVBoxLayout, QFormLayout,
    QHBoxLayout, QToolButton, QMessageBox, QWidget, QApplication
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from core.api import api_client
from core.logger import get_logger

logger = get_logger()


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход / Регистрация")
        self.setFixedSize(400, 300)
        self.user_data = None
        self.token = None
        self.is_register_mode = False
        logger.info("Инициализация LoginDialog")

        self._build_ui()
        self._set_register_mode(False)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.form = QFormLayout()
        self.form.setSpacing(12)

        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Введите логин")
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
        self.lastname_edit.setPlaceholderText("Введите фамилию")
        self.form.addRow("Фамилия:", self.lastname_edit)

        self.firstname_edit = QLineEdit()
        self.firstname_edit.setPlaceholderText("Введите имя")
        self.form.addRow("Имя:", self.firstname_edit)

        self.middlename_edit = QLineEdit()
        self.middlename_edit.setPlaceholderText("Введите отчество")
        self.form.addRow("Отчество:", self.middlename_edit)

        layout.addLayout(self.form)

        buttons_layout = QVBoxLayout()
        self.submit_btn = QPushButton("Войти")
        self.submit_btn.clicked.connect(self._on_submit)
        buttons_layout.addWidget(self.submit_btn)

        self.toggle_mode_btn = QPushButton("У меня нет аккаунта")
        self.toggle_mode_btn.clicked.connect(self._toggle_mode)
        buttons_layout.addWidget(self.toggle_mode_btn)

        layout.addLayout(buttons_layout)
        layout.addStretch()

        logger.info("UI LoginDialog построен")

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
        logger.info(
            f"Переключение режима на {'регистрацию' if not self.is_register_mode else 'вход'}")
        self._set_register_mode(not self.is_register_mode)
        self.toggle_mode_btn.clearFocus()
        self.toggle_mode_btn.setDown(False)

    def _set_register_mode(self, register: bool):
        self.is_register_mode = register
        logger.info(
            f"Установка режима: {'регистрация' if register else 'вход'}")

        # Сначала скрываем все дополнительные поля
        for field in [self.row_repeat, self.lastname_edit, self.firstname_edit, self.middlename_edit]:
            field.setVisible(register)
            if hasattr(self.form, "labelForField"):
                label = self.form.labelForField(field)
                if label:
                    label.setVisible(register)

        # Устанавливаем текст кнопок
        self.submit_btn.setText("Зарегистрироваться" if register else "Войти")
        self.toggle_mode_btn.setText(
            "Уже есть аккаунт" if register else "У меня нет аккаунта")

        # Изменяем размер окна
        self.setFixedSize(400, 460 if register else 220)

        # Обновляем геометрию окна
        self.adjustSize()
        self.updateGeometry()

    def _on_submit(self):
        # Отключаем кнопку, чтобы предотвратить повторные нажатия
        self.submit_btn.setEnabled(False)
        QApplication.processEvents()  # Обрабатываем события, чтобы UI обновился

        if not api_client.is_connected():
            logger.warning("Попытка входа без подключения к серверу")
            QMessageBox.warning(self, "Ошибка подключения",
                                "Нет подключения к серверу. Проверьте настройки подключения.")
            self.submit_btn.setEnabled(True)
            return

        login = self.login_edit.text().strip()
        password = self.password_edit.text()

        if self.is_register_mode:
            logger.info(f"Попытка регистрации пользователя: {login}")
            repeat = self.repeat_edit.text()
            last = self.lastname_edit.text().strip()
            first = self.firstname_edit.text().strip()
            middle = self.middlename_edit.text().strip()

            if not login or not password or not repeat or not last or not first or not middle:
                logger.warning("Не все поля заполнены при регистрации")
                QMessageBox.warning(self, "Ошибка", "Заполните все поля")
                self.submit_btn.setEnabled(True)
                return

            if password != repeat:
                logger.warning("Пароли не совпадают при регистрации")
                QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
                self.submit_btn.setEnabled(True)
                return

            user_data = {
                "login": login,
                "password": password,
                "last_name": last,
                "first_name": first,
                "middle_name": middle,
                "role": "student"
            }

            # Прямой вызов API для регистрации
            try:
                logger.info("Отправка запроса на регистрацию")
                result = api_client.register(user_data)
                if result:
                    logger.success(
                        f"Пользователь {login} успешно зарегистрирован")
                    QMessageBox.information(
                        self, "Успех", "Вы успешно зарегистрированы! Теперь вы можете войти.")
                    self._set_register_mode(False)
                    self.login_edit.setText(login)
                    self.password_edit.clear()
                else:
                    logger.error(f"Ошибка регистрации пользователя {login}")
                    QMessageBox.warning(
                        self, "Ошибка", "Не удалось зарегистрироваться")
            except Exception as e:
                logger.error(f"Исключение при регистрации: {str(e)}")
                QMessageBox.critical(self, "Ошибка", str(e))

            self.submit_btn.setEnabled(True)
        else:
            logger.info(f"Попытка входа пользователя: {login}")
            if not login or not password:
                logger.warning("Не заполнены логин или пароль при входе")
                QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
                self.submit_btn.setEnabled(True)
                return

            # Прямой вызов API для входа
            try:
                logger.info("Отправка запроса на вход")
                result = api_client.login(login, password)
                if result:
                    logger.success(
                        f"Пользователь {login} успешно вошел в систему")
                    self.user_data = result.get("user")
                    self.token = result.get("access_token")
                    api_client.set_token(self.token)
                    self.accept()
                else:
                    logger.warning(
                        f"Неверный логин или пароль для пользователя {login}")
                    QMessageBox.warning(
                        self, "Ошибка", "Неверный логин или пароль")
                    self.submit_btn.setEnabled(True)
            except Exception as e:
                logger.error(f"Исключение при входе: {str(e)}")
                QMessageBox.critical(self, "Ошибка", str(e))
                self.submit_btn.setEnabled(True)

    def closeEvent(self, event):
        logger.info("Закрытие диалога LoginDialog")
        event.accept()

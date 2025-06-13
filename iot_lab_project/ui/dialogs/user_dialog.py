from PySide6.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QLineEdit,
    QPushButton, QMessageBox, QComboBox, QHBoxLayout, QToolButton, QWidget
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Signal

from core.api import api_client
from core.api.api_worker import (
    GetUserWorker, CreateUserWorker, UpdateUserWorker
)
from core.permissions import get_all_roles, get_role_label, RoleEnum


class UserDialog(QDialog):
    user_saved = Signal(dict)

    def __init__(self, mode="profile", user_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self._get_title(mode))
        self.setMinimumWidth(400)
        self.setFixedHeight(340)
        self.mode = mode
        self.user_data = user_data or {}

        self._parent_user = self._find_current_user()
        self._is_self_edit = (
            self.mode == "edit" and self.user_data.get(
                "id") == self._parent_user.get("id")
        )

        self._build_ui()
        self._fill_fields()
        self._update_save_button_state()

    def _get_title(self, mode):
        return {
            "profile": "Редактирование профиля",
            "edit": "Редактирование пользователя",
            "add": "Добавление пользователя"
        }.get(mode, "Пользователь")

    def _find_current_user(self):
        """Поиск текущей учётки вверх по иерархии"""
        p = self.parent()
        while p:
            if hasattr(p, "user_data"):
                return p.user_data
            p = p.parent()
        return {}

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.form = QFormLayout()

        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Введите логин")
        self.login_edit.textChanged.connect(self._update_save_button_state)
        self.form.addRow("Логин:", self.login_edit)

        self.lastname_edit = QLineEdit()
        self.firstname_edit = QLineEdit()
        self.middlename_edit = QLineEdit()

        for field in [self.lastname_edit, self.firstname_edit, self.middlename_edit]:
            field.textChanged.connect(self._update_save_button_state)

        self.form.addRow("Фамилия:", self.lastname_edit)
        self.form.addRow("Имя:", self.firstname_edit)
        self.form.addRow("Отчество:", self.middlename_edit)

        self.password_edit, self.toggle_btn = self._create_password_field()
        self.password_edit.setPlaceholderText(
            "Введите пароль" if self.mode == "add" else "Новый пароль (необязательно)")
        self.password_edit.textChanged.connect(self._update_save_button_state)
        self.form.addRow("Пароль:", self._wrap_with_icon(
            self.password_edit, self.toggle_btn))

        if self.mode != "profile" and not self._is_self_edit:
            self.role_combo = QComboBox()
            self.role_combo.addItems(get_all_roles())
            self.role_combo.currentTextChanged.connect(
                self._update_save_button_state)
            self.role_combo.currentTextChanged.connect(
                self._update_placeholders)
            self.form.addRow("Роль:", self.role_combo)
        else:
            self.role_combo = None

        layout.addLayout(self.form)

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
        btn.toggled.connect(
            lambda checked: self._toggle_password_visibility(edit, btn, checked))
        return edit, btn

    def _toggle_password_visibility(self, field, btn, visible):
        field.setEchoMode(QLineEdit.Normal if visible else QLineEdit.Password)
        icon = QIcon(
            ":/icon/icons/eye_off.png") if visible else QIcon(":/icon/icons/eye.png")
        btn.setIcon(icon)

    def _wrap_with_icon(self, field, icon_btn):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(field)
        layout.addWidget(icon_btn)
        container = QWidget()
        container.setLayout(layout)
        return container

    def _fill_fields(self):
        self.login_edit.setText(self.user_data.get("login", ""))
        self.lastname_edit.setText(self.user_data.get("last_name", ""))
        self.firstname_edit.setText(self.user_data.get("first_name", ""))
        self.middlename_edit.setText(self.user_data.get("middle_name", ""))

        if self.role_combo and self.mode != "add":
            self.role_combo.setCurrentText(
                self.user_data.get("role", RoleEnum.STUDENT.value))

        self._update_placeholders()

    def _update_placeholders(self):
        role = self.role_combo.currentText() if self.role_combo else self.user_data.get(
            "role", RoleEnum.STUDENT.value)
        label = get_role_label(role)
        is_admin = role == RoleEnum.ADMIN.value
        def hint(
            r): return f"{'Обязательно' if r else 'Необязательно'} для роли: {label}"

        self.lastname_edit.setPlaceholderText(hint(not is_admin))
        self.firstname_edit.setPlaceholderText(hint(not is_admin))
        self.middlename_edit.setPlaceholderText(hint(not is_admin))

    def _has_changes(self):
        if self.user_data.get("login", "") != self.login_edit.text().strip():
            return True

        for key, field in [
            ("last_name", self.lastname_edit),
            ("first_name", self.firstname_edit),
            ("middle_name", self.middlename_edit)
        ]:
            if self.user_data.get(key, "") != field.text().strip():
                return True

        if self.role_combo and self.role_combo.currentText() != self.user_data.get("role"):
            return True

        if self.password_edit.text():
            return True

        return False

    def _update_save_button_state(self):
        self.save_btn.setEnabled(self._has_changes())

    def _save_user(self):
        login = self.login_edit.text().strip()
        last = self.lastname_edit.text().strip()
        first = self.firstname_edit.text().strip()
        middle = self.middlename_edit.text().strip()
        password = self.password_edit.text().strip()
        role = self.role_combo.currentText() if self.role_combo else self.user_data.get("role")

        if not login:
            return QMessageBox.warning(self, "Ошибка", "Логин обязателен.")

        # Обязательное ФИО только для студента и преподавателя
        if role in [RoleEnum.STUDENT.value, RoleEnum.TEACHER.value]:
            if not (last and first and middle):
                return QMessageBox.warning(self, "Ошибка", "ФИО обязательно для выбранной роли.")

        if self.mode == "add" and not password:
            return QMessageBox.warning(self, "Ошибка", "Пароль обязателен при добавлении.")

        try:
            if self.mode == "add":
                # Создание нового пользователя через API
                user_data = {
                    "login": login,
                    "password": password,
                    "last_name": last,
                    "first_name": first,
                    "middle_name": middle,
                    "role": role
                }

                worker = CreateUserWorker(api_client, user_data)
                worker.result_ready.connect(self._on_user_created)
                worker.error_occurred.connect(self._show_error)
                worker.start()
            else:
                # Обновление существующего пользователя через API
                user_data = {
                    "login": login,
                    "last_name": last,
                    "first_name": first,
                    "middle_name": middle,
                    "role": role
                }

                if password:
                    user_data["password"] = password

                worker = UpdateUserWorker(
                    api_client, self.user_data["id"], user_data)
                worker.result_ready.connect(self._on_user_updated)
                worker.error_occurred.connect(self._show_error)
                worker.start()

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def _on_user_created(self, user):
        """Обработка успешного создания пользователя"""
        if not user:
            QMessageBox.warning(
                self, "Ошибка", "Не удалось создать пользователя")
            return

        QMessageBox.information(self, "Успех", "Пользователь добавлен.")
        self.user_saved.emit(user)
        self.accept()

    def _on_user_updated(self, user):
        """Обработка успешного обновления пользователя"""
        if not user:
            QMessageBox.warning(
                self, "Ошибка", "Не удалось обновить пользователя")
            return

        QMessageBox.information(self, "Успех", "Данные обновлены.")
        self.user_saved.emit(user)
        self.accept()

    def _show_error(self, error):
        """Отображение ошибки"""
        QMessageBox.warning(self, "Ошибка", error)

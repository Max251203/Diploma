from PySide6.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QLineEdit,
    QPushButton, QMessageBox, QComboBox, QHBoxLayout, QToolButton, QWidget
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Signal
from db.users_db import UserDB

class UserDialog(QDialog):
    user_saved = Signal(dict)  # Сигнал для обновления профиля и таблицы

    def __init__(self, mode="profile", user_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self._get_title(mode))
        self.setMinimumWidth(400)
        self.setFixedHeight(340)
        self.mode = mode
        self.user_data = user_data or {}
        self.db = UserDB()
        self.original_data = self.user_data.copy()

        self._build_ui()
        self._fill_fields()
        self._update_save_button_state()

    def _get_title(self, mode):
        return {
            "profile": "Редактирование профиля",
            "edit": "Редактирование пользователя",
            "add": "Добавление пользователя"
        }.get(mode, "Пользователь")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.login_edit = QLineEdit(placeholderText="Обязательное поле")
        self.login_edit.textChanged.connect(self._update_save_button_state)
        form.addRow("Логин:", self.login_edit)

        self.lastname_edit = QLineEdit()
        self.firstname_edit = QLineEdit()
        self.middlename_edit = QLineEdit()
        self.lastname_edit.textChanged.connect(self._update_save_button_state)
        self.firstname_edit.textChanged.connect(self._update_save_button_state)
        self.middlename_edit.textChanged.connect(self._update_save_button_state)
        form.addRow("Фамилия:", self.lastname_edit)
        form.addRow("Имя:", self.firstname_edit)
        form.addRow("Отчество:", self.middlename_edit)

        self.password_edit, self.toggle_btn = self._create_password_field()
        self.password_edit.setPlaceholderText("Новый пароль (не обязательно)")
        self.password_edit.textChanged.connect(self._update_save_button_state)
        form.addRow("Пароль:", self._wrap_with_icon(self.password_edit, self.toggle_btn))

        self.role_combo = QComboBox()
        self.role_combo.addItems(["student", "teacher", "admin"])
        if self.mode != "profile":
            self.role_combo.currentTextChanged.connect(self._update_placeholders)
            self.role_combo.currentTextChanged.connect(self._update_save_button_state)
            form.addRow("Роль:", self.role_combo)

        layout.addLayout(form)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self._save_user)
        layout.addWidget(self.save_btn)
        self.save_btn.setEnabled(False)

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
        self._update_placeholders()
        self.password_edit.clear()

    def _update_placeholders(self):
        role = self.role_combo.currentText() if self.mode != "profile" else self.user_data.get("role", "student")
        if role == "admin":
            self.lastname_edit.setPlaceholderText("Не обязательно для администратора")
            self.firstname_edit.setPlaceholderText("Не обязательно для администратора")
            self.middlename_edit.setPlaceholderText("Не обязательно для администратора")
        else:
            self.lastname_edit.setPlaceholderText("Обязательное поле")
            self.firstname_edit.setPlaceholderText("Обязательное поле")
            self.middlename_edit.setPlaceholderText("Обязательное поле")
        self.password_edit.setPlaceholderText("Новый пароль (не обязательно)")

    def _has_changes(self):
        fields = [
            ("login", self.login_edit.text().strip()),
            ("last_name", self.lastname_edit.text().strip()),
            ("first_name", self.firstname_edit.text().strip()),
            ("middle_name", self.middlename_edit.text().strip()),
        ]
        for key, val in fields:
            if self.user_data.get(key, "") != val:
                return True
        if self.mode != "add":
            current_role = self.role_combo.currentText() if self.mode != "profile" else self.user_data.get("role", "student")
            if current_role != self.user_data.get("role", "student"):
                return True
        if self.password_edit.text().strip():
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
        role = self.role_combo.currentText() if self.mode != "profile" else self.user_data.get("role", "student")

        if not self._has_changes():
            QMessageBox.warning(self, "Внимание", "Нет изменений для сохранения")
            return

        if not login:
            return QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля")
        if role == "admin":
            if self.mode == "add" and not password:
                return QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля")
        else:
            if not last or not first or not middle:  
                return QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля")
            if self.mode == "add" and not password:
                return QMessageBox.warning(self, "Ошибка", "Заполните обязательные поля")

        try:
            if self.mode == "add":
                self.db.add_user(login, password, last, first, middle, role)
                user = self.db.get_user_by_login(login)
                QMessageBox.information(self, "Успех", "Пользователь добавлен!")
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
                user = self.db.get_user_by_login(login)
                QMessageBox.information(self, "Успех", "Данные успешно обновлены!")
            self.user_saved.emit(user)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
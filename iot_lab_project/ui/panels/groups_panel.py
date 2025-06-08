from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QHBoxLayout, QInputDialog
)
from core.adapters.api_adapter import APIAdapter
import requests
import json


class GroupsPanel(QWidget):
    def __init__(self, adapter: APIAdapter, parent=None):
        super().__init__(parent)
        self.adapter = adapter
        self.groups_data = []

        self.list = QListWidget()
        self.title_label = QLabel("Список групп устройств:")

        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_add = QPushButton("➕ Добавить")
        self.btn_edit = QPushButton("✏️ Изменить")
        self.btn_delete = QPushButton("🗑 Удалить")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.list)

        btns_layout = QHBoxLayout()
        btns_layout.addWidget(self.btn_refresh)
        btns_layout.addWidget(self.btn_add)
        btns_layout.addWidget(self.btn_edit)
        btns_layout.addWidget(self.btn_delete)
        layout.addLayout(btns_layout)

        # Связи
        self.btn_refresh.clicked.connect(self._load_groups)
        self.btn_add.clicked.connect(self._create_group)
        self.btn_edit.clicked.connect(self._edit_group)
        self.btn_delete.clicked.connect(self._delete_group)

        self._load_groups()

    def _load_groups(self):
        self.list.clear()
        try:
            res = requests.get(
                f"{self.adapter.url}/api/groups",
                headers={"x-api-key": self.adapter.api_key}
            )
            if res.ok:
                self.groups_data = res.json()
                for group in self.groups_data:
                    name = group.get("name", "Без названия")
                    desc = group.get("description", "")
                    devs = group.get("devices", [])
                    item = QListWidgetItem(
                        f"{name} ({len(devs)} устройств): {desc}")
                    item.setData(1000, group)  # сохраняем весь объект группы
                    self.list.addItem(item)
            else:
                self.list.addItem(f"Ошибка загрузки: {res.status_code}")
        except Exception as e:
            self.list.addItem(f"Ошибка: {e}")

    def _create_group(self):
        name, ok = QInputDialog.getText(
            self, "Добавить группу", "Название группы:")
        if not ok or not name.strip():
            return

        try:
            res = requests.post(
                f"{self.adapter.url}/api/groups",
                headers={"x-api-key": self.adapter.api_key},
                json={
                    "name": name.strip(),
                    "description": "Добавлено через GUI",
                    "devices": []
                }
            )
            if res.ok:
                QMessageBox.information(self, "Успех", "Группа добавлена.")
                self._load_groups()
            else:
                QMessageBox.warning(self, "Ошибка", f"Код: {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _edit_group(self):
        selected = self.list.currentItem()
        if not selected:
            QMessageBox.warning(
                self, "Ошибка", "Выберите группу для редактирования.")
            return

        group: dict = selected.data(1000)
        current_name = group.get("name", "")
        current_desc = group.get("description", "")
        current_devs = group.get("devices", [])

        new_name, ok = QInputDialog.getText(
            self, "Редактировать группу", "Новое имя:", text=current_name)
        if not ok or not new_name.strip():
            return

        # Пока состав устройств остаётся как есть, редактируем имя/описание
        new_desc, ok = QInputDialog.getText(
            self, "Описание группы", "Описание:", text=current_desc)
        if not ok:
            return

        try:
            res = requests.put(
                f"{self.adapter.url}/api/groups/{group['id']}",
                headers={"x-api-key": self.adapter.api_key},
                json={
                    "name": new_name.strip(),
                    "description": new_desc.strip(),
                    "devices": current_devs
                }
            )
            if res.ok:
                QMessageBox.information(self, "Успех", "Группа обновлена.")
                self._load_groups()
            else:
                QMessageBox.warning(self, "Ошибка", f"Код: {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _delete_group(self):
        selected = self.list.currentItem()
        if not selected:
            QMessageBox.warning(
                self, "Ошибка", "Выберите группу для удаления.")
            return

        group = selected.data(1000)
        confirm = QMessageBox.question(
            self, "Удаление группы",
            f"Удалить группу: {group['name']}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            res = requests.delete(
                f"{self.adapter.url}/api/groups/{group['id']}",
                headers={"x-api-key": self.adapter.api_key}
            )
            if res.ok:
                QMessageBox.information(self, "Удалено", "Группа удалена.")
                self._load_groups()
            else:
                QMessageBox.warning(
                    self, "Ошибка", f"Удаление не удалось: код {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

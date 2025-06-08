from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QHBoxLayout, QInputDialog
)
from core.adapters.api_adapter import APIAdapter
from ui.dialogs.automation_dialog import AutomationDialog
import requests
import json


class AutomationsPanel(QWidget):
    def __init__(self, adapter: APIAdapter, parent=None):
        super().__init__(parent)
        self.adapter = adapter
        self.automations_data = []

        self.title_label = QLabel("Автоматизации:")
        self.list = QListWidget()

        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_add = QPushButton("➕ Добавить")
        self.btn_toggle = QPushButton("🔁 Переключить")
        self.btn_delete = QPushButton("🗑 Удалить")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.list)

        row = QHBoxLayout()
        row.addWidget(self.btn_refresh)
        row.addWidget(self.btn_add)
        row.addWidget(self.btn_toggle)
        row.addWidget(self.btn_delete)
        layout.addLayout(row)

        self.btn_refresh.clicked.connect(self._load)
        self.btn_add.clicked.connect(self._add)
        self.btn_toggle.clicked.connect(self._toggle)
        self.btn_delete.clicked.connect(self._delete)

        self._load()

    def _load(self):
        self.list.clear()
        try:
            res = requests.get(f"{self.adapter.url}/api/automations",
                               headers={"x-api-key": self.adapter.api_key})
            if res.ok:
                self.automations_data = res.json()
                for a in self.automations_data:
                    name = a["name"]
                    desc = a.get("description", "")
                    enabled = "🟢" if a["enabled"] else "🔴"
                    item = QListWidgetItem(f"{enabled} {name} — {desc}")
                    item.setData(1000, a)  # Сохраняем объект
                    self.list.addItem(item)
            else:
                self.list.addItem(f"Ошибка: {res.status_code}")
        except Exception as e:
            self.list.addItem(f"Ошибка: {e}")

    def _add(self):
        dialog = AutomationDialog(self.adapter, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                res = requests.post(
                    f"{self.adapter.url}/api/automations",
                    headers={"x-api-key": self.adapter.api_key},
                    json=data
                )
                if res.ok:
                    QMessageBox.information(
                        self, "Успех", "Автоматизация добавлена.")
                    self._load()
                else:
                    QMessageBox.warning(
                        self, "Ошибка", f"Код: {res.status_code}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _toggle(self):
        selected = self.list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите автоматизацию.")
            return

        auto = selected.data(1000)
        auto_id = auto["id"]

        try:
            res = requests.post(f"{self.adapter.url}/api/automations/{auto_id}/toggle",
                                headers={"x-api-key": self.adapter.api_key})
            if res.ok:
                QMessageBox.information(self, "OK", "Статус изменён.")
                self._load()
            else:
                QMessageBox.warning(self, "Ошибка", f"Код: {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _delete(self):
        selected = self.list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите автоматизацию.")
            return

        auto = selected.data(1000)

        confirm = QMessageBox.question(
            self, "Удалить?", f"Удалить: {auto['name']}?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return

        try:
            res = requests.delete(
                f"{self.adapter.url}/api/automations/{auto['id']}", headers={"x-api-key": self.adapter.api_key})
            if res.ok:
                QMessageBox.information(
                    self, "Удалена", "Автоматизация удалена.")
                self._load()
            else:
                QMessageBox.warning(self, "Ошибка", f"Код: {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

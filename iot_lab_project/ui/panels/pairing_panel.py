from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget,
    QHBoxLayout, QListWidgetItem, QMessageBox, QInputDialog
)
from PySide6.QtCore import QTimer
from core.adapters.api_adapter import APIAdapter
import requests


class PairingPanel(QWidget):
    def __init__(self, adapter: APIAdapter, parent=None):
        super().__init__(parent)
        self.adapter = adapter

        self.layout = QVBoxLayout(self)

        self.status_label = QLabel("Статус: —")
        self.found_list = QListWidget()

        self.btn_start = QPushButton("🔓 Начать сопряжение")
        self.btn_stop = QPushButton("🛑 Остановить")
        self.btn_add = QPushButton("➕ Добавить выбранное")

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(QLabel("Обнаруженные устройства:"))
        self.layout.addWidget(self.found_list)

        row = QHBoxLayout()
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_stop)
        row.addWidget(self.btn_add)
        self.layout.addLayout(row)

        self.btn_start.clicked.connect(self._start)
        self.btn_stop.clicked.connect(self._stop)
        self.btn_add.clicked.connect(self._add_device)

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_status)
        self.timer.start(2000)

    def _update_status(self):
        try:
            res = requests.get(f"{self.adapter.url}/api/pairing/status",
                               headers={"x-api-key": self.adapter.api_key})
            if res.ok:
                data = res.json()
                if data["active"]:
                    time_left = int(data["time_left"])
                    msg = f"🔄 Активно — осталось {time_left} сек."
                else:
                    msg = "❌ Выключено"
                    self.timer.stop()

                self.status_label.setText("Статус: " + msg)

                self.found_list.clear()
                for dev in data.get("discovered_devices", []):
                    ieee = dev.get("id", "???")
                    name = dev["info"].get("friendly_name", "Безымянный")
                    item = QListWidgetItem(f"{name} ({ieee})")
                    item.setData(1000, ieee)
                    self.found_list.addItem(item)
            else:
                self.status_label.setText(f"Ошибка: {res.status_code}")
        except Exception as e:
            self.status_label.setText("Ошибка подключения: " + str(e))

    def _start(self):
        time_value, ok = QInputDialog.getInt(
            self, "Сопряжение", "Введите длительность (сек):", value=60, minValue=10, maxValue=300
        )
        if not ok:
            return

        try:
            res = requests.post(
                f"{self.adapter.url}/api/pairing/start",
                headers={"x-api-key": self.adapter.api_key},
                json={"duration": time_value}
            )
            if res.ok:
                QMessageBox.information(self, "Успех", "Сопряжение запущено.")
                self.timer.start(2000)
                self._update_status()
            else:
                QMessageBox.warning(
                    self, "Ошибка", f"Сервер вернул код {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _stop(self):
        try:
            res = requests.post(
                f"{self.adapter.url}/api/pairing/stop",
                headers={"x-api-key": self.adapter.api_key}
            )
            if res.ok:
                QMessageBox.information(
                    self, "Остановлено", "Сопряжение остановлено.")
                self.timer.stop()
                self._update_status()
            else:
                QMessageBox.warning(self, "Ошибка", f"Код {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _add_device(self):
        selected = self.found_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите устройство.")
            return

        ieee = selected.data(1000)

        try:
            res = requests.post(
                f"{self.adapter.url}/api/devices/add/{ieee}",
                headers={"x-api-key": self.adapter.api_key}
            )
            if res.ok:
                QMessageBox.information(
                    self, "Добавлено", "Устройство добавлено.")
                self._update_status()
            else:
                QMessageBox.warning(self, "Ошибка", f"Код: {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

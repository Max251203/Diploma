import json
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QComboBox,
    QLineEdit, QLabel, QDialogButtonBox, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from core.adapters.api_adapter import APIAdapter


class AutomationDialog(QDialog):
    def __init__(self, adapter: APIAdapter, mode="add", automation_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Автоматизация")
        self.setMinimumWidth(400)
        self.adapter = adapter
        self.mode = mode
        self.automation_data = automation_data or {}

        self._build_ui()
        if self.mode == "edit":
            self._fill_fields()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.name_edit = QLineEdit()
        form.addRow("Название:", self.name_edit)

        self.desc_edit = QLineEdit()
        form.addRow("Описание:", self.desc_edit)

        self.enabled_cb = QCheckBox("Включено")
        self.enabled_cb.setChecked(True)
        layout.addWidget(self.enabled_cb)

        self.trigger_type = QComboBox()
        self.trigger_type.addItems(
            ["Время (по часу)", "Событие от устройства"])
        self.trigger_type.currentIndexChanged.connect(self._switch_trigger)
        form.addRow("Триггер:", self.trigger_type)

        # Варианты триггера
        self.trigger_time_edit = QLineEdit("12:00")
        form.addRow("⏰ Время (чч:мм):", self.trigger_time_edit)

        # Eсли триггер от устройства — покамест скрыт (TODO)
        self.trigger_device_id = QLineEdit()
        self.trigger_device_id.setPlaceholderText("sensor.temperature1")
        form.addRow("🧭 ID устройства:", self.trigger_device_id)
        self.trigger_device_prop = QLineEdit("temperature")
        form.addRow("💡 Свойство:", self.trigger_device_prop)
        self.trigger_condition = QComboBox()
        self.trigger_condition.addItems(["eq", "ne", "gt", "lt", "gte", "lte"])
        form.addRow("⚙️ Условие:", self.trigger_condition)
        self.trigger_value = QLineEdit("25")
        self.trigger_value.setValidator(QIntValidator())
        form.addRow("🎯 Значение:", self.trigger_value)

        # Только одно будет отображаться
        self._switch_trigger(0)

        self.action_type = QComboBox()
        self.action_type.addItems(["Уведомление", "Команда устройству"])
        self.action_type.currentIndexChanged.connect(self._switch_action)
        form.addRow("Действие:", self.action_type)

        self.action_msg = QLineEdit("Сработала автоматизация!")
        form.addRow("🔔 Сообщение:", self.action_msg)

        self.action_device_id = QLineEdit("relay1")
        form.addRow("📡 ID устройства:", self.action_device_id)
        self.action_device_cmd = QLineEdit('{"state": "ON"}')
        form.addRow("⚡ Команда:", self.action_device_cmd)

        # Скрыть по умолчанию
        self._switch_action(0)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def _switch_trigger(self, index):
        is_time = index == 0
        self.trigger_time_edit.setVisible(is_time)

        self.trigger_device_id.setVisible(not is_time)
        self.trigger_device_prop.setVisible(not is_time)
        self.trigger_condition.setVisible(not is_time)
        self.trigger_value.setVisible(not is_time)

    def _switch_action(self, index):
        is_notif = (index == 0)
        self.action_msg.setVisible(is_notif)

        self.action_device_id.setVisible(not is_notif)
        self.action_device_cmd.setVisible(not is_notif)

    def _fill_fields(self):
        a = self.automation_data
        self.name_edit.setText(a.get("name", ""))
        self.desc_edit.setText(a.get("description", ""))
        self.enabled_cb.setChecked(a.get("enabled", True))
        # TODO: Продумать заполнение триггера / экшена

    def get_data(self) -> dict:
        # Триггер
        trigger_block = {}
        if self.trigger_type.currentIndex() == 0:
            # Время
            trigger_block = {
                "type": "time",
                "time": self.trigger_time_edit.text().strip()
            }
        else:
            trigger_block = {
                "type": "device",
                "device_id": self.trigger_device_id.text().strip(),
                "property": self.trigger_device_prop.text().strip(),
                "condition": self.trigger_condition.currentText(),
                "value": self.trigger_value.text().strip()
            }

        # Действие
        actions = []
        if self.action_type.currentIndex() == 0:
            # Уведомление
            actions.append({
                "type": "notification",
                "message": self.action_msg.text().strip()
            })
        else:
            actions.append({
                "type": "device_command",
                "device_id": self.action_device_id.text().strip(),
                "command": json.loads(self.action_device_cmd.text().strip())
            })

        return {
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
            "enabled": self.enabled_cb.isChecked(),
            "trigger": trigger_block,
            "actions": actions
        }

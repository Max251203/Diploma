from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

class DeviceCard(QWidget):
    def __init__(self, device: dict, entity_manager, parent=None):
        super().__init__(parent)
        self.device = device
        self.entity_manager = entity_manager

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.setStyleSheet("border: 1px solid #ccc; border-radius: 6px; padding: 8px;")

        name = device.get("name", "Без названия")
        manufacturer = device.get("manufacturer", "Неизвестно")
        model = device.get("model", "Неизвестно")

        self.title = QLabel(f"<b>{name}</b><br>{manufacturer} {model}")
        self.title.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.title)

        entities = device.get("entities", [])
        for entity in entities:
            eid = entity.get("entity_id")
            if not eid:
                continue
            state = self.entity_manager.get_state(eid)
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{eid}: {state}"))

            domain = eid.split(".")[0]
            if domain in ["light", "switch", "fan", "cover"]:
                btn = QPushButton("Toggle")
                btn.clicked.connect(lambda _, e=eid: self.toggle_entity(e))
                row.addWidget(btn)

            self.layout.addLayout(row)

    def toggle_entity(self, entity_id):
        self.entity_manager.toggle(entity_id)
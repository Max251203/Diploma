from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

class EntityWidget(QFrame):
    """Виджет для отображения сущности"""
    control_requested = Signal(str, str)  # entity_id, action
    
    def __init__(self, entity, parent=None):
        super().__init__(parent)
        self.entity = entity
        self.entity_id = entity.get("entity_id", "unknown")
        self.entity_type = self.entity_id.split('.')[0]
        
        self.setObjectName("entityItemFrame")
        self.setFrameShape(QFrame.StyledPanel)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QGridLayout(self)
        
        # Название и ID
        entity_name = self.entity.get("original_name", self.entity.get("name", "—"))
        layout.addWidget(QLabel(f"<b>{entity_name}</b>"), 0, 0, 1, 2)
        layout.addWidget(QLabel(f"ID: {self.entity_id}"), 1, 0, 1, 2)
        
        # Метка состояния
        self.state_label = QLabel("Состояние: загрузка...")
        self.state_label.setObjectName(f"state_{self.entity_id}")
        layout.addWidget(self.state_label, 2, 0, 1, 2)
        
        # Элементы управления
        if self.entity_type in ["light", "switch", "fan"]:
            self._add_toggle_controls(layout)
        elif self.entity_type == "cover":
            self._add_cover_controls(layout)
    
    def _add_toggle_controls(self, layout):
        btn_on = QPushButton("Включить")
        btn_off = QPushButton("Выключить")
        
        btn_on.clicked.connect(lambda: self.control_requested.emit(self.entity_id, "turn_on"))
        btn_off.clicked.connect(lambda: self.control_requested.emit(self.entity_id, "turn_off"))
        
        layout.addWidget(btn_on, 3, 0)
        layout.addWidget(btn_off, 3, 1)
    
    def _add_cover_controls(self, layout):
        btn_open = QPushButton("Открыть")
        btn_close = QPushButton("Закрыть")
        
        btn_open.clicked.connect(lambda: self.control_requested.emit(self.entity_id, "open_cover"))
        btn_close.clicked.connect(lambda: self.control_requested.emit(self.entity_id, "close_cover"))
        
        layout.addWidget(btn_open, 3, 0)
        layout.addWidget(btn_close, 3, 1)
    
    def update_state(self, state_data):
        """Обновляет отображение состояния"""
        if not state_data:
            self.state_label.setText("Состояние: недоступно")
            return
            
        state = state_data.get("state", "unknown")
        attributes = state_data.get("attributes", {})
        
        # Форматируем состояние
        if self.entity_type == "sensor":
            unit = attributes.get("unit_of_measurement", "")
            formatted = f"{state} {unit}"
        elif self.entity_type in ["binary_sensor", "switch", "light"]:
            formatted = "Включено" if state == "on" else "Выключено"
        elif self.entity_type == "cover":
            formatted = "Открыто" if state == "open" else "Закрыто"
        else:
            formatted = state
            
        self.state_label.setText(f"Состояние: {formatted}")
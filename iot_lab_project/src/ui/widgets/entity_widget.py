from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal

class EntityWidget(QFrame):
    """Виджет для отображения сущности"""
    control_requested = Signal(str, str)  
    
    def __init__(self, entity, parent=None):
        super().__init__(parent)
        self.entity = entity
        self.entity_id = entity.get("entity_id", "unknown")
        self.entity_type = self.entity_id.split('.')[0]
        
        self.setObjectName("entityItemFrame")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QGridLayout(self)
        
        # Название и ID
        entity_name = self.entity.get("original_name", self.entity.get("name", "—"))
        name_label = QLabel(f"<b>{entity_name}</b>")
        name_label.setStyleSheet("font-size: 12px; color: #c6e2ff;")
        layout.addWidget(name_label, 0, 0, 1, 2)
        
        id_label = QLabel(f"ID: {self.entity_id}")
        id_label.setStyleSheet("font-size: 10px; color: #a0c0e0;")
        layout.addWidget(id_label, 1, 0, 1, 2)
        
        # Метка состояния
        self.state_label = QLabel("Состояние: загрузка...")
        self.state_label.setObjectName(f"state_{self.entity_id}")
        self.state_label.setStyleSheet("font-size: 11px; color: #ffcc00;")
        layout.addWidget(self.state_label, 2, 0, 1, 2)
        
        # Элементы управления
        if self.entity_type in ["light", "switch", "fan"]:
            self._add_toggle_controls(layout)
        elif self.entity_type == "cover":
            self._add_cover_controls(layout)
    
    def _add_toggle_controls(self, layout):
        control_frame = QFrame()
        control_frame.setObjectName("entityControlFrame")
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 5, 0, 0)
        
        btn_on = QPushButton("Включить")
        btn_on.setStyleSheet("min-height: 25px; font-size: 10px;")
        btn_off = QPushButton("Выключить")
        btn_off.setStyleSheet("min-height: 25px; font-size: 10px;")
        
        btn_on.clicked.connect(lambda: self.control_requested.emit(self.entity_id, "turn_on"))
        btn_off.clicked.connect(lambda: self.control_requested.emit(self.entity_id, "turn_off"))
        
        control_layout.addWidget(btn_on)
        control_layout.addWidget(btn_off)
        
        layout.addWidget(control_frame, 3, 0, 1, 2)
    
    def _add_cover_controls(self, layout):
        control_frame = QFrame()
        control_frame.setObjectName("entityControlFrame")
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 5, 0, 0)
        
        btn_open = QPushButton("Открыть")
        btn_open.setStyleSheet("min-height: 25px; font-size: 10px;")
        btn_close = QPushButton("Закрыть")
        btn_close.setStyleSheet("min-height: 25px; font-size: 10px;")
        
        btn_open.clicked.connect(lambda: self.control_requested.emit(self.entity_id, "open_cover"))
        btn_close.clicked.connect(lambda: self.control_requested.emit(self.entity_id, "close_cover"))
        
        control_layout.addWidget(btn_open)
        control_layout.addWidget(btn_close)
        
        layout.addWidget(control_frame, 3, 0, 1, 2)
    
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
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QGridLayout, 
                             QPushButton, QFrame, QScrollArea, QMessageBox, QWidget)

class DeviceDetailDialog(QDialog):
    def __init__(self, device, entity_manager, parent=None):
        super().__init__(parent)
        self.device = device
        self.entity_manager = entity_manager
        
        self.setWindowTitle(f"Устройство: {device['name']}")
        self.setMinimumSize(600, 400)
        
        self.main_layout = QVBoxLayout(self)
        
        # Информация об устройстве
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_layout = QGridLayout(info_frame)
        
        info_layout.addWidget(QLabel("<b>Название:</b>"), 0, 0)
        info_layout.addWidget(QLabel(device['name']), 0, 1)
        
        info_layout.addWidget(QLabel("<b>Производитель:</b>"), 1, 0)
        info_layout.addWidget(QLabel(device['manufacturer']), 1, 1)
        
        info_layout.addWidget(QLabel("<b>Модель:</b>"), 2, 0)
        info_layout.addWidget(QLabel(device['model']), 2, 1)
        
        info_layout.addWidget(QLabel("<b>ID:</b>"), 3, 0)
        info_layout.addWidget(QLabel(device['id']), 3, 1)
        
        self.main_layout.addWidget(info_frame)
        
        # Список сущностей
        self.main_layout.addWidget(QLabel("<h3>Сущности:</h3>"))
        
        entities_scroll = QScrollArea()
        entities_scroll.setWidgetResizable(True)
        entities_widget = QWidget()
        entities_layout = QVBoxLayout(entities_widget)
        
        for entity in device['entities']:
            entity_frame = self._create_entity_widget(entity)
            entities_layout.addWidget(entity_frame)
        
        entities_scroll.setWidget(entities_widget)
        self.main_layout.addWidget(entities_scroll)
        
        # Кнопка закрытия
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        self.main_layout.addWidget(close_button)
    
    def _create_entity_widget(self, entity):
        """Создает виджет для отображения сущности"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.2);
                border: 1px solid rgb(0, 191, 255);
                border-radius: 5px;
                margin: 2px;
            }
        """)
        
        layout = QGridLayout(frame)
        
        entity_id = entity.get("entity_id", "unknown")
        entity_name = entity.get("original_name", entity.get("name", "—"))
        entity_type = entity_id.split('.')[0]
        
        layout.addWidget(QLabel(f"<b>{entity_name}</b>"), 0, 0, 1, 2)
        layout.addWidget(QLabel(f"ID: {entity_id}"), 1, 0)
        layout.addWidget(QLabel(f"Тип: {entity_type}"), 1, 1)
        
        # Добавляем кнопки управления в зависимости от типа сущности
        if entity_type in ["light", "switch", "fan", "cover"]:
            btn_on = QPushButton("Включить")
            btn_off = QPushButton("Выключить")
            
            btn_on.clicked.connect(lambda: self._control_entity(entity_id, "turn_on"))
            btn_off.clicked.connect(lambda: self._control_entity(entity_id, "turn_off"))
            
            layout.addWidget(btn_on, 2, 0)
            layout.addWidget(btn_off, 2, 1)
        
        return frame
    
    def _control_entity(self, entity_id, action):
        """Управляет сущностью"""
        try:
            domain = entity_id.split('.')[0]
            self.entity_manager.ws.send_command("call_service", {
                "domain": domain,
                "service": action,
                "service_data": {"entity_id": entity_id}
            })
            QMessageBox.information(self, "Успех", f"Команда {action} отправлена на {entity_id}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить действие: {str(e)}")
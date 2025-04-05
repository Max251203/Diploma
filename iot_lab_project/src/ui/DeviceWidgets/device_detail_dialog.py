from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QGridLayout, 
                             QPushButton, QFrame, QScrollArea, QMessageBox, QWidget)
from PySide6.QtCore import Qt

# Добавим новый класс в device_detail_dialog.py
from PySide6.QtCore import QThread, Signal

class EntityStateLoader(QThread):
    states_loaded = Signal(dict)
    error = Signal(str)
    
    def __init__(self, entity_manager):
        super().__init__()
        self.entity_manager = entity_manager
    
    def run(self):
        try:
            states = self.entity_manager.ws.send_command("get_states")
            # Словарь состояний по entity_id
            state_map = {s.get("entity_id"): s for s in states}
            self.states_loaded.emit(state_map)
        except Exception as e:
            self.error.emit(str(e))

class DeviceDetailDialog(QDialog):
    def __init__(self, device, entity_manager, parent=None):
        super().__init__(parent)
        self.device = device
        self.entity_manager = entity_manager
        
        self.setWindowTitle(f"Устройство: {device['name']}")
        self.setMinimumSize(600, 400)
        
        self.setup_ui()
        self.load_entity_states()
    
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Информация об устройстве
        info_frame = QFrame()
        info_frame.setObjectName("deviceInfoFrame")
        info_layout = QGridLayout(info_frame)
        
        info_layout.addWidget(QLabel("<b>Название:</b>"), 0, 0)
        info_layout.addWidget(QLabel(self.device['name']), 0, 1)
        
        info_layout.addWidget(QLabel("<b>Производитель:</b>"), 1, 0)
        info_layout.addWidget(QLabel(self.device['manufacturer']), 1, 1)
        
        info_layout.addWidget(QLabel("<b>Модель:</b>"), 2, 0)
        info_layout.addWidget(QLabel(self.device['model']), 2, 1)
        
        info_layout.addWidget(QLabel("<b>ID:</b>"), 3, 0)
        info_layout.addWidget(QLabel(self.device['id']), 3, 1)
        
        # Добавляем кнопку "Опросить" для устройств с датчиками
        has_sensors = any(e.get("entity_id", "").startswith("sensor.") for e in self.device['entities'])
        if has_sensors:
            refresh_btn = QPushButton("Опросить")
            refresh_btn.clicked.connect(self.load_entity_states)
            info_layout.addWidget(refresh_btn, 4, 0, 1, 2)
        
        self.main_layout.addWidget(info_frame)
        
        # Список сущностей
        self.main_layout.addWidget(QLabel("<h3>Сущности и их состояния:</h3>"))
        
        entities_scroll = QScrollArea()
        entities_scroll.setWidgetResizable(True)
        entities_scroll.setStyleSheet("background: transparent; border: none;")
        
        entities_widget = QWidget()
        entities_widget.setStyleSheet("background: transparent;")
        self.entities_layout = QVBoxLayout(entities_widget)
        
        # Сохраняем ссылки на виджеты сущностей для обновления
        self.entity_widgets = {}
        
        for entity in self.device['entities']:
            entity_frame = self._create_entity_widget(entity)
            self.entities_layout.addWidget(entity_frame)
            self.entity_widgets[entity.get("entity_id")] = entity_frame
        
        entities_scroll.setWidget(entities_widget)
        self.main_layout.addWidget(entities_scroll)
    
    def _create_entity_widget(self, entity):
        """Создает виджет для отображения сущности"""
        frame = QFrame()
        frame.setObjectName("entityItemFrame")
        frame.setFrameShape(QFrame.StyledPanel)  # Добавляем рамку
        
        layout = QGridLayout(frame)
        
        entity_id = entity.get("entity_id", "unknown")
        entity_name = entity.get("original_name", entity.get("name", "—"))
        entity_type = entity_id.split('.')[0]
        
        # Основная информация
        layout.addWidget(QLabel(f"<b>{entity_name}</b>"), 0, 0, 1, 2)
        layout.addWidget(QLabel(f"ID: {entity_id}"), 1, 0, 1, 2)
        
        # Метка для состояния (будет обновляться)
        state_label = QLabel("Состояние: загрузка...")
        state_label.setObjectName(f"state_{entity_id}")
        layout.addWidget(state_label, 2, 0, 1, 2)
        
        # Добавляем кнопки управления в зависимости от типа сущности
        if entity_type in ["light", "switch", "fan", "cover"]:
            btn_on = QPushButton("Включить")
            btn_off = QPushButton("Выключить")
            
            btn_on.clicked.connect(lambda: self._control_entity(entity_id, "turn_on"))
            btn_off.clicked.connect(lambda: self._control_entity(entity_id, "turn_off"))
            
            layout.addWidget(btn_on, 3, 0)
            layout.addWidget(btn_off, 3, 1)
        
        return frame
    
    def load_entity_states(self):
        """Загружает текущие состояния сущностей"""
        # Показываем индикатор загрузки
        for entity_id, frame in self.entity_widgets.items():
            state_label = frame.findChild(QLabel, f"state_{entity_id}")
            if state_label:
                state_label.setText("Состояние: загрузка...")
        
        # Запускаем загрузку в отдельном потоке
        self.state_loader = EntityStateLoader(self.entity_manager)
        self.state_loader.states_loaded.connect(self._update_entity_states)
        self.state_loader.error.connect(self._on_state_load_error)
        self.state_loader.start()

    def _update_entity_states(self, state_map):
        """Обновляет отображение состояний сущностей"""
        for entity_id, frame in self.entity_widgets.items():
            state_label = frame.findChild(QLabel, f"state_{entity_id}")
            if not state_label:
                continue
            
            if entity_id in state_map:
                state = state_map[entity_id]
                state_value = state.get("state", "unknown")
                attributes = state.get("attributes", {})
                
                # Форматируем строку состояния в зависимости от типа сущности
                formatted_state = self._format_state(entity_id, state_value, attributes)
                state_label.setText(f"Состояние: {formatted_state}")
            else:
                state_label.setText("Состояние: недоступно")

    def _on_state_load_error(self, error):
        """Обработчик ошибки загрузки состояний"""
        QMessageBox.warning(self, "Ошибка", f"Не удалось получить состояния: {error}")
    
    def _format_state(self, entity_id, state, attributes):
        """Форматирует отображение состояния в зависимости от типа сущности"""
        entity_type = entity_id.split('.')[0]
        
        if entity_type == "sensor":
            unit = attributes.get("unit_of_measurement", "")
            return f"{state} {unit}"
        
        elif entity_type in ["binary_sensor", "switch", "light"]:
            if state == "on":
                return "Включено"
            elif state == "off":
                return "Выключено"
            return state
        
        elif entity_type == "cover":
            if state == "open":
                return "Открыто"
            elif state == "closed":
                return "Закрыто"
            return state
        
        return state
    
    def _control_entity(self, entity_id, action):
        """Управляет сущностью"""
        try:
            domain = entity_id.split('.')[0]
            self.entity_manager.ws.send_command("call_service", {
                "domain": domain,
                "service": action,
                "service_data": {"entity_id": entity_id}
            })
            
            # Обновляем состояния с небольшой задержкой
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1000, self.load_entity_states)
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить действие: {str(e)}")
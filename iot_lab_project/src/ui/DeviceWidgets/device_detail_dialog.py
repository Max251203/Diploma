from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QGridLayout, 
                             QPushButton, QFrame, QScrollArea, QMessageBox,
                             QHBoxLayout, QGroupBox, QWidget)
from PySide6.QtCore import Qt

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
        info_frame.setObjectName("deviceInfoFrame")
        info_layout = QGridLayout(info_frame)
        
        info_layout.addWidget(QLabel("<b>Название:</b>"), 0, 0)
        info_layout.addWidget(QLabel(device['name']), 0, 1)
        
        info_layout.addWidget(QLabel("<b>Производитель:</b>"), 1, 0)
        info_layout.addWidget(QLabel(device['manufacturer']), 1, 1)
        
        info_layout.addWidget(QLabel("<b>Модель:</b>"), 2, 0)
        info_layout.addWidget(QLabel(device['model']), 2, 1)
        
        info_layout.addWidget(QLabel("<b>ID:</b>"), 3, 0)
        info_layout.addWidget(QLabel(device['id']), 3, 1)
        
        # Добавляем кнопку "Опросить" для устройств с датчиками
        has_sensors = any(e.get("entity_id", "").startswith("sensor.") for e in device['entities'])
        if has_sensors:
            refresh_btn = QPushButton("Опросить")
            refresh_btn.clicked.connect(self.load_entity_states)
            info_layout.addWidget(refresh_btn, 4, 0, 1, 2)
        
        self.main_layout.addWidget(info_frame)
        
        # Список сущностей
        self.main_layout.addWidget(QLabel("<h3>Сущности:</h3>"))
        
        entities_scroll = QScrollArea()
        entities_scroll.setWidgetResizable(True)
        
        # Устанавливаем прозрачный фон для области прокрутки
        entities_scroll.setStyleSheet("background: transparent; border: none;")
        
        entities_widget = QWidget()
        entities_widget.setStyleSheet("background: transparent;")
        entities_layout = QVBoxLayout(entities_widget)
        
        for entity in device['entities']:
            entity_frame = self._create_entity_widget(entity)
            entities_layout.addWidget(entity_frame)
        
        entities_scroll.setWidget(entities_widget)
        self.main_layout.addWidget(entities_scroll)
    
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
        
        # Кнопки управления устройством
        control_layout = QHBoxLayout()
        
        # Определяем, какие кнопки показывать в зависимости от типа устройства
        has_light = any(e.get("entity_id", "").startswith("light.") for e in self.device['entities'])
        has_switch = any(e.get("entity_id", "").startswith("switch.") for e in self.device['entities'])
        has_cover = any(e.get("entity_id", "").startswith("cover.") for e in self.device['entities'])
        
        if has_light or has_switch:
            btn_on = QPushButton("Включить")
            btn_off = QPushButton("Выключить")
            btn_on.clicked.connect(self.turn_on_device)
            btn_off.clicked.connect(self.turn_off_device)
            control_layout.addWidget(btn_on)
            control_layout.addWidget(btn_off)
        
        if has_cover:
            btn_open = QPushButton("Открыть")
            btn_close = QPushButton("Закрыть")
            btn_open.clicked.connect(self.open_cover)
            btn_close.clicked.connect(self.close_cover)
            control_layout.addWidget(btn_open)
            control_layout.addWidget(btn_close)
        
        # Кнопка обновления состояния
        btn_refresh = QPushButton("Обновить состояние")
        btn_refresh.clicked.connect(self.load_entity_states)
        control_layout.addWidget(btn_refresh)
        
        # Добавляем кнопки в информационный фрейм
        if control_layout.count() > 0:
            info_layout.addLayout(control_layout, 4, 0, 1, 2)
        
        self.main_layout.addWidget(info_frame)
        
        # Список сущностей
        self.main_layout.addWidget(QLabel("<h3>Сущности и их состояния:</h3>"))
        
        entities_scroll = QScrollArea()
        entities_scroll.setWidgetResizable(True)
        entities_widget = QWidget()
        entities_widget.setObjectName("entityListFrame")
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
        
        layout = QGridLayout(frame)
        
        entity_id = entity.get("entity_id", "unknown")
        entity_name = entity.get("original_name", entity.get("name", "—"))
        entity_type = entity_id.split('.')[0]
        
        layout.addWidget(QLabel(f"<b>{entity_name}</b>"), 0, 0, 1, 2)
        layout.addWidget(QLabel(f"ID: {entity_id}"), 1, 0)
        layout.addWidget(QLabel(f"Тип: {entity_type}"), 1, 1)
        
        # Добавляем кнопки управления только для управляемых устройств
        if entity_type in ["light", "switch", "fan", "cover"]:
            btn_on = QPushButton("Включить")
            btn_off = QPushButton("Выключить")
            
            btn_on.clicked.connect(lambda: self._control_entity(entity_id, "turn_on"))
            btn_off.clicked.connect(lambda: self._control_entity(entity_id, "turn_off"))
            
            layout.addWidget(btn_on, 2, 0)
            layout.addWidget(btn_off, 2, 1)
        
        return frame
    
    def load_entity_states(self):
        """Загружает и отображает текущие состояния сущностей"""
        try:
            states = self.entity_manager.ws.send_command("get_states")
            
            # Создаем словарь состояний по entity_id
            state_map = {s.get("entity_id"): s for s in states}
            
            # Обходим все фреймы сущностей и обновляем информацию
            for entity in self.device['entities']:
                entity_id = entity.get("entity_id", "")
                if entity_id in state_map:
                    state = state_map[entity_id]
                    state_value = state.get("state", "unknown")
                    attributes = state.get("attributes", {})
                    
                    # Здесь можно добавить обновление информации в UI
                    # Например, добавлять или обновлять метку с текущим состоянием
                    
            QMessageBox.information(self, "Обновлено", "Состояния устройств обновлены")
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось получить состояния: {str(e)}")
    
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
    
    def turn_on_device(self):
        """Включает все управляемые сущности устройства"""
        self._control_device_entities(["light", "switch"], "turn_on")
    
    def turn_off_device(self):
        """Выключает все управляемые сущности устройства"""
        self._control_device_entities(["light", "switch"], "turn_off")
    
    def open_cover(self):
        """Открывает все жалюзи/шторы устройства"""
        self._control_device_entities(["cover"], "open_cover")
    
    def close_cover(self):
        """Закрывает все жалюзи/шторы устройства"""
        self._control_device_entities(["cover"], "close_cover")
    
    def _control_device_entities(self, domains, service):
        """Управляет всеми сущностями устройства заданного типа"""
        try:
            success = False
            
            for entity in self.device['entities']:
                entity_id = entity.get("entity_id", "")
                domain = entity_id.split('.')[0]
                
                if domain in domains:
                    self.entity_manager.ws.send_command("call_service", {
                        "domain": domain,
                        "service": service,
                        "service_data": {"entity_id": entity_id}
                    })
                    success = True
            
            if success:
                QMessageBox.information(
                    self, 
                    "Успех", 
                    f"Команда отправлена на устройство: {self.device['name']}"
                )
                # Обновляем состояния с небольшой задержкой
                from PySide6.QtCore import QTimer
                QTimer.singleShot(1000, self.load_entity_states)
            else:
                QMessageBox.warning(
                    self, 
                    "Предупреждение", 
                    f"Нет подходящих сущностей для выполнения действия"
                )
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить действие: {str(e)}")
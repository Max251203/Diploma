from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QGridLayout, 
                             QPushButton, QFrame, QScrollArea, QMessageBox, QWidget)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from ui.widgets.entity_widget import EntityWidget

class StateLoaderThread(QThread):
    """Поток для загрузки состояний сущностей"""
    states_loaded = Signal(dict)
    error = Signal(str)
    
    def __init__(self, entity_manager):
        super().__init__()
        self.entity_manager = entity_manager
    
    def run(self):
        try:
            # Получаем все состояния
            states = self.entity_manager.ws.send_command("get_states")
            # Преобразуем в словарь для быстрого доступа
            state_map = {s.get("entity_id"): s for s in states}
            self.states_loaded.emit(state_map)
        except Exception as e:
            self.error.emit(str(e))

class DeviceDialog(QDialog):
    """Диалог для отображения и управления устройством"""
    
    def __init__(self, device, entity_manager, parent=None):
        super().__init__(parent)
        self.device = device
        self.entity_manager = entity_manager
        self.entity_widgets = {}
        
        self.setWindowTitle(f"Устройство: {device['name']}")
        self.setMinimumSize(600, 400)
        
        self.setup_ui()
        self.load_states()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация об устройстве
        info_frame = QFrame()
        info_frame.setObjectName("deviceInfoFrame")
        info_layout = QGridLayout(info_frame)
        
        # Основная информация
        info_layout.addWidget(QLabel("<b>Название:</b>"), 0, 0)
        info_layout.addWidget(QLabel(self.device['name']), 0, 1)
        
        info_layout.addWidget(QLabel("<b>Производитель:</b>"), 1, 0)
        info_layout.addWidget(QLabel(self.device['manufacturer']), 1, 1)
        
        info_layout.addWidget(QLabel("<b>Модель:</b>"), 2, 0)
        info_layout.addWidget(QLabel(self.device['model']), 2, 1)
        
        info_layout.addWidget(QLabel("<b>ID:</b>"), 3, 0)
        info_layout.addWidget(QLabel(self.device['id']), 3, 1)
        
        # Кнопка опроса для устройств с датчиками
        has_sensors = any(e.get("entity_id", "").startswith("sensor.") for e in self.device['entities'])
        if has_sensors:
            refresh_btn = QPushButton("Опросить")
            refresh_btn.clicked.connect(self.load_states)
            info_layout.addWidget(refresh_btn, 4, 0, 1, 2)
        
        layout.addWidget(info_frame)
        
        # Список сущностей
        entities_title = QLabel("<h3>Сущности и их состояния:</h3>")
        entities_title.setStyleSheet("color: #c6e2ff; margin-top: 10px;")
        layout.addWidget(entities_title)
        
        # Создаем контейнер для сущностей с рамкой
        entities_container = QFrame()
        entities_container.setObjectName("entitiesContainer")
        entities_container.setFrameShape(QFrame.StyledPanel)
        entities_container.setFrameShadow(QFrame.Raised)
        entities_layout = QVBoxLayout(entities_container)
        
        # Создаем область прокрутки с прозрачным фоном
        entities_scroll = QScrollArea()
        entities_scroll.setWidgetResizable(True)
        entities_scroll.setStyleSheet("background: transparent; border: none;")
        
        # Контейнер для сущностей
        entities_widget = QWidget()
        entities_widget.setStyleSheet("background: transparent;")
        entities_content_layout = QVBoxLayout(entities_widget)
        
        # Создаем виджеты для каждой сущности
        for entity in self.device['entities']:
            entity_widget = EntityWidget(entity)
            entity_widget.control_requested.connect(self._handle_control_request)
            entities_content_layout.addWidget(entity_widget)
            
            # Сохраняем ссылку на виджет
            entity_id = entity.get("entity_id")
            if entity_id:
                self.entity_widgets[entity_id] = entity_widget
        
        # Добавляем растягивающийся элемент в конец
        entities_content_layout.addStretch()
        
        # Устанавливаем виджет в область прокрутки
        entities_scroll.setWidget(entities_widget)
        
        # Добавляем область прокрутки в контейнер
        entities_layout.addWidget(entities_scroll)
        
        # Добавляем контейнер в основной layout
        layout.addWidget(entities_container)
    
    def load_states(self):
        """Загружает состояния сущностей в отдельном потоке"""
        # Запускаем загрузку
        self.state_loader = StateLoaderThread(self.entity_manager)
        self.state_loader.states_loaded.connect(self._update_states)
        self.state_loader.error.connect(self._handle_state_error)
        self.state_loader.start()
    
    def _update_states(self, state_map):
        """Обновляет состояния в виджетах сущностей"""
        for entity_id, widget in self.entity_widgets.items():
            state_data = state_map.get(entity_id)
            widget.update_state(state_data)
    
    def _handle_state_error(self, error):
        """Обрабатывает ошибку загрузки состояний"""
        QMessageBox.warning(self, "Ошибка", f"Не удалось получить состояния: {error}")
    
    def _handle_control_request(self, entity_id, action):
        """Обрабатывает запрос на управление сущностью"""
        try:
            domain = entity_id.split('.')[0]
            self.entity_manager.ws.send_command("call_service", {
                "domain": domain,
                "service": action,
                "service_data": {"entity_id": entity_id}
            })
            
            # Обновляем состояния через 1 секунду
            QTimer.singleShot(1000, self.load_states)
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить действие: {str(e)}")
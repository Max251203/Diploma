from PySide6.QtCore import QThread, Signal

class StateLoaderThread(QThread):
    """Поток для загрузки состояний сущностей"""
    states_loaded = Signal(dict)
    error = Signal(str)
    
    def __init__(self, entity_manager, entity_ids=None):
        super().__init__()
        self.entity_manager = entity_manager
        self.entity_ids = entity_ids  # Список ID сущностей для обновления
    
    def run(self):
        try:
            # Если есть список сущностей для обновления, сначала запрашиваем их обновление
            if self.entity_ids:
                for entity_id in self.entity_ids:
                    domain = entity_id.split('.')[0]
                    # Для датчиков используем REST API (более надежно)
                    if domain in ["sensor", "binary_sensor"]:
                        self.entity_manager.update_sensor(entity_id)
            
            # Даем время на обновление (небольшая задержка)
            self.msleep(500)
            
            # Оптимизация: если нужно только одно состояние, используем точечный запрос
            if self.entity_ids and len(self.entity_ids) == 1:
                entity_id = self.entity_ids[0]
                state = self.entity_manager.get_entity_state(entity_id)
                if state:
                    self.states_loaded.emit({entity_id: state})
                    return
            
            # Для нескольких состояний используем bulk запрос через WebSocket
            states = self.entity_manager.get_states()
            
            # Преобразуем в словарь для быстрого доступа
            state_map = {s.get("entity_id"): s for s in states}
            
            # Если нужны только конкретные сущности, фильтруем результат
            if self.entity_ids:
                filtered_map = {id: state_map.get(id) for id in self.entity_ids}
                self.states_loaded.emit(filtered_map)
            else:
                self.states_loaded.emit(state_map)
                
        except Exception as e:
            self.error.emit(str(e))
from PySide6.QtCore import QThread, Signal

class StateLoader(QThread):
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
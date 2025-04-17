from PySide6.QtCore import QThread, Signal
from core.ha.entity_manager import EntityManager
from typing import List, Dict, Optional

class StateLoaderThread(QThread):
    """Поток для загрузки состояний сущностей"""

    states_loaded = Signal(dict)
    error = Signal(str)

    def __init__(self, entity_manager: EntityManager, entity_ids: Optional[List[str]] = None):
        super().__init__()
        self.entity_manager = entity_manager
        self.entity_ids = entity_ids  # Список ID сущностей для обновления

    def run(self):
        try:
            # Обновляем сенсоры через REST (если есть)
            if self.entity_ids:
                for entity_id in self.entity_ids:
                    domain = entity_id.split('.')[0]
                    if domain in ["sensor", "binary_sensor"]:
                        self.entity_manager.update_sensor(entity_id)

            # Даем REST немного времени на обновление (не обязательно, но можно)
            self.msleep(500)

            if self.entity_ids and len(self.entity_ids) == 1:
                entity_id = self.entity_ids[0]

                def on_state_loaded(state):
                    if state:
                        self.states_loaded.emit({entity_id: state})
                    else:
                        self.states_loaded.emit({})

                self.entity_manager.get_entity_state(entity_id, callback=on_state_loaded)
                return

            # Получаем все состояния
            def on_states_loaded(states: List[Dict]):
                state_map = {s.get("entity_id"): s for s in states}
                if self.entity_ids:
                    filtered = {eid: state_map.get(eid) for eid in self.entity_ids}
                    self.states_loaded.emit(filtered)
                else:
                    self.states_loaded.emit(state_map)

            self.entity_manager.get_states(callback=on_states_loaded)

        except Exception as e:
            self.error.emit(str(e))
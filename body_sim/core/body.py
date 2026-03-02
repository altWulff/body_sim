# core/body.py

from typing import Dict, Optional
import uuid

from body_sim.core.components import ComponentInterface
from body_sim.core.events import EventBus, Event, EventType
from body_sim.systems.stats import StatisticsService


class Body:
    """Aggregate root всего организма"""
    def __init__(self, name: str, gender: str = "female"):
        self.name = name
        self.gender = gender
        self.id = uuid.uuid4().hex
        
        # Системы
        self.event_bus = EventBus()
        self.stats = StatisticsService()
        self.components: Dict[str, ComponentInterface] = {}
        
        # Основные системы (инициализируются отдельно)
        self.reproductive: Optional[ReproductiveSystem] = None
        self.digestive: Optional[DigestiveSystem] = None
        self.appearance: Optional[AppearanceComponent] = None
        
    def add_system(self, name: str, system: ComponentInterface):
        self.components[name] = system
        system._parent_body = self
        self.event_bus.emit(Event(
            type=EventType.COMPONENT_ADDED,
            source=system.component_id
        ))
        
    def get_component(self, name: str) -> Optional[ComponentInterface]:
        return self.components.get(name)
        
    def update(self, delta_time: float = 1.0):
        """Главный игровой тик"""
        for component in self.components.values():
            component.update(delta_time, self.event_bus)
            
        self.event_bus.emit(Event(
            type=EventType.TICK,
            source=self.id,
            data={'delta_time': delta_time}
        ))
        
    def get_full_state(self) -> Dict:
        return {
            'name': self.name,
            'gender': self.gender,
            'components': {
                name: comp.get_state() 
                for name, comp in self.components.items()
            }
        }

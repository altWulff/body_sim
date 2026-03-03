# === anatomy/digestive/anus.py ===
from typing import Dict, Any, TYPE_CHECKING

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus

if TYPE_CHECKING:
    from body_sim.anatomy.digestive.stomach import Stomach

class Anus(AnatomicalComponent):
    def __init__(self):
        super().__init__("anus", max_volume=100)
        self.sphincter_tone = 1.0  # 0-1
        self.diameter = 0.0  # cm текущее растяжение
        self.max_diameter = 8.0
        self.connected_to_stomach = False  # Для экстремальных сценариев
        
    def penetrate(self, size: float, depth: float):
        self.diameter = max(self.diameter, size)
            
    def connect_to_stomach(self, stomach: 'Stomach'):
        """Устанавливает прямое соединение (альтернативная анатомия)."""
        self.connected_to_stomach = True
        self.connect_to(stomach)
        
    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        # Восстановление тонуса со временем
        if self.diameter > 0:
            self.diameter = max(0.0, self.diameter - 0.1 * delta_time)
            
    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update({
            'sphincter_tone': self.sphincter_tone,
            'diameter': self.diameter,
            'max_diameter': self.max_diameter,
            'connected_to_stomach': self.connected_to_stomach
        })
        return basestring
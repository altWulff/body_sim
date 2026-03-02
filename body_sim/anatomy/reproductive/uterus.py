# anatomy/reproductive/uterus.py

from typing import Dict, List

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus


class Uterus(AnatomicalComponent):
    def __init__(self):
        super().__init__("uterus", max_volume=5000)  # 5L max для экстремальных сценариев
        self.wall_thickness = 1.0  # cm
        self.cervix_dilation = 0.0  # cm
        self.cervix_effacement = 0.0  # %
        self.fundus_height = 7.0  # cm
        self.prolapse_stage = 0  # 0-4
        self.is_inverted = False
        self.implantation_sites: List[Dict] = []
        
    def contract(self, intensity: float, event_bus: EventBus = None):
        """Мышечные сокращения матки"""
        if event_bus:
            event_bus.emit(Event(
                type=EventType.MUSCLE_CONTRACTION,
                source=self.component_id,
                data={'intensity': intensity, 'contents': len(self.fluids)}
            ))
            
    def invert(self):
        """Инверсия матки (экстремальный медицинский случай)"""
        self.is_inverted = True
        self.prolapse_stage = 4
        
    def can_accept_insertion(self, size: float) -> bool:
        """Проверка возможности проникновения через шейку"""
        return self.cervix_dilation >= size or self.is_inverted

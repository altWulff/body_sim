# anatomy/reproductive/system.py

from typing import List

from body_sim.core.components import BaseComponent
from body_sim.core.events import EventBus
from body_sim.anatomy.base import AnatomicalComponent

from .vagina import Vagina
from .uterus import Uterus
from .ovaries import Ovaries
from .tubes import FallopianTube

class ReproductiveSystem(BaseComponent):
    """Aggregate root для репродуктивной системы"""
    def __init__(self):
        super().__init__("reproductive_system")
        self.vagina = Vagina()
        self.uterus = Uterus()
        self.left_ovary = Ovaries("left")
        self.right_ovary = Ovaries("right")
        self.left_tube = FallopianTube("left")
        self.right_tube = FallopianTube("right")
        self.breasts: Optional[Breasts] = None  # Устанавливается извне
        
        # Установка связей
        self.vagina.connect_to(self.uterus)
        self.left_tube.connect_to(self.uterus)
        self.right_tube.connect_to(self.uterus)
        self.left_tube.connect_to(self.left_ovary)
        self.right_tube.connect_to(self.right_ovary)
        
    def update(self, delta_time: float, event_bus: EventBus):
        for component in [self.vagina, self.uterus, self.left_ovary, 
                         self.right_ovary, self.left_tube, self.right_tube]:
            component.update(delta_time, event_bus)
        if self.breasts:
            self.breasts.update(delta_time, event_bus)
            
    def get_components(self) -> List[AnatomicalComponent]:
        comps = [self.vagina, self.uterus, self.left_ovary, 
                self.right_ovary, self.left_tube, self.right_tube]
        if self.breasts:
            comps.append(self.breasts)
        return comps

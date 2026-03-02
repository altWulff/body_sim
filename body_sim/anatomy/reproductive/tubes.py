# anatomy/reproductive/tubes.py

from typing import Optional, Dict, Any
from dataclasses import dataclass


from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.fluids import FluidType
from body_sim.core.events import EventBus
# from body_sim.anatomy.reproductive.ovaries import Gamete


@dataclass
class FallopianTube(AnatomicalComponent):
    side: str = "left"
    base_length: float = 10.0
    base_diameter: float = 0.3
    current_stretch: float = 1.0
    inflation_ratio: float = 1.0
    contained_fluid: float = 0.0
    max_fluid_capacity: float = 15.0
    cilia_activity: float = 1.0
    
    def __post_init__(self):
        super().__init__(f"tube_{self.side}", max_volume=self.max_fluid_capacity)
        
    @property
    def current_length(self) -> float:
        return self.base_length * self.current_stretch
        
    def stretch(self, ratio: float) -> bool:
        if ratio > 4.0:
            return False
        self.current_stretch = ratio
        return True
        
    def inflate(self, ratio: float) -> bool:
        self.inflation_ratio = ratio
        self.max_fluid_capacity = 15.0 * (ratio ** 2)
        return True
        
    def transfer_to_ovary(self, amount: float, fluid_type: FluidType = None) -> float:
        actual = min(amount, self.contained_fluid)
        self.contained_fluid -= actual
        return actual
        
    def receive_backflow(self, amount: float, fluid_type: FluidType = None) -> float:
        space = self.max_fluid_capacity - self.contained_fluid
        actual = min(amount, space)
        self.contained_fluid += actual
        return actual
        
    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        if self.contained_fluid > 0 and self.cilia_activity > 0:
            self.contained_fluid = max(0, self.contained_fluid - 0.01 * delta_time)
            
    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update({
            'side': self.side,
            'length': self.current_length,
            'diameter': self.base_diameter * self.inflation_ratio,
            'fluid': self.contained_fluid,
            'stretch': self.current_stretch
        })
        return base

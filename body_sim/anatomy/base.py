# === anatomy/base.py ===
from typing import Dict, Any

from body_sim.core.components import BaseComponent, ComponentInterface
from body_sim.core.fluids import FluidContainer
from body_sim.core.events import EventBus, Event, EventType

class AnatomicalComponent(BaseComponent, FluidContainer):
    def __init__(self, name: str, max_volume: float = 0):
        BaseComponent.__init__(self, name)
        FluidContainer.__init__(self, max_volume)
        self.sensitivity = 1.0
        self.current_stimulation = 0.0
        self.pain_level = 0.0
        self.arousal = 0.0
        
    def stimulate(self, amount: float, source: str = None):
        self.current_stimulation = min(100.0, self.current_stimulation + amount * self.sensitivity)
        self.arousal = min(1.0, self.arousal + amount * 0.01)
        
    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        self.current_stimulation *= (0.95 ** delta_time)
        self.pain_level *= (0.90 ** delta_time)
        if self.arousal > 0:
            self.arousal = max(0.0, self.arousal - 0.02 * delta_time)
            
    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update({
            'sensitivity': self.sensitivity,
            'stimulation': self.current_stimulation,
            'pain': self.pain_level,
            'arousal': self.arousal,
            'fullness': self.get_fullness(),
            'fluids': [{'type': f.fluid_type.value, 'volume': f.volume} for f in self.fluids]
        })
        return base
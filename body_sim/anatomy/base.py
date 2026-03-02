# anatomy/base.py

from body_sim.core.components import BaseComponent
from body_sim.core.fluids import FluidContainer
from body_sim.core.events import EventBus


class AnatomicalComponent(BaseComponent, FluidContainer):
    """Базовый класс для анатомических органов"""
    def __init__(self, name: str, max_volume: float = 0):
        BaseComponent.__init__(self, name)
        FluidContainer.__init__(self, max_volume)
        self.sensitivity = 1.0
        self.current_stimulation = 0.0
        self.pain_level = 0.0
        
    def stimulate(self, amount: float, source: str = None):
        self.current_stimulation += amount * self.sensitivity
        if self.current_stimulation > 100:
            self.current_stimulation = 100
            
    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        # Decay stimulation
        self.current_stimulation *= (0.95 ** delta_time)
        self.pain_level *= (0.90 ** delta_time)

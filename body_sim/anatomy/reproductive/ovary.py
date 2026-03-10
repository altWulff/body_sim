# anatomy/reproductive/ovary.py

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.fluids import Fluid
from body_sim.core.events import EventBus

# @dataclass
# class Gamete:
#     id: str
#     is_sperm: bool
#     dna: str
#     maturity: float = 0.0
#     fertility: float = 1.0


@dataclass
class Ovary(AnatomicalComponent):
    side: str = "left"
    follicle_count: int = 5
    hormone_production: float = 1.0
    prolapse_degree: float = 0.0
    is_everted: bool = False

    def __post_init__(self):
        super().__init__(f"ovary_{self.side}", max_volume=20)

    def evert(self, degree: float = 1.0):
        self.prolapse_degree = min(1.0, self.prolapse_degree + degree)
        if self.prolapse_degree > 0.7:
            self.is_everted = True

    def reposition(self, amount: float = 0.5):
        self.prolapse_degree = max(0.0, self.prolapse_degree - amount)
        if self.prolapse_degree < 0.3:
            self.is_everted = False

    def add_fluid(self, fluid: Fluid) -> float:
        """Добавить жидкость в яичник."""
        available = self.max_capacity - sum(f.volume for f in self.fluids)
        actual = min(fluid.volume, available)
        if actual > 0:
            fluid.volume = actual
            super().add_fluid(fluid)  # вызываем AnatomicalComponent.add_fluid
        return fluid.volume - actual

    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        if self.is_everted:
            self.hormone_production = max(
                0.0, self.hormone_production - 0.01 * delta_time
            )

    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update(
            {
                "side": self.side,
                "follicles": self.follicle_count,
                "hormone": self.hormone_production,
                "everted": self.is_everted,
            }
        )
        return base

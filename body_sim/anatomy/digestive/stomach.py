# === anatomy/digestive/stomach.py ===
from typing import Dict, Any

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.fluids import FluidType
from body_sim.core.events import EventBus


class Stomach(AnatomicalComponent):
    def __init__(self):
        super().__init__("stomach", max_volume=1500)
        self.ph_level = 1.5
        self.emptying_rate = 2.0  # ml/min
        self.peristalsis_active = False

    def digest(self, delta_time: float):
        """Пищеварение жидкостей."""
        for fluid in self.fluids:
            if fluid.fluid_type != FluidType.GASTRIC_JUICE:
                # Переваривание
                fluid.volume -= self.emptying_rate * delta_time / 60

        self.fluids = [f for f in self.fluids if f.volume > 0]

    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        self.digest(delta_time)

    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update(
            {
                "ph": self.ph_level,
                "emptying_rate": self.emptying_rate,
                "digesting": self.peristalsis_active,
                "fullness": self.get_fullness(),
            }
        )
        return basestring

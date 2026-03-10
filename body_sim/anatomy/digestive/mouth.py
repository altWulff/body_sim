# === anatomy/digestive/mouth.py ===
from typing import Dict, Any

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus


class Mouth(AnatomicalComponent):
    def __init__(self):
        super().__init__("mouth", max_volume=100)
        self.jaw_opening = 0.0  # cm
        self.max_opening = 6.0
        self.saliva_production = 1.0

    def open(self, amount: float):
        self.jaw_opening = min(amount, self.max_opening)

    def can_accept(self, size: float) -> bool:
        return self.jaw_opening >= size

    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        # Челюсть закрывается со временем
        if self.jaw_opening > 0:
            self.jaw_opening = max(0.0, self.jaw_opening - 0.2 * delta_time)

    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update(
            {
                "jaw_opening": self.jaw_opening,
                "max_opening": self.max_opening,
                "can_accept": self.can_accept(self.max_opening),
            }
        )
        return base

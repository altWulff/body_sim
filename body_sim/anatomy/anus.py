"""
Анус - задний проход.
"""
from dataclasses import dataclass
from typing import Optional, Any

from body_sim.anatomy.base import Genital
from body_sim.core.enums import AnusType


@dataclass
class Anus(Genital):
    anus_type: AnusType = AnusType.AVERAGE
    base_diameter: float = 2.5
    max_diameter: float = 6.0
    sphincter_tone: float = 0.7
    is_gaping: bool = False
    gaping_size: float = 0.0
    inserted_object: Optional[Any] = None

    @property
    def current_diameter(self) -> float:
        if self.is_gaping: return self.gaping_size
        return self.base_diameter * (1 - self.sphincter_tone * 0.5)

    @property
    def can_hold(self) -> bool:
        return self.sphincter_tone > 0.3 and not self.is_gaping

    def relax(self, amount: float = 0.1) -> None:
        self.sphincter_tone = max(0.0, self.sphincter_tone - amount)

    def contract(self, amount: float = 0.1) -> None:
        self.sphincter_tone = min(1.0, self.sphincter_tone + amount)

    def stretch(self, diameter: float) -> bool:
        if diameter > self.max_diameter: return False
        self.is_gaping = True
        self.gaping_size = diameter
        return True

    def close(self) -> None:
        self.is_gaping = False
        self.gaping_size = 0.0

    def tick(self, dt: float) -> None:
        super().tick(dt)
        if not self.inserted_object and not self.is_gaping:
            self.sphincter_tone = min(0.7, self.sphincter_tone + 0.02 * dt)
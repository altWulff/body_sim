# === anatomy/reproductive/penis.py ===
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import math

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.fluids import Fluid, FluidType
from body_sim.core.events import EventBus


@dataclass
class Penis(AnatomicalComponent):
    base_length: float = 15.0
    base_girth: float = 12.0
    is_erect: bool = False
    erection_length_multiplier: float = 1.3
    erection_girth_multiplier: float = 1.2
    sensitivity: float = 1.0
    is_transformed_clitoris: bool = False
    original_clitoris_size: float = 0.0

    ejaculation_force: float = 1.0
    scrotum: Optional["Scrotum"] = field(default=None, repr=False)
    current_pulses: int = 0

    def __post_init__(self):
        super().__init__(self.name if hasattr(self, "name") else "penis", max_volume=50)
        self.name = "penis"

    @property
    def current_length(self) -> float:
        mult = self.erection_length_multiplier if self.is_erect else 1.0
        return self.base_length * mult

    @property
    def current_girth(self) -> float:
        mult = self.erection_girth_multiplier if self.is_erect else 1.0
        return self.base_girth * mult

    @property
    def current_diameter(self) -> float:
        return self.current_girth / math.pi

    def can_penetrated(self, opening_diameter: float) -> bool:
        return opening_diameter >= self.current_diameter * 0.8

    def stimulate(self, intensity: float = 0.1, source: str = None):
        super().stimulate(intensity, source)
        if self.arousal > 0.6 and not self.is_erect:
            self.erect()

    def erect(self):
        self.is_erect = True

    def flaccid(self):
        self.is_erect = False

    def has_scrotum(self) -> bool:
        return self.scrotum is not None

    def ejaculate(self, force: float = 1.0) -> Dict[str, Any]:
        if not self.is_erect:
            return {"amount": 0, "reason": "not_erect", "pulses": 0}

        if not self.scrotum:
            return {"amount": 0, "reason": "no_scrotum", "pulses": 0}

        available = self.scrotum.drain_fluid(1000)
        total_volume = sum(f.volume for f in available)

        if total_volume <= 0:
            return {"amount": 0, "reason": "empty", "pulses": 0}

        pulses = min(5, max(1, int(force * 3)))
        per_pulse = total_volume / pulses

        return {
            "amount": total_volume,
            "pulses": pulses,
            "per_pulse": per_pulse,
            "remaining_in_testicles": self.scrotum.total_stored if self.scrotum else 0,
        }

    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)

    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update(
            {
                "length": self.current_length,
                "girth": self.current_girth,
                "is_erect": self.is_erect,
                "is_transformed_clitoris": self.is_transformed_clitoris,
                "has_scrotum": self.has_scrotum(),
            }
        )
        return base

# === systems/inflation.py ===
"""
Система инфляции/растяжения тканей
"""

from typing import Optional, Dict
from dataclasses import dataclass, field
from enum import Enum, auto

from body_sim.core.events import EventBus, EventType


class StretchState(Enum):
    NORMAL = auto()
    ELASTIC = auto()
    PLASTIC = auto()
    PERMANENT = auto()
    DAMAGED = auto()


@dataclass
class InflationProfile:
    """Профиль инфляции."""

    stretch_ratio: float = 1.0
    max_stretch: float = 3.0
    plasticity: float = 0.3
    recovery_rate: float = 0.001
    peak_stretch: float = 1.0
    is_permanently_stretched: bool = False
    stretch_marks: float = 0.0
    base_elasticity: float = 1.0
    current_elasticity: float = 1.0  # <-- ДОБАВИТЬ ЭТО


class InflationSystem:
    """Управление растяжением тканей."""

    def __init__(self, profile: Optional[InflationProfile] = None):
        self.profile = profile or InflationProfile()
        self._listeners = []

    def calculate_target_stretch(
        self, current_volume: float, base_volume: float
    ) -> float:
        """Целевое растяжение на основе объема."""
        normal_volume = base_volume * 1.5

        if current_volume <= normal_volume:
            return self._calculate_recovery()

        excess = (current_volume - normal_volume) / normal_volume
        new_stretch = 1.0 + excess
        self.profile.peak_stretch = max(self.profile.peak_stretch, new_stretch)

        if new_stretch >= self.profile.max_stretch:
            self.profile.is_permanently_stretched = True
            return self.profile.max_stretch

        return new_stretch

    def _calculate_recovery(self) -> float:
        """Восстановление при уменьшении объема."""
        if self.profile.stretch_ratio <= 1.0:
            return 1.0

        plastic_part = (
            1.0 + (self.profile.stretch_ratio - 1.0) * self.profile.plasticity
        )
        elastic_part = (self.profile.stretch_ratio - 1.0) * (
            1.0 - self.profile.plasticity
        )
        recovered_elastic = elastic_part * (1.0 - self.profile.recovery_rate)

        target = plastic_part + recovered_elastic
        return max(1.0, target)

    def apply_stretch(self, target: float, dt: float = 1.0) -> Dict:
        """Применить растяжение."""
        old = self.profile.stretch_ratio
        speed = 0.1 if target > old else 0.05

        self.profile.stretch_ratio = max(
            1.0, min(old + (target - old) * speed * dt, self.profile.max_stretch)
        )

        self._update_elasticity()
        self._update_stretch_marks()

        return {
            "old": old,
            "new": self.profile.stretch_ratio,
            "delta": self.profile.stretch_ratio - old,
            "state": self.get_state().name,
        }

    def _update_elasticity(self):
        """Обновить эластичность."""
        if self.profile.stretch_ratio > 1.0:
            penalty = (self.profile.stretch_ratio - 1.0) * 0.5
            self.profile.current_elasticity = max(
                0.1, self.profile.base_elasticity - penalty
            )
        else:
            self.profile.current_elasticity = self.profile.base_elasticity

    def _update_stretch_marks(self):
        """Обновить растяжки."""
        tension = self.get_skin_tension()
        if tension > 0.6:
            risk = (tension - 0.6) ** 2 * 0.01
            self.profile.stretch_marks = min(1.0, self.profile.stretch_marks + risk)

    def get_skin_tension(self) -> float:
        """Натяжение кожи 0-1."""
        if self.profile.stretch_ratio <= 1.0:
            return 0.0
        ratio = (self.profile.stretch_ratio - 1.0) / (self.profile.max_stretch - 1.0)
        return min(1.0, ratio**2)

    def get_state(self) -> StretchState:
        """Текущее состояние."""
        s = self.profile.stretch_ratio
        if s < 1.1:
            return StretchState.NORMAL
        elif s < 1.5:
            return (
                StretchState.ELASTIC
                if not self.profile.is_permanently_stretched
                else StretchState.PLASTIC
            )
        elif s < self.profile.max_stretch * 0.9:
            return (
                StretchState.PLASTIC
                if self.profile.is_permanently_stretched
                else StretchState.ELASTIC
            )
        else:
            return (
                StretchState.DAMAGED
                if self.profile.stretch_marks > 0.5
                else StretchState.PERMANENT
            )

    def get_max_volume(self, base_volume: float) -> float:
        """Максимальный объем с учетом растяжения."""
        return base_volume * 1.5 * self.profile.stretch_ratio

    def tick(self, delta_time: float, event_bus: EventBus, component_id: str):
        """Обновление."""
        # Проверка на растяжки
        if self.profile.stretch_marks > 0.5:
            event_bus.emit(
                Event(
                    type=EventType.STRETCH_MARKS,
                    source=component_id,
                    data={"severity": self.profile.stretch_marks},
                )
            )

        return {
            "stretch_ratio": self.profile.stretch_ratio,
            "tension": self.get_skin_tension(),
            "state": self.get_state().name,
        }

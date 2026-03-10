# body_sim/systems/pressure.py
"""
Система управления давлением
"""

from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class PressureTier(Enum):
    """Уровни давления."""

    NO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PressureController:
    """Контроллер давления."""

    current_pressure: float = 0.0
    _last_tier: Optional[PressureTier] = field(default=None, init=False)
    _thresholds: list = field(default_factory=lambda: [0.5, 1.0, 1.8, 2.5])

    def update(self, pressure: float) -> Optional[PressureTier]:
        """Обновить состояние и вернуть новый tier если изменился."""
        self.current_pressure = max(0.0, pressure)
        current_tier = self.get_tier()

        if current_tier != self._last_tier:
            old_tier = self._last_tier
            self._last_tier = current_tier
            return current_tier

        return None

    def get_tier(self) -> PressureTier:
        """Определить уровень давления."""
        p = self.current_pressure
        if p >= 2.5:
            return PressureTier.CRITICAL
        elif p >= 1.8:
            return PressureTier.HIGH
        elif p >= 1.0:
            return PressureTier.MEDIUM
        elif p >= 0.5:
            return PressureTier.LOW
        return PressureTier.NO

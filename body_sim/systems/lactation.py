# body_sim/systems/lactation.py
"""
Система лактации.
"""

from dataclasses import dataclass, field
from typing import Dict, TYPE_CHECKING

from body_sim.core.enums import LactationState, FluidType

if TYPE_CHECKING:
    from body_sim.anatomy.breast import Breast
    from body_sim.core.fluids import BreastFluid


@dataclass
class LactationSystem:
    state: LactationState = field(default=LactationState.OFF)
    base_rate_per_100ml: float = 2.0
    min_rate: float = 3.0
    max_rate: float = 50.0
    stimulation_bonus: float = 2.0
    hormone_level: float = 1.0
    letdown_reflex: float = 1.0
    consecutive_stimulation: int = 0
    max_streak_bonus: float = 2.0
    _stimulated: bool = field(default=False, repr=False)

    def __post_init__(self):
        if not isinstance(self.state, LactationState):
            self.state = LactationState.OFF

    def start(self) -> None:
        """Запустить лактацию."""
        if self.state == LactationState.OFF:
            self.state = LactationState.PREPARE
            self.consecutive_stimulation = 0

    def stop(self) -> None:
        """Остановить лактацию."""
        if self.state != LactationState.OFF:
            self.state = LactationState.DRYING
            self.consecutive_stimulation = 0

    def stimulate(self) -> None:
        """Стимулировать лактацию."""
        self._stimulated = True
        self.consecutive_stimulation += 1

    def calculate_base_rate(self, breast: 'Breast') -> float:
        volume_100ml = breast._base_volume / 100.0
        rate = self.base_rate_per_100ml * volume_100ml
        return max(min(rate, self.max_rate), self.min_rate)

    def calculate_fill_penalty(self, fill_ratio: float) -> float:
        if fill_ratio <= 0.5:
            return 1.0
        if fill_ratio <= 0.85:
            return 1.0 - (fill_ratio - 0.5) * (0.5 / 0.35)
        return max(0.2, 0.5 - (fill_ratio - 0.85) * 2.0)

    def tick(self, breast: 'Breast', defs: Dict[FluidType, 'BreastFluid'], dt: float = 1.0) -> float:
        if self.state == LactationState.OFF:
            return 0.0

        fill_ratio = breast.filled / breast._max_volume
        fill_penalty = self.calculate_fill_penalty(fill_ratio)
        volume_rate = self.calculate_base_rate(breast)
        current_base_rate = volume_rate * fill_penalty

        produced = 0.0
        streak = min(1.0 + self.consecutive_stimulation * 0.1, self.max_streak_bonus)
        multiplier = self.hormone_level * self.letdown_reflex * streak
        
        # Стимуляция от вставленных предметов
        object_stimulation = breast.insertion_manager.lactation_stimulation
        multiplier *= (1.0 + object_stimulation)

        if self.state == LactationState.PREPARE:
            produced = current_base_rate * 0.3 * multiplier * dt
            if breast.filled > breast._base_volume * 0.15:
                self.state = LactationState.ACTIVE
                breast._emit("lactation_active")

        elif self.state == LactationState.ACTIVE:
            produced = current_base_rate * multiplier * dt
            if self._stimulated:
                produced *= self.stimulation_bonus
                self._stimulated = False
            else:
                self.consecutive_stimulation = max(0, self.consecutive_stimulation - 1)

            if fill_ratio >= 0.85:
                self.state = LactationState.ENGORGED
                breast._emit("engorgement")

        elif self.state == LactationState.ENGORGED:
            produced = current_base_rate * 0.5 * multiplier * dt
            if fill_ratio < 0.7:
                self.state = LactationState.ACTIVE
                breast._emit("engorgement_relief")

        elif self.state == LactationState.DRYING:
            self.base_rate_per_100ml *= 0.99
            current_base_rate = self.calculate_base_rate(breast)
            produced = current_base_rate * 0.5 * dt
            if self.base_rate_per_100ml < 0.1:
                self.state = LactationState.OFF
                breast._emit("lactation_end")
                return 0.0

        if produced > 0:
            milk = defs.get(FluidType.MILK)
            if milk and hasattr(breast, 'add_fluid'):
                actual = breast.add_fluid(milk, produced)
                breast._emit("milk_produced", amount=round(actual, 2))
                return actual

        return 0.0
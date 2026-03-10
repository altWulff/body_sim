# === systems/lactation.py ===
"""
Система лактации
"""

from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass, field
from enum import Enum

from body_sim.core.events import EventBus, EventType, Event

if TYPE_CHECKING:
    from body_sim.anatomy.breasts import BreastComponent


class LactationState(Enum):
    OFF = 0
    PREPARE = 1
    ACTIVE = 2
    ENGORGED = 3
    DRYING = 4


@dataclass
class LactationProfile:
    state: LactationState = LactationState.OFF
    hormone_level: float = 1.0
    letdown_reflex: float = 1.0
    base_rate_per_100ml: float = 3.0
    min_rate: float = 3.0
    max_rate: float = 50.0
    stimulation_sensitivity: float = 2.0
    consecutive_stimulation: int = 0
    max_streak: int = 10
    object_stimulation: float = 0.0


class LactationSystem:
    """Управление лактацией."""

    ENGORGEMENT_THRESHOLD = 0.85

    def __init__(self, profile: Optional[LactationProfile] = None):
        self.profile = profile or LactationProfile()
        self._stimulated = False
        self._total_produced = 0.0

    def start(self):
        if self.profile.state == LactationState.OFF:
            self.profile.state = LactationState.PREPARE

    def stop(self):
        if self.profile.state != LactationState.OFF:
            self.profile.state = LactationState.DRYING

    def stimulate(self, intensity: float = 1.0):
        self._stimulated = True
        self.profile.consecutive_stimulation = min(
            self.profile.max_streak, self.profile.consecutive_stimulation + intensity
        )

    def calculate_rate(self, base_volume: float, fill_ratio: float) -> float:
        """Рассчитать скорость производства."""
        if self.profile.state == LactationState.OFF:
            return 0.0

        # Базовая скорость
        volume_factor = base_volume / 100.0
        base = self.profile.base_rate_per_100ml * volume_factor
        base = max(self.profile.min_rate, min(base, self.profile.max_rate))

        # Штраф от переполнения
        if fill_ratio <= 0.5:
            penalty = 1.0
        elif fill_ratio <= self.ENGORGEMENT_THRESHOLD:
            penalty = 1.0 - (fill_ratio - 0.5) * (0.5 / 0.35)
        else:
            penalty = max(0.2, 0.5 - (fill_ratio - 0.85) * 2.0)

        # Бонусы
        streak = min(1.0 + self.profile.consecutive_stimulation * 0.1, 2.0)
        multiplier = self.profile.hormone_level * self.profile.letdown_reflex * streak
        object_bonus = 1.0 + self.profile.object_stimulation

        return base * penalty * multiplier * object_bonus

    @property
    def is_active(self) -> bool:
        """Активна ли лактация (ACTIVE или ENGORGED)."""
        return self.profile.state in (LactationState.ACTIVE, LactationState.ENGORGED)

    @property
    def is_producing(self) -> bool:
        """Производится ли молоко (включая PREPARE)."""
        return self.profile.state in (
            LactationState.PREPARE,
            LactationState.ACTIVE,
            LactationState.ENGORGED,
        )

    def tick(
        self, delta_time: float, breast: "BreastComponent", event_bus: EventBus
    ) -> dict:
        """Обновление."""
        result = {"produced": 0.0, "state_changed": False, "event": None}

        if self.profile.state == LactationState.OFF:
            return result

        fill_ratio = breast.get_fullness()
        rate = self.calculate_rate(breast._base_volume, fill_ratio)
        produced = rate * delta_time

        # Логика состояний
        if self.profile.state == LactationState.PREPARE:
            produced *= 0.3
            if breast.mixture.total() > breast._base_volume * 0.15:
                self.profile.state = LactationState.ACTIVE
                result["state_changed"] = True
                result["event"] = EventType.LACTATION_ACTIVE

        elif self.profile.state == LactationState.ACTIVE:
            if self._stimulated:
                produced *= self.profile.stimulation_sensitivity
                self._stimulated = False
            else:
                self.profile.consecutive_stimulation = max(
                    0, self.profile.consecutive_stimulation - 0.5 * delta_time
                )

            if fill_ratio >= self.ENGORGEMENT_THRESHOLD:
                self.profile.state = LactationState.ENGORGED
                result["state_changed"] = True
                result["event"] = EventType.ENGORGEMENT

        elif self.profile.state == LactationState.ENGORGED:
            produced *= 0.5
            if fill_ratio < 0.7:
                self.profile.state = LactationState.ACTIVE
                result["state_changed"] = True
                result["event"] = EventType.ENGORGEMENT_RELIEF

        elif self.profile.state == LactationState.DRYING:
            self.profile.base_rate_per_100ml *= 0.99**delta_time
            produced = (
                self.calculate_rate(breast._base_volume, fill_ratio) * 0.5 * delta_time
            )
            if self.profile.base_rate_per_100ml < 0.1:
                self.profile.state = LactationState.OFF
                result["state_changed"] = True
                result["event"] = EventType.LACTATION_END

        # Добавление молока
        if produced > 0:
            from body_sim.core.fluids import FluidType

            actual = breast.add_fluid_by_type(FluidType.MILK, produced)
            self._total_produced += actual
            result["produced"] = actual

            if result["event"]:
                event_bus.emit(
                    Event(
                        type=result["event"],
                        source=breast.component_id,
                        data={"amount": actual, "fill_ratio": fill_ratio},
                    )
                )

        return result

# body_sim/core/types.py
"""
Общие протоколы и типы для системы.
"""

from typing import Protocol, Dict, runtime_checkable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from body_sim.core.enums import FluidType
    from body_sim.core.fluids import BreastFluid


@runtime_checkable
class Tickable(Protocol):
    """Протокол для объектов, обновляемых по времени."""
    
    def tick(self, dt: float) -> None:
        """Обновить состояние за время dt."""
        ...


@runtime_checkable
class Stimulatable(Protocol):
    """Протокол для стимулируемых объектов."""
    
    def stimulate(self, intensity: float = 0.1) -> None:
        """Стимулировать объект."""
        ...


@runtime_checkable
class FluidContainer(Protocol):
    """Протокол для контейнеров жидкостей."""
    
    def add_fluid(self, fluid: "BreastFluid", amount: float) -> float:
        """Добавить жидкость. Возвращает фактически добавленное количество."""
        ...
    
    def remove_fluid(self, amount: float) -> float:
        """Удалить жидкость. Возвращает фактически удалённое количество."""
        ...
    
    @property
    def filled(self) -> float:
        """Текущее количество жидкости."""
        ...
        
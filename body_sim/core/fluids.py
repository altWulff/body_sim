# body_sim/core/fluids.py
"""
Система жидкостей.
"""

from dataclasses import dataclass, field
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from body_sim.core.enums import FluidType

from body_sim.core.enums import FluidType


@dataclass(frozen=True)
class BreastFluid:
    fluid_type: FluidType
    viscosity: float
    density: float


@dataclass
class FluidMixture:
    components: Dict[FluidType, float] = field(default_factory=dict)

    def total(self) -> float:
        return sum(self.components.values())

    def add(self, fluid: 'FluidType | BreastFluid', amount: float) -> None:
        """Добавить жидкость - принимает enum или объект."""
        if isinstance(fluid, BreastFluid):
            fluid_type = fluid.fluid_type
        else:
            fluid_type = fluid
        
        self.components[fluid_type] = self.components.get(fluid_type, 0.0) + amount

    def remove(self, amount: float) -> None:
        total = self.total()
        if total <= 0:
            return
        ratio = amount / total
        actual = min(amount, total)
        for ft in list(self.components):
            self.components[ft] -= self.components[ft] * ratio
            if self.components[ft] <= 0:
                del self.components[ft]
        return actual
    

    def viscosity(self, defs: Dict[FluidType, 'BreastFluid']) -> float:
        total = self.total()
        if total == 0:
            return 0.0
        return sum(
            (v / total) * defs[k].viscosity
            for k, v in self.components.items()
        )
    
    def density(self, defs: Dict[FluidType, 'BreastFluid']) -> float:
        total = self.total()
        if total == 0:
            return 1.0
        return sum(
            (v / total) * defs[k].density
            for k, v in self.components.items()
        )


# Дефолтные определения жидкостей
FLUID_DEFS: Dict[FluidType, BreastFluid] = {
    FluidType.MILK: BreastFluid(FluidType.MILK, 2.0, 1.03),
    FluidType.CUM: BreastFluid(FluidType.CUM, 2.5, 1.03),
    FluidType.WATER: BreastFluid(FluidType.WATER, 0.7, 1.0),
    FluidType.HONEY: BreastFluid(FluidType.HONEY, 6.0, 1.42),
    FluidType.OIL: BreastFluid(FluidType.OIL, 3.0, 0.92),
    FluidType.CUSTOM: BreastFluid(FluidType.CUSTOM, 8.0, 1.5),
}

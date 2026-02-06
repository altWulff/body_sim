# body_sim/core/__init__.py
"""
Ядро системы - базовые типы, константы и утилиты.
"""

from body_sim.core.enums import *
from body_sim.core.fluids import BreastFluid, FluidMixture, FLUID_DEFS
from body_sim.core.constants import *
from body_sim.core.types import Tickable, Stimulatable

__all__ = [
    "BreastFluid", "FluidMixture", "FLUID_DEFS",
    "Tickable", "Stimulatable",
    # Enums и константы импортируются через *
]
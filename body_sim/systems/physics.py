# body_sim/systems/physics.py
"""
Физические расчеты для компонентов BodySim 2.0
"""

import math
from typing import TYPE_CHECKING, Dict
from dataclasses import dataclass

if TYPE_CHECKING:
    from body_sim.anatomy.base import AnatomicalComponent


@dataclass
class PhysicsState:
    """Физическое состояние."""

    pressure: float = 0.0
    tension: float = 0.0
    sag: float = 0.0
    elasticity: float = 1.0


class PhysicsEngine:
    """Движок физических расчетов."""

    MAX_SAG = 1.0
    GRAVITY = 9.81

    @staticmethod
    def calculate_pressure(
        filled_volume: float,
        base_volume: float,
        viscosity: float = 1.0,
        elasticity: float = 1.0,
        sag: float = 0.0,
        external_pressure: float = 0.0,
    ) -> float:
        """Рассчитать давление в полости."""
        if filled_volume <= 0 or base_volume <= 0:
            return external_pressure

        fill_ratio = filled_volume / base_volume
        base_pressure = fill_ratio**2
        viscosity_mod = 1.0 + (viscosity - 1.0) ** 0.8 * 0.3
        elasticity_mod = 1.0 / max(0.1, elasticity**1.2)
        sag_mod = 1.0 + sag * 0.5

        pressure = base_pressure * viscosity_mod * elasticity_mod * sag_mod
        return pressure + external_pressure

    @staticmethod
    def calculate_sag(
        fill_ratio: float,
        size_factor: float = 1.0,
        fluid_density: float = 1.0,
        elasticity: float = 1.0,
        current_sag: float = 0.0,
        dt: float = 1.0,
    ) -> float:
        """Рассчитать провисание с инерцией."""
        if fill_ratio <= 0:
            target = 0.0
        else:
            base_sag = (fill_ratio**2) * 0.5
            density_mod = fluid_density**0.5
            elasticity_mod = 1.0 / max(0.3, elasticity)
            target = base_sag * size_factor * density_mod * elasticity_mod

        inertia = 0.05 * dt
        if current_sag > 0.5:
            inertia *= 0.5

        new_sag = current_sag + (target - current_sag) * inertia
        return min(new_sag, PhysicsEngine.MAX_SAG)

    @staticmethod
    def calculate_flow_rate(
        pressure_diff: float,
        hole_diameter: float,
        viscosity: float = 1.0,
        is_open: bool = True,
    ) -> float:
        """Рассчитать скорость потока (мл/тик)."""
        if not is_open or pressure_diff <= 0 or hole_diameter <= 0:
            return 0.0

        radius = hole_diameter / 2
        area = math.pi * radius**2
        flow = 0.8 * area * pressure_diff / max(viscosity, 0.1)
        return max(0.0, flow)

# body_sim/systems/inflation.py
"""
Система инфляции (растяжения) груди.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
import math

if TYPE_CHECKING:
    from body_sim.anatomy.breast import Breast


@dataclass
class InflationSystem:
    stretch_ratio: float = 1.0
    max_stretch: float = 3.0
    plasticity: float = 0.3
    recovery_rate: float = 0.001
    peak_stretch: float = 1.0
    is_permanently_stretched: bool = False

    def calculate_stretch(self, breast: 'Breast', target_volume: float) -> float:
        normal_volume = breast._base_volume * 1.5
        
        if target_volume <= normal_volume:
            return self._recover()
        
        excess = (target_volume - normal_volume) / normal_volume
        new_stretch = 1.0 + excess
        self.peak_stretch = max(self.peak_stretch, new_stretch)
        
        if new_stretch >= self.max_stretch:
            self.is_permanently_stretched = True
            return self.max_stretch
        
        return new_stretch

    def _recover(self) -> float:
        if self.stretch_ratio <= 1.0:
            return 1.0
        
        elastic_recovery = (self.stretch_ratio - 1.0) * (1.0 - self.plasticity)
        plastic_deformation = 1.0 + (self.stretch_ratio - 1.0) * self.plasticity
        target = plastic_deformation + elastic_recovery * 0.99
        
        return max(1.0, target)

    def apply_stretch(self, breast: 'Breast', dt: float = 1.0) -> None:
        current_volume = breast.volume
        target_stretch = self.calculate_stretch(breast, current_volume)
        
        speed = 0.1 if target_stretch > self.stretch_ratio else 0.05
        self.stretch_ratio += (target_stretch - self.stretch_ratio) * speed * dt
        
        self._update_breast_dimensions(breast)

    def _update_breast_dimensions(self, breast: 'Breast') -> None:
        base_max = breast._base_volume * 1.5
        breast._max_volume = base_max * self.stretch_ratio
        
        stretch_penalty = (self.stretch_ratio - 1.0) * 0.5
        breast._elasticity = max(0.1, breast.base_elasticity - stretch_penalty)
        
        if breast.areola:
            base_diameter = breast.areola.base_diameter
            target_diameter = base_diameter * math.sqrt(self.stretch_ratio)
            breast.areola._current_diameter = target_diameter

    def force_inflate(self, breast: 'Breast', amount_ml: float) -> float:
        available = breast._max_volume * self.max_stretch - breast.filled
        
        if available <= 0:
            return 0.0
        
        actual = min(amount_ml, available)
        self.stretch_ratio = min(
            self.max_stretch,
            self.stretch_ratio + (actual / breast._base_volume) * 0.1
        )
        
        return actual

    def get_skin_tension(self) -> float:
        if self.stretch_ratio <= 1.0:
            return 0.0
        return min(1.0, (self.stretch_ratio - 1.0) / (self.max_stretch - 1.0))

    def get_stretch_marks_risk(self) -> float:
        tension = self.get_skin_tension()
        return tension * tension

    def __str__(self) -> str:
        status = "NORMAL" if self.stretch_ratio < 1.1 else \
                 "STRETCHED" if self.stretch_ratio < 2.0 else \
                 "EXTREME" if self.stretch_ratio < self.max_stretch else "MAX"
        return (
            f"Inflation({status}: ×{self.stretch_ratio:.2f}, "
            f"peak=×{self.peak_stretch:.2f}, tension={self.get_skin_tension():.0%})"
        )
        
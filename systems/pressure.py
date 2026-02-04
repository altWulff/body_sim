# body_sim/systems/pressure.py
"""
Система управления давлением и состояниями сосков.
"""

from dataclasses import dataclass, field
from typing import Optional

from body_sim.core.enums import PressureTier
from body_sim.core.constants import (
    PRESSURE_TIER_HIGH, PRESSURE_TIER_CRITICAL,
    GAPE_OPEN_SPEED, GAPE_CLOSE_SPEED
)


@dataclass
class PressureSystem:
    """Инкапсулирует расчёты давления и состояний."""
    
    TIERS = [0.5, 1.0, 1.8, 2.5]
    _last_tier: Optional[str] = field(default=None, init=False)
    
    def get_tier(self, pressure: float) -> int:
        """Возвращает уровень давления 0-4."""
        for i, threshold in enumerate(self.TIERS):
            if pressure < threshold:
                return i
        return 4
    
    def get_tier_name(self, pressure: float) -> str:
        tier = self.get_tier(pressure)
        names = ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        return names[tier]
    
    def check_changed(self, pressure: float) -> Optional[str]:
        current = self.get_tier_name(pressure)
        if current != self._last_tier:
            self._last_tier = current
            return current
        return None


def get_pressure_tier(pressure: float) -> PressureTier:
    """Определить tier давления."""
    if pressure >= PRESSURE_TIER_CRITICAL:
        return PressureTier.CRITICAL
    elif pressure >= PRESSURE_TIER_HIGH:
        return PressureTier.HIGH
    return PressureTier.LOW


def apply_pressure_to_nipple(nipple: 'Nipple', tier: PressureTier, dt: float) -> None:
    """Применить эффект давления к соску."""
    if tier == PressureTier.CRITICAL:
        # Принудительное раскрытие
        target = nipple.max_gape_diameter * 0.8
        nipple.gape_diameter += (target - nipple.gape_diameter) * GAPE_OPEN_SPEED * dt * 2
        
        # Растяжение ширины
        max_width = nipple.base_width * 3.0
        if nipple.current_width < max_width:
            nipple.current_width += nipple.base_width * 0.01 * dt
            
    elif tier == PressureTier.HIGH:
        # Постепенное раскрытие
        if nipple.gape_diameter < nipple.max_gape_diameter * 0.5:
            nipple.gape_diameter += GAPE_OPEN_SPEED * dt
    
    else:
        # LOW - постепенное закрытие если не заблокирован
        if nipple.gape_diameter > nipple.min_gape_diameter:
            nipple.gape_diameter -= GAPE_CLOSE_SPEED * dt
    
    # Клэмпинг
    nipple.gape_diameter = max(nipple.min_gape_diameter, 
                               min(nipple.gape_diameter, nipple.max_gape_diameter))
                               
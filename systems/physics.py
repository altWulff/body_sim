# body_sim/systems/physics.py
"""
Физические расчёты для груди.
"""

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from body_sim.anatomy.breast import Breast


def calc_pressure(filled: float, volume: float, viscosity: float, 
                elasticity: float, sag: float) -> float:
    """
    Рассчитать давление в груди.
    
    Args:
        filled: Количество жидкости (мл)
        volume: Базовый объём (мл)
        viscosity: Вязкость жидкости
        elasticity: Эластичность тканей (0-1)
        sag: Провисание (0-1)
    """
    if filled <= 0 or volume <= 0:
        return 0.0
    
    fill_ratio = filled / volume
    
    # Базовое давление от заполнения
    base_pressure = fill_ratio ** 2
    
    # Модификатор вязкости
    viscosity_mod = 1.0 + (viscosity - 1.0) * 0.3
    
    # Эластичность снижает давление
    elasticity_mod = 1.0 / max(0.1, elasticity)
    
    # Провисание увеличивает давление (гравитация)
    sag_mod = 1.0 + sag * 0.5
    
    return base_pressure * viscosity_mod * elasticity_mod * sag_mod


def calc_sag_target(breast: 'Breast', fill_ratio: float, density: float) -> float:
    """
    Рассчитать целевое значение провисания.
    
    Args:
        breast: Объект груди
        fill_ratio: Коэффициент заполнения (0-1)
        density: Средняя плотность жидкости
    """
    from body_sim.core.constants import SAG_SIZE_FACTOR
    
    # Базовое провисание от заполнения
    base_sag = fill_ratio ** 2 * 0.5
    
    # Модификатор размера
    size_key = breast.cup.name
    size_mod = SAG_SIZE_FACTOR.get(size_key, 1.0)
    
    # Модификатор плотности (тяжелее = больше sag)
    density_mod = density ** 0.5
    
    # Модификатор эластичности
    elasticity_mod = 1.0 / max(0.3, breast.elasticity)
    
    target = base_sag * size_mod * density_mod * elasticity_mod
    
    # Ограничиваем максимумом
    from body_sim.core.constants import MAX_SAG
    return min(target, MAX_SAG)
    
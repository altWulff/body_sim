# body_sim/anatomy/nipple.py
"""
Соски и ареолы.
"""

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from body_sim.core.enums import Color, NippleShape, NippleType

if TYPE_CHECKING:
    pass  # Для будущих ссылок


@dataclass
class Nipple:
    # Базовые размеры
    base_length: float
    base_width: float
    base_min_gape_diameter: float = 0.0
    
    # Текущие размеры
    current_length: float = field(init=False)
    current_width: float = field(init=False)
    
    # Состояние отверстия
    gape_diameter: float = 0.0
    max_gape_diameter: float = field(init=False)
    
    color: Color = Color.LIGHT_PINK
    erect_multiplier: float = 1.5
    
    # Обратная ссылка на ареолу
    areola: 'Areola' = field(default=None, repr=False)
        
    def __post_init__(self):
        if self.base_length < 0:
            raise ValueError("Length must be non-negative")
        if self.base_width < 0:
            raise ValueError("Width must be non-negative")
        
        self.current_length = self.base_length
        self.current_width = self.base_width
        
        # Max gape зависит от ширины соска (до 90% ширины)
        # Не ограничиваем жестко - пусть растягивается от давления
        self.max_gape_diameter = self.current_width * 0.9
        
        self.gape_diameter = max(self.gape_diameter, self.base_min_gape_diameter)
        self.gape_diameter = min(self.gape_diameter, self.max_gape_diameter)

    @property
    def effective_gape(self) -> float:
        """Эффективный диаметр отверстия без жесткого ограничения."""
        if not self.is_open:
            return 0.0
        openness = self.gape_diameter / self.current_width if self.current_width > 0 else 0
        return self.gape_diameter * openness
    
    def stretch(self, factor: float) -> None:
        """Растянуть сосок - увеличивает max_gape пропорционально."""
        if factor <= 0:
            return
        
        self.current_width *= factor
        self.current_length *= factor
        
        # Обновляем max_gape (90% от новой ширины)
        self.max_gape_diameter = self.current_width * 0.9
        
        # Если текущий gape больше нового max, уменьшаем
        if self.gape_diameter > self.max_gape_diameter:
            self.gape_diameter = self.max_gape_diameter
        
        if self.areola is not None:
            self.areola._update_diameter()
    
    def open_from_pressure(self, pressure: float, max_pressure: float = 2.0) -> None:
        """Открыть сосок от давления в груди (0..max_pressure -> 0..max_gape)."""
        if pressure <= 0:
            return
        
        # Чем больше давление, тем больше отверстие
        openness_ratio = min(pressure / max_pressure, 1.0)
        target_gape = self.max_gape_diameter * openness_ratio
        
        # Плавное открытие (30% за шаг)
        self.gape_diameter += (target_gape - self.gape_diameter) * 0.3
        self.gape_diameter = max(self.gape_diameter, self.base_min_gape_diameter)
        
    @property
    def length(self) -> float:
        return self.current_length

    @property
    def width(self) -> float:
        return self.current_width
    
    @property
    def min_gape_diameter(self) -> float:
        stretch_factor = self.current_width / self.base_width if self.base_width > 0 else 1.0
        return self.base_min_gape_diameter * max(stretch_factor * 0.5, 1.0)

    @property
    def erect_length(self) -> float:
        return self.current_length * self.erect_multiplier

    @property
    def is_open(self) -> bool:
        return self.gape_diameter > 0.05

    @property
    def stretch_ratio(self) -> float:
        return self.current_width / self.base_width if self.base_width > 0 else 1.0

    @property
    def nipple_type(self) -> NippleType:
        g = self.gape_diameter
        l = self.current_length
        w = self.current_width

        if g >= 0.35 or (g / w > 0.6 if w > 0 else False):
            return NippleType.GAPING_STRETCHED

        if l < 0.3:
            return NippleType.TINY_FLAT if w < 0.5 else NippleType.CUTE_SMALL
        elif l < 0.8:
            if w < 0.7:
                return NippleType.CUTE_SMALL
            elif w < 1.1:
                return NippleType.PERKY_MEDIUM
            else:
                return NippleType.LARGE_THICK
        elif l < 1.5:
            return NippleType.LARGE_THICK if w >= 1.2 else NippleType.PUFFY
        else:
            return NippleType.HYPER_LONG

    @property
    def shape(self) -> NippleShape:
        t = self.nipple_type
        if t == NippleType.TINY_FLAT:
            return NippleShape.FLAT
        if t == NippleType.INVERTED:
            return NippleShape.INVERTED
        if t in (NippleType.PUFFY, NippleType.GAPING_STRETCHED):
            return NippleShape.PUFFY
        if self.current_length > self.current_width * 1.8:
            return NippleShape.CONICAL
        return NippleShape.CYLINDRICAL

    def _notify_areola_stretch(self) -> None:
        """Уведомить ареолу об изменении размеров."""
        if self.areola is not None:
            self.areola._update_diameter()

    def __str__(self) -> str:
        stretch_pct = (self.stretch_ratio - 1) * 100
        stretch_str = f" stretched +{stretch_pct:.0f}%" if stretch_pct > 5 else ""
        return (
            f"Nipple(base={self.base_length:.1f}x{self.base_width:.1f}cm, "
            f"current={self.current_length:.1f}x{self.current_width:.1f}cm{stretch_str}, "
            f"gape={self.gape_diameter:.2f}/{self.max_gape_diameter:.2f}cm, "
            f"open={self.is_open}, type={self.nipple_type.name})"
        )


@dataclass
class Areola:
    base_diameter: float
    color: Color = Color.LIGHT_PINK
    nipples: List[Nipple] = field(default_factory=list)
    puffiness: float = 0.0
    sensitivity: float = 0.7
    
    _current_diameter: float = field(init=False, repr=False)
    nipple_stretch_influence: float = 0.6

    def __post_init__(self):
        if self.base_diameter <= 0:
            raise ValueError("Areola diameter must be positive")
        if not (0.0 <= self.puffiness <= 1.0):
            raise ValueError("Puffiness must be between 0 and 1")
        if not (0.0 <= self.sensitivity <= 1.0):
            raise ValueError("Sensitivity must be between 0 and 1")
        
        self._current_diameter = self.base_diameter
        
        if not self.nipples:
            nipple = Nipple(base_length=0.5, base_width=0.8)
            self.add_nipple(nipple)
        else:
            for nipple in self.nipples:
                self._bind_nipple(nipple)
        
        self._update_diameter()

    def _bind_nipple(self, nipple: Nipple) -> None:
        nipple.areola = self

    def add_nipple(self, nipple: Nipple) -> None:
        self._bind_nipple(nipple)
        self.nipples.append(nipple)
        self._update_diameter()

    def _update_diameter(self) -> None:
        """Обновить диаметр ареолы на основе растяжения сосков."""
        if not self.nipples:
            self._current_diameter = self.base_diameter
            return
        
        avg_stretch = sum(n.stretch_ratio for n in self.nipples) / len(self.nipples)
        stretch_expansion = (avg_stretch - 1.0) * self.nipple_stretch_influence
        
        max_nipple_width = max(n.current_width for n in self.nipples)
        width_ratio = max_nipple_width / (self.base_diameter * 0.3)
        width_expansion = max(0, (width_ratio - 1) * 0.5)
        
        total_expansion = 1.0 + stretch_expansion + width_expansion
        target_diameter = self.base_diameter * total_expansion
        self._current_diameter += (target_diameter - self._current_diameter) * 0.3

    @property
    def diameter(self) -> float:
        return self._current_diameter
    
    @property
    def base_radius(self) -> float:
        return self.base_diameter / 2
    
    @property
    def current_radius(self) -> float:
        return self._current_diameter / 2
    
    @property
    def expansion_ratio(self) -> float:
        return self._current_diameter / self.base_diameter if self.base_diameter > 0 else 1.0

    def __str__(self) -> str:
        expansion_pct = (self.expansion_ratio - 1) * 100
        expansion_str = f" expanded +{expansion_pct:.0f}%" if expansion_pct > 5 else ""
        return (
            f"Areola(base={self.base_diameter:.1f}cm, "
            f"current={self.diameter:.1f}cm{expansion_str}, "
            f"puffiness={self.puffiness:.1f}, sensitivity={self.sensitivity:.1f}, "
            f"nipples=[{len(self.nipples)}])"
        )
        
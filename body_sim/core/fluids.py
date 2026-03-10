# === core/fluids.py ===
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import math

class FluidType(Enum):
    WATER = ("water", 1.0, 1.0, "clear")
    SALIVA = ("saliva", 1.01, 1.1, "clear")
    SEMEN = ("semen", 1.05, 3.0, "cream")
    MILK = ("milk", 1.03, 1.5, "white")
    BLOOD = ("blood", 1.06, 4.0, "red")
    GASTRIC_JUICE = ("gastric_juice", 1.02, 2.0, "yellow")
    MAGIC_FLUID = ("magic_fluid", 1.1, 2.0, "glowing")
    AIR = ("air", 0.0012, 0.01, "invisible")
    CUSTOM = ("custom", 1.0, 1.0, "unknown")
    
    def __init__(self, fluid_name: str, density: float, viscosity: float, color: str):
        self.fluid_name = fluid_name
        self.density = density  # г/мл
        self.viscosity = viscosity  # относительно воды
        self.color = color

@dataclass 
class FluidProperties:
    """Свойства жидкости."""
    density: float = 1.0  # г/мл
    viscosity: float = 1.0  # относительно воды
    color: str = "clear"
    temperature: float = 37.0
    fertility_factor: float = 0.0

@dataclass
class Fluid:
    fluid_type: FluidType
    volume: float
    source_component: str
    properties: FluidProperties = field(default_factory=FluidProperties)  # <-- добавлено
    dna_profile: Optional[str] = None
    temperature: float = 37.0
    
    def merge(self, other: 'Fluid') -> 'Fluid':
        total_vol = self.volume + other.volume
        # Усредняем свойства
        new_density = (self.volume * self.properties.density + 
                      other.volume * other.properties.density) / total_vol
        new_viscosity = (self.volume * self.properties.viscosity + 
                        other.volume * other.properties.viscosity) / total_vol
        
        return Fluid(
            fluid_type=self.fluid_type if self.volume > other.volume else other.fluid_type,
            volume=total_vol,
            source_component=f"mixed:{self.source_component}+{other.source_component}",
            properties=FluidProperties(
                density=new_density,
                viscosity=new_viscosity,
                color=self.properties.color if self.volume > other.volume else other.properties.color
            )
        )


class FluidMixture:
    """Улучшенная система смешивания жидкостей с физическими свойствами."""
    
    def __init__(self):
        self._contents: Dict[FluidType, float] = {}  # Тип -> количество (мл)
        self._history: List[Tuple[FluidType, float, datetime]] = []
        
    def add(self, fluid_type: FluidType, amount: float, source: str = "unknown") -> float:
        """Добавить жидкость."""
        if amount <= 0:
            return 0.0
        
        from datetime import datetime
        self._contents[fluid_type] = self._contents.get(fluid_type, 0.0) + amount
        self._history.append((fluid_type, amount, datetime.now()))
        return amount
    
    def remove(self, amount: float, prefer_types: Optional[List[FluidType]] = None) -> Dict[FluidType, float]:
        """Удалить жидкость с возможностью приоритета."""
        if amount <= 0 or not self._contents:
            return {}
        
        removed: Dict[FluidType, float] = {}
        remaining = amount
        
        # Сначала удаляем предпочтительные типы
        if prefer_types:
            for ftype in prefer_types:
                if remaining <= 0:
                    break
                if ftype in self._contents:
                    take = min(self._contents[ftype], remaining)
                    self._contents[ftype] -= take
                    removed[ftype] = take
                    remaining -= take
                    if self._contents[ftype] <= 0:
                        del self._contents[ftype]
        
        # Затем остальные пропорционально
        if remaining > 0 and self._contents:
            total = sum(self._contents.values())
            for ftype, vol in list(self._contents.items()):
                if remaining <= 0:
                    break
                ratio = vol / total
                take = min(vol, remaining * ratio)
                self._contents[ftype] -= take
                removed[ftype] = removed.get(ftype, 0.0) + take
                remaining -= take
                if self._contents[ftype] <= 0:
                    del self._contents[ftype]
        
        return removed
    
    def remove_all(self, fluid_type: FluidType) -> float:
        """Удалить все жидкости определенного типа."""
        return self._contents.pop(fluid_type, 0.0)
    
    def total(self) -> float:
        """Общий объем."""
        return max(0.0, sum(self._contents.values()))
    
    def get_amount(self, fluid_type: FluidType) -> float:
        """Количество конкретного типа."""
        return self._contents.get(fluid_type, 0.0)
    
    def composition(self) -> Dict[FluidType, float]:
        """Состав смеси (тип -> объем в мл)."""
        return self._contents.copy()
    
    def viscosity(self) -> float:
        """Средняя вязкость смеси."""
        total = self.total()
        if total == 0:
            return 1.0
        
        visc_sum = sum(
            amount * ftype.viscosity 
            for ftype, amount in self._contents.items()
        )
        return visc_sum / total
    
    def density(self) -> float:
        """Средняя плотность."""
        total = self.total()
        if total == 0:
            return 1.0
        
        dens_sum = sum(
            amount * ftype.density
            for ftype, amount in self._contents.items()
        )
        return dens_sum / total
    
    def dominant_type(self) -> Optional[FluidType]:
        """Преобладающий тип жидкости."""
        if not self._contents:
            return None
        return max(self._contents.items(), key=lambda x: x[1])[0]
    
    def clone(self) -> 'FluidMixture':
        """Создать копию."""
        new = FluidMixture()
        new._contents = self._contents.copy()
        return new
    
    def to_fluids_list(self, source: str = "mixture") -> List[Fluid]:
        """Конвертировать в список объектов Fluid."""
        return [
            Fluid(
                fluid_type=ftype,
                volume=vol,
                source_component=source
            )
            for ftype, vol in self._contents.items() if vol > 0
        ]
    
    def __repr__(self) -> str:
        comp = ", ".join(f"{ft.name}:{vol:.1f}ml" for ft, vol in self._contents.items())
        return f"FluidMixture[{comp}]"

class FluidContainer:
    """Улучшенный контейнер с поддержкой смесей и утечек."""
    
    def __init__(self, max_capacity: float):
        self.max_capacity = max_capacity
        self.mixture = FluidMixture()
        self._leakage_rate = 0.0
        self._pressure = 0.0
        
    @property
    def current_volume(self) -> float:
        return self.mixture.total()
        
    def add_fluid(self, fluid: Fluid) -> float:
        """Добавить жидкость (обратная совместимость)."""
        overflow = 0.0
        current = self.mixture.total()
        
        if current + fluid.volume > self.max_capacity:
            available = self.max_capacity - current
            if available <= 0:
                return fluid.volume
            overflow = fluid.volume - available
            fluid.volume = available
        
        self.mixture.add(fluid.fluid_type, fluid.volume, fluid.source_component)
        return overflow
            
    def remove_fluid(self, amount: float, fluid_type: FluidType = None) -> List[Fluid]:
        """Удалить жидкость (обратная совместимость)."""
        if fluid_type:
            removed = self.mixture.remove_all(fluid_type)
            if removed > 0:
                return [Fluid(fluid_type=fluid_type, volume=removed, source_component=self.__class__.__name__)]
            return []
        
        # Удаляем любые
        removed_dict = self.mixture.remove(amount)
        return [
            Fluid(fluid_type=ftype, volume=vol, source_component=self.__class__.__name__)
            for ftype, vol in removed_dict.items()
        ]
        
    def transfer_to(self, target: 'FluidContainer', amount: float, 
                   fluid_type: FluidType = None, event_bus: Any = None):
        """Передача жидкости с эмиссией события."""
        removed = self.remove_fluid(amount, fluid_type)
        total_transferred = 0.0
        total_overflow = 0.0
        
        for fluid in removed:
            overflow = target.add_fluid(fluid)
            transferred = fluid.volume - overflow
            total_transferred += transferred
            total_overflow += overflow
            
            if event_bus and hasattr(self, 'component_id'):
                from body_sim.core.events import Event, EventType
                event_bus.emit(Event(
                    type=EventType.FLUID_TRANSFER,
                    source=self.component_id,
                    target=getattr(target, 'component_id', 'unknown'),
                    data={
                        'fluid_type': fluid.fluid_type.value,
                        'volume': transferred,
                        'overflow': overflow
                    }
                ))
        
        return total_transferred, total_overflow
                
    def get_fullness(self) -> float:
        return self.current_volume / self.max_capacity if self.max_capacity > 0 else 0.0
    
    def get_pressure(self, base_volume: float, elasticity: float = 1.0) -> float:
        """Рассчитать давление в контейнере."""
        if self.mixture.total() <= 0 or base_volume <= 0:
            return 0.0
        
        fill_ratio = self.mixture.total() / base_volume
        base_pressure = fill_ratio ** 2
        viscosity_mod = 1.0 + (self.mixture.viscosity() - 1.0) * 0.3
        elasticity_mod = 1.0 / max(0.1, elasticity)
        
        return base_pressure * viscosity_mod * elasticity_mod

    @property
    def fluids(self) -> List[Fluid]:
        """
        Обратная совместимость: возвращает список Fluid объектов.
        """
        return self.mixture.to_fluids_list(self.__class__.__name__)
    
    @fluids.setter
    def fluids(self, value: List[Fluid]):
        """
        Обратная совместимость: устанавливает список жидкостей.
        """
        # Очищаем текущую смесь
        self.mixture._contents.clear()
        # Добавляем новые жидкости
        for fluid in value:
            if fluid.volume > 0:
                self.mixture.add(fluid.fluid_type, fluid.volume, fluid.source_component)
                
        
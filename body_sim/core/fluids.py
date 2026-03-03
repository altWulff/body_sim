# === core/fluids.py ===
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class FluidType(Enum):
    # Базовые
    WATER = "water"
    CUSTOM = "custom"
    
    # Репродуктивные
    SEMEN = "semen"
    MILK = "milk"
    VAGINAL_LUBRICATION = "vaginal_lubrication"
    CERVICAL_MUCUS = "cervical_mucus"
    AMNIOTIC_FLUID = "amniotic_fluid"
    EGG_WHITE = "egg_white"  # Овариальная жидкость
    
    # Пищеварительные
    SALIVA = "saliva"
    GASTRIC_JUICE = "gastric_juice"
    BILE = "bile"
    FECES = "feces"
    URINE = "urine"
    PEE = "pee"  # Альтернативное название
    
    # Кровеносные/иммунные
    BLOOD = "blood"
    LYMPH = "lymph"
    PLASMA = "plasma"
    PUS = "pus"  # Гной (для инфекций)
    
    # Нервная система
    CEREBROSPINAL_FLUID = "cerebrospinal_fluid"
    SYNOVIAL_FLUID = "synovial_fluid"  # Суставная жидкость
    
    # Внешние выделения
    SWEAT = "sweat"
    TEARS = "tears"
    EAR_WAX = "ear_wax"
    NASAL_MUCUS = "nasal_mucus"
    
    # Специфические/магические (для фэнтези рас)
    DRAGON_ACID = "dragon_acid"
    SLIME = "slime"
    VENOM = "venom"
    HONEY = "honey"
    NECTAR = "nectar"
    
    # Медицинские/химические
    CONTRAST_DYE = "contrast_dye"  # Контраст для рентгена
    SALINE = "saline"  # Физраствор
    LUBRICANT = "lubricant"  # Искусственная смазка
    MEDICINE = "medicine"  # Лекарства
    ALCOHOL = "alcohol"
    POISON = "poison"

@dataclass
class Fluid:
    fluid_type: FluidType
    volume: float
    source_component: str
    properties: Dict[str, Any] = field(default_factory=dict)
    dna_profile: Optional[str] = None
    temperature: float = 37.0  # °C
    
    def merge(self, other: 'Fluid') -> 'Fluid':
        total_vol = self.volume + other.volume
        # Приоритет по объему, но некоторые типы доминируют
        dominant_type = self._get_dominant_type(other)
        
        return Fluid(
            fluid_type=dominant_type,
            volume=total_vol,
            source_component=f"mixed:{self.source_component}+{other.source_component}",
            properties={**self.properties, **other.properties},
            temperature=(self.temperature * self.volume + other.temperature * other.volume) / total_vol
        )
        
    def _get_dominant_type(self, other: 'Fluid') -> FluidType:
        """Определить доминирующий тип при смешивании."""
        # Приоритет: кислота > яд > гной > кровь > сперма > молоко > остальное
        priority = [
            FluidType.DRAGON_ACID, FluidType.VENOM, FluidType.POISON,
            FluidType.PUS, FluidType.BLOOD, FluidType.SEMEN,
            FluidType.MILK, FluidType.AMNIOTIC_FLUID
        ]
        
        for p in priority:
            if self.fluid_type == p or other.fluid_type == p:
                return p
                
        return self.fluid_type if self.volume > other.volume else other.fluid_type

class FluidContainer:
    def __init__(self, max_capacity: float):
        self.max_capacity = max_capacity
        self.fluids: List[Fluid] = []
        self._leakage_rate = 0.0
        
    def add_fluid(self, fluid: Fluid) -> float:
        current = sum(f.volume for f in self.fluids)
        if current + fluid.volume <= self.max_capacity:
            self.fluids.append(fluid)
            return 0.0
        else:
            available = self.max_capacity - current
            if available > 0:
                fluid.volume = available
                self.fluids.append(fluid)
            return fluid.volume - available
            
    def remove_fluid(self, amount: float, fluid_type: FluidType = None) -> List[Fluid]:
        removed = []
        remaining = amount
        
        for fluid in self.fluids[:]:
            if remaining <= 0:
                break
            if fluid_type is None or fluid.fluid_type == fluid_type:
                if fluid.volume <= remaining:
                    removed.append(fluid)
                    self.fluids.remove(fluid)
                    remaining -= fluid.volume
                else:
                    fluid.volume -= remaining
                    removed.append(Fluid(
                        fluid_type=fluid.fluid_type,
                        volume=remaining,
                        source_component=fluid.source_component,
                        properties=fluid.properties.copy(),
                        temperature=fluid.temperature
                    ))
                    remaining = 0
        return removed
        
    def transfer_to(self, target: 'FluidContainer', amount: float, 
                   fluid_type: FluidType = None, event_bus: Any = None):
        removed = self.remove_fluid(amount, fluid_type)
        for fluid in removed:
            overflow = target.add_fluid(fluid)
            if event_bus and hasattr(self, 'component_id'):
                from body_sim.core.events import Event, EventType
                event_bus.emit(Event(
                    type=EventType.FLUID_TRANSFER,
                    source=self.component_id,
                    target=target.component_id if hasattr(target, 'component_id') else 'unknown',
                    data={
                        'fluid_type': fluid.fluid_type.value,
                        'volume': fluid.volume - overflow,
                        'overflow': overflow,
                        'temperature': fluid.temperature
                    }
                ))
                
    def get_fullness(self) -> float:
        return sum(f.volume for f in self.fluids) / self.max_capacity if self.max_capacity > 0 else 0.0
        
    def get_total_by_type(self, fluid_type: FluidType) -> float:
        """Получить общий объем жидкости определенного типа."""
        return sum(f.volume for f in self.fluids if f.fluid_type == fluid_type)
        
    def get_composition(self) -> Dict[FluidType, float]:
        """Получить процентный состав жидкостей."""
        total = sum(f.volume for f in self.fluids)
        if total == 0:
            return {}
        return {
            ft: sum(f.volume for f in self.fluids if f.fluid_type == ft) / total 
            for ft in set(f.fluid_type for f in self.fluids)
        }

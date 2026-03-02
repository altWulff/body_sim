# === core/fluids.py ===
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class FluidType(Enum):
    WATER = "water"
    SALIVA = "saliva"
    SEMEN = "semen"
    MILK = "milk"
    BLOOD = "blood"
    GASTRIC_JUICE = "gastric_juice"
    CUSTOM = "custom"

@dataclass
class Fluid:
    fluid_type: FluidType
    volume: float
    source_component: str
    properties: Dict[str, Any] = field(default_factory=dict)
    dna_profile: Optional[str] = None
    
    def merge(self, other: 'Fluid') -> 'Fluid':
        total_vol = self.volume + other.volume
        return Fluid(
            fluid_type=self.fluid_type if self.volume > other.volume else other.fluid_type,
            volume=total_vol,
            source_component=f"mixed:{self.source_component}+{other.source_component}",
            properties={**self.properties, **other.properties}
        )

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
                        properties=fluid.properties.copy()
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
                        'overflow': overflow
                    }
                ))
                
    def get_fullness(self) -> float:
        return sum(f.volume for f in self.fluids) / self.max_capacity if self.max_capacity > 0 else 0.0
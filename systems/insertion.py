# body_sim/systems/insertion.py
"""
Система вставляемых предметов.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import math

from body_sim.core.enums import FluidType, InsertableType, InsertableMaterial


@dataclass
class InsertableObject:
    name: str
    insertable_type: InsertableType
    material: InsertableMaterial
    length: float
    diameter: float
    width: float = 0.0
    
    volume_ml: float = field(init=False)
    is_expandable: bool = False
    expansion_ratio: float = 1.0
    is_hollow: bool = False
    inner_diameter: float = 0.0
    
    blocks_leakage: bool = True
    leakage_reduction: float = 1.0
    stimulates_lactation: float = 0.0
    pressure_increase: float = 0.0
    
    is_inserted: bool = False
    inserted_depth: float = 0.0
    expansion_current: float = 1.0

    def __post_init__(self):
        if self.width > 0:
            self.volume_ml = (self.length * self.width * self.diameter) * 0.8
        else:
            radius = self.diameter / 2
            self.volume_ml = math.pi * radius ** 2 * self.length

    @property
    def effective_volume(self) -> float:
        return self.volume_ml * self.expansion_current

    @property
    def effective_diameter(self) -> float:
        return self.diameter * math.sqrt(self.expansion_current)

    def expand(self, ratio: float) -> bool:
        if not self.is_expandable:
            return False
        self.expansion_current = min(ratio, self.expansion_ratio)
        return True

    def deflate(self) -> None:
        self.expansion_current = 1.0

    def can_fit_through(self, gape_diameter: float) -> bool:
        required = self.effective_diameter * 1.1
        return gape_diameter >= required

    def insert(self, depth: Optional[float] = None) -> None:
        self.is_inserted = True
        self.inserted_depth = min(depth or self.length, self.length)

    def remove(self) -> None:
        self.is_inserted = False
        self.inserted_depth = 0.0
        self.deflate()


@dataclass
class InsertionManager:
    inserted_objects: List[InsertableObject] = field(default_factory=list)
    max_objects: int = 3

    @property
    def total_volume(self) -> float:
        return sum(obj.effective_volume for obj in self.inserted_objects)

    @property
    def total_leakage_reduction(self) -> float:
        if not self.inserted_objects:
            return 0.0
        
        if any(obj.blocks_leakage for obj in self.inserted_objects):
            return 1.0
        
        reduction = 1.0
        for obj in self.inserted_objects:
            reduction *= (1.0 - obj.leakage_reduction)
        
        return 1.0 - reduction

    @property
    def lactation_stimulation(self) -> float:
        return sum(obj.stimulates_lactation for obj in self.inserted_objects)

    @property
    def pressure_modifier(self) -> float:
        return sum(obj.pressure_increase for obj in self.inserted_objects)

    def can_insert(self, obj: InsertableObject) -> bool:
        return len(self.inserted_objects) < self.max_objects

    def insert(self, obj: InsertableObject, depth: Optional[float] = None) -> bool:
        if not self.can_insert(obj):
            return False
        
        obj.insert(depth)
        self.inserted_objects.append(obj)
        return True

    def remove(self, index: int) -> Optional[InsertableObject]:
        if 0 <= index < len(self.inserted_objects):
            obj = self.inserted_objects.pop(index)
            obj.remove()
            return obj
        return None

    def remove_all(self) -> List[InsertableObject]:
        removed = self.inserted_objects.copy()
        for obj in removed:
            obj.remove()
        self.inserted_objects.clear()
        return removed

    def expand_object(self, index: int, ratio: float) -> bool:
        if 0 <= index < len(self.inserted_objects):
            obj = self.inserted_objects[index]
            if obj.is_expandable:
                return obj.expand(ratio)
        return False

    def __len__(self) -> int:
        return len(self.inserted_objects)

    def __str__(self) -> str:
        if not self.inserted_objects:
            return "No inserted objects"
        
        lines = [
            f"Inserted: {len(self.inserted_objects)}/{self.max_objects}",
            f"Total volume: {self.total_volume:.1f}ml",
            f"Leakage blocked: {self.total_leakage_reduction:.0%}",
            f"Lactation bonus: +{self.lactation_stimulation:.0%}"
        ]
        for i, obj in enumerate(self.inserted_objects):
            lines.append(f"  [{i}] {obj}")
        
        return "\n".join(lines)


# Фабричные функции
def create_plug(diameter: float = 1.0, length: float = 2.0) -> InsertableObject:
    return InsertableObject(
        name="Silicone Plug",
        insertable_type=InsertableType.PLUG,
        material=InsertableMaterial.SILICONE,
        length=length, diameter=diameter,
        blocks_leakage=True, leakage_reduction=0.0,
        stimulates_lactation=0.1
    )

def create_tube(diameter: float = 0.8, length: float = 5.0, 
                inner_diameter: float = 0.5) -> InsertableObject:
    return InsertableObject(
        name="Drainage Tube",
        insertable_type=InsertableType.TUBE,
        material=InsertableMaterial.SILICONE,
        length=length, diameter=diameter,
        is_hollow=True, inner_diameter=inner_diameter,
        blocks_leakage=False, leakage_reduction=0.3,
        stimulates_lactation=0.05
    )

def create_balloon(diameter: float = 1.5, max_diameter: float = 5.0) -> InsertableObject:
    ratio = (max_diameter / diameter) ** 2 if diameter > 0 else 1.0
    return InsertableObject(
        name="Inflatable Balloon",
        insertable_type=InsertableType.BALLOON,
        material=InsertableMaterial.LATEX,
        length=max_diameter, diameter=diameter,
        is_expandable=True, expansion_ratio=ratio,
        blocks_leakage=True, leakage_reduction=0.0,
        pressure_increase=0.5
    )

def create_beads(count: int = 3, diameter: float = 1.0) -> InsertableObject:
    return InsertableObject(
        name=f"Bead Chain ({count})",
        insertable_type=InsertableType.BEADS,
        material=InsertableMaterial.SILICONE,
        length=diameter * count * 1.5, diameter=diameter,
        blocks_leakage=False, leakage_reduction=0.7,
        stimulates_lactation=0.15
    )

def create_egg(diameter: float = 2.0, length: float = 3.0) -> InsertableObject:
    return InsertableObject(
        name="Smooth Egg",
        insertable_type=InsertableType.EGG,
        material=InsertableMaterial.GLASS,
        length=length, diameter=diameter, width=diameter * 0.7,
        blocks_leakage=True, leakage_reduction=0.0
    )

def create_vibrator(diameter: float = 1.2, length: float = 4.0) -> InsertableObject:
    return InsertableObject(
        name="Stimulating Vibrator",
        insertable_type=InsertableType.VIBRATOR,
        material=InsertableMaterial.SILICONE,
        length=length, diameter=diameter,
        blocks_leakage=True, leakage_reduction=0.1,
        stimulates_lactation=0.4, pressure_increase=0.2
    )

def create_needle(diameter: float = 0.3, length: float = 6.0) -> InsertableObject:
    return InsertableObject(
        name="Drainage Needle",
        insertable_type=InsertableType.NEEDLE,
        material=InsertableMaterial.METAL,
        length=length, diameter=diameter,
        is_hollow=True, inner_diameter=diameter * 0.6,
        blocks_leakage=False, leakage_reduction=-0.5
    )
    
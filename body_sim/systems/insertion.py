# body_sim/systems/insertion.py
"""
Система управления вставленными объектами
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class InsertionType(Enum):
    """Типы вставляемых объектов."""
    PLUG = "plug"
    TUBE = "tube"
    PUMP = "pump"
    FOREIGN = "foreign"
    MAGICAL = "magical"


@dataclass
class InsertedObject:
    """Объект внутри полости."""
    name: str
    volume: float  # мл
    length: float = 5.0  # см
    diameter: float = 1.0  # см
    insertion_type: InsertionType = InsertionType.FOREIGN
    is_blocking: bool = False
    is_permeable: bool = False
    pressure_modifier: float = 0.0
    lactation_stimulation: float = 0.0
    material: str = "silicone"
    position_depth: float = 0.0  # Глубина вставки (0-100%)


class InsertionManager:
    """Управление объектами внутри анатомических полостей."""
    
    def __init__(self, max_volume: float = float('inf')):
        self.objects: List[InsertedObject] = []
        self.max_volume = max_volume
        self._cache_valid: bool = False
        self._cached_volume: float = 0.0
    
    def insert(self, obj: InsertedObject) -> bool:
        """Вставить объект."""
        if self.total_volume + obj.volume > self.max_volume:
            return False
        
        self.objects.append(obj)
        self._cache_valid = False
        return True
    
    def remove(self, obj_name: str) -> Optional[InsertedObject]:
        """Удалить объект по имени."""
        for i, obj in enumerate(self.objects):
            if obj.name == obj_name:
                self._cache_valid = False
                return self.objects.pop(i)
        return None
    
    def remove_all(self) -> List[InsertedObject]:
        """Удалить все объекты."""
        removed = self.objects.copy()
        self.objects.clear()
        self._cache_valid = False
        return removed
    
    def find_by_type(self, ins_type: InsertionType) -> List[InsertedObject]:
        """Найти объекты по типу."""
        return [obj for obj in self.objects if obj.insertion_type == ins_type]
    
    def is_blocked(self) -> bool:
        """Есть ли блокирующий объект?"""
        return any(obj.is_blocking for obj in self.objects)
    
    @property
    def total_volume(self) -> float:
        """Общий объем вставленных объектов."""
        if not self._cache_valid:
            self._cached_volume = sum(obj.volume for obj in self.objects)
            self._cache_valid = True
        return self._cached_volume
    
    @property
    def total_leakage_reduction(self) -> float:
        """Общее снижение утечки (0-1)."""
        if not self.objects:
            return 0.0
        
        reduction = 0.0
        for obj in self.objects:
            if obj.is_blocking:
                reduction += 0.9
            elif not obj.is_permeable:
                reduction += 0.3
        
        return min(1.0, reduction)
    
    @property
    def pressure_modifier(self) -> float:
        """Модификатор давления от объектов."""
        return sum(obj.pressure_modifier for obj in self.objects)
    
    @property
    def lactation_stimulation(self) -> float:
        """Общая стимуляция лактации."""
        return sum(obj.lactation_stimulation for obj in self.objects)
    
    def get_state(self) -> Dict[str, Any]:
        """Состояние для сериализации."""
        return {
            'count': len(self.objects),
            'total_volume': self.total_volume,
            'blocked': self.is_blocked(),
            'objects': [
                {
                    'name': obj.name,
                    'type': obj.insertion_type.value,
                    'volume': obj.volume,
                    'blocking': obj.is_blocking
                }
                for obj in self.objects
            ]
        }
        
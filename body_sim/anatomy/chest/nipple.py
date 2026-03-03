# anatomy/chest/nipple.py
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class NippleState(Enum):
    SOFT = "soft"
    ERECT = "erect"
    INVERTED = "inverted"  # Втянутый

@dataclass
class Nipple:
    name: str = "nipple"
    size: float = 0.5  # Длина в см
    diameter: float = 1.0  # Диаметр в см
    state: NippleState = NippleState.SOFT
    sensitivity: float = 1.0
    plug: Optional['NipplePlug'] = None
    hole_gape: float = 0.0  # Растяжение отверстия (для пенетрации)
    can_penetration: bool = False  # Возможность пенетрации после растяжки
    
    def erect(self):
        if self.state != NippleState.INVERTED:
            self.state = NippleState.ERECT
            self.size *= 1.3
            
    def relax(self):
        if self.state == NippleState.ERECT:
            self.size /= 1.3
        self.state = NippleState.SOFT
            
    def stretch_hole(self, diameter: float):
        """Растяжение ниппельного отверстия для пенетрации"""
        self.hole_gape = max(self.hole_gape, diameter)
        if self.hole_gape > 0.3:
            self.can_penetration = True
            
    def insert_plug(self, plug: 'NipplePlug'):
        if self.hole_gape >= plug.diameter or not self.plug:
            self.plug = plug
            return True
        return False
        
    def remove_plug(self) -> Optional['NipplePlug']:
        plug = self.plug
        self.plug = None
        return plug

@dataclass
class NipplePlug:
    name: str
    diameter: float
    length: float
    material: str = "silicone"
    has_hole: bool = False  # Сквозное отверстие для сцеживания
    
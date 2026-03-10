from dataclasses import dataclass, field
from typing import List
from enum import Enum
from .nipple import Nipple

class AreolaTexture(Enum):
    SMOOTH = "smooth"
    BUMPY = "bumpy"
    PUFFY = "puffy"

@dataclass
class MontgomeryGland:
    size: float = 0.1
    active: bool = True
    secretion: float = 0.0

@dataclass
class Areola:
    diameter: float = 4.0
    base_diameter: float = field(init=False)  # Базовый размер для расчета инфляции
    color: str = "pink"
    texture: AreolaTexture = AreolaTexture.BUMPY
    puffiness: float = 0.0
    
    nipples: List[Nipple] = field(default_factory=list)
    montgomery_glands: List[MontgomeryGland] = field(default_factory=list)
    sensitivity: float = 0.8
    
    def __post_init__(self):
        self.base_diameter = self.diameter
        if not self.nipples:
            self.nipples = [Nipple(diameter=self.diameter * 0.25)]
        
        if not self.montgomery_glands:
            import random
            count = random.randint(10, 15)
            self.montgomery_glands = [MontgomeryGland() for _ in range(count)]
    
    def _update_diameter(self, stretch_ratio: float = 1.0):
        """Обновление диаметра при растяжении груди."""
        import math
        target = self.base_diameter * (stretch_ratio ** 0.5)
        self.diameter = target
    
    def add_nipple(self, nipple: Nipple):
        self.nipples.append(nipple)
    
    def stimulate(self, intensity: float = 1.0):
        for nipple in self.nipples:
            nipple.stimulate(intensity)
        
        if self.texture == AreolaTexture.BUMPY:
            for gland in self.montgomery_glands:
                if gland.active:
                    gland.secretion = min(0.1, gland.secretion + 0.01 * intensity)
    
    def relax(self):
        for nipple in self.nipples:
            nipple.relax()
    
    def get_total_gape(self) -> float:
        return sum(n.effective_gape for n in self.nipples)
    
    def get_state(self) -> dict:
        return {
            'diameter': self.diameter,
            'base_diameter': self.base_diameter,
            'color': self.color,
            'texture': self.texture.value,
            'nipple_count': len(self.nipples),
            'nipples': [n.get_state() for n in self.nipples]
        }

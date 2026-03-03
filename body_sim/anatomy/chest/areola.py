# anatomy/chest/areola.py
from dataclasses import dataclass, field
from typing import List
from enum import Enum

class AreolaTexture(Enum):
    SMOOTH = "smooth"
    BUMPY = "bumpy"  # Железы Монтгомери выражены
    PUFFY = "puffy"

@dataclass
class MontgomeryGland:
    """Железы Монтгомери на ареоле"""
    size: float = 0.1  # см
    active: bool = True  # Выделяют смазку при возбуждении
    secretion: float = 0.0  # мл смазки

@dataclass
class Areola:
    color: str = "pink"
    diameter: float = 4.0  # см
    texture: AreolaTexture = AreolaTexture.BUMPY
    puffiness: float = 0.0  # Отёчность (0-1)
    sensitivity: float = 0.8
    montgomery_glands: List[MontgomeryGland] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.montgomery_glands:
            # Создаём 10-15 желез по периметру
            import random
            count = random.randint(10, 15)
            self.montgomery_glands = [MontgomeryGland() for _ in range(count)]
    
    def stimulate(self):
        """При стимуляции железы выделяют смазку"""
        if self.texture == AreolaTexture.BUMPY:
            for gland in self.montgomery_glands:
                if gland.active:
                    gland.secretion = min(0.1, gland.secretion + 0.01)
                    
    def get_state(self) -> dict:
        return {
            "color": self.color,
            "diameter": f"{self.diameter}cm",
            "texture": self.texture.value,
            "glands_active": sum(1 for g in self.montgomery_glands if g.secretion > 0)
        }
        
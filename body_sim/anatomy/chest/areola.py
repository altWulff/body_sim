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
    """Железы Монтгомери."""
    size: float = 0.1  # см
    active: bool = True
    secretion: float = 0.0  # мл смазки

@dataclass
class Areola:
    """
    Ареола с поддержкой multiple nipples (из старого кода)
    и желез Монтгомери (из нового).
    """
    diameter: float = 4.0
    color: str = "pink"
    texture: AreolaTexture = AreolaTexture.BUMPY
    puffiness: float = 0.0
    
    # Поддержка множественных сосков (для некоторых рас)
    # По умолчанию 1 сосок, но может быть больше
    nipples: List[Nipple] = field(default_factory=list)
    
    # Железы Монтгомери
    montgomery_glands: List[MontgomeryGland] = field(default_factory=list)
    sensitivity: float = 0.8
    
    def __post_init__(self):
        if not self.nipples:
            # По умолчанию один сосок
            self.nipples = [Nipple(diameter=self.diameter * 0.25)]
        
        if not self.montgomery_glands:
            import random
            count = random.randint(10, 15)
            self.montgomery_glands = [MontgomeryGland() for _ in range(count)]
    
    def add_nipple(self, nipple: Nipple):
        """Добавить дополнительный сосок (для мутаций/рас)."""
        self.nipples.append(nipple)
    
    def stimulate(self, intensity: float = 1.0):
        """Стимуляция ареолы и всех сосков."""
        for nipple in self.nipples:
            nipple.stimulate(intensity)
        
        # Железы выделяют смазку
        if self.texture == AreolaTexture.BUMPY:
            for gland in self.montgomery_glands:
                if gland.active:
                    gland.secretion = min(0.1, gland.secretion + 0.01 * intensity)
    
    def relax(self):
        """Расслабление всех сосков."""
        for nipple in self.nipples:
            nipple.relax()
    
    def get_total_gape(self) -> float:
        """Суммарное отверстие всех сосков."""
        return sum(n.gape_diameter for n in self.nipples)
    
    def get_state(self) -> dict:
        return {
            'diameter': self.diameter,
            'color': self.color,
            'texture': self.texture.value,
            'nipple_count': len(self.nipples),
            'nipples': [n.get_state() for n in self.nipples]
        }

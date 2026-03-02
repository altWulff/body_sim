# appearance/core.py

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

from body_sim.core.components import BaseComponent


class Race(Enum):
    HUMAN = "human"
    MIGURD = "migurd"
    DRAGON = "dragon"
    WOLF = "wolf"
    ELF = "elf"
    DEMI_HUMAN = "demi_human"

@dataclass
class AppearanceConfig:
    race: Race
    height_cm: float
    weight_kg: float
    skin_tone: str
    eye_color: str
    eye_shape: str
    ear_type: str
    ear_length: float
    special_traits: List[str] = None
    
    def __post_init__(self):
        if self.special_traits is None:
            self.special_traits = []

class AppearanceComponent(BaseComponent):
    def __init__(self, config: AppearanceConfig):
        super().__init__("appearance")
        self.config = config
        self.part_modifiers: Dict[str, Dict] = {}  # Модификации частей тела
        
    def modify_part(self, part: str, changes: Dict):
        self.part_modifiers[part] = changes
        
    def get_description(self) -> str:
        base = f"{self.config.race.value}, {self.config.height_cm}cm, {self.config.skin_tone} skin"
        if self.config.special_traits:
            base += f", traits: {', '.join(self.config.special_traits)}"
        return base

# === appearance/core.py ===
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any

from body_sim.core.components import BaseComponent

class Race(Enum):
    HUMAN = "human"
    HIGH_ELF = "high_elf"
    DARK_ELF = "dark_elf"
    BEASTKIN = "beastkin"
    SUCCUBUS = "succubus"
    INCUBUS = "incubus"
    DEMON = "demon"
    DRAGON = "dragon"
    DRAGONKIN = "dragonkin"
    VAMPIRE = "vampire"
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
        self.part_modifiers: Dict[str, Dict] = {}
        
    def modify_part(self, part: str, changes: Dict):
        self.part_modifiers[part] = changes
        
    def get_description(self) -> str:
        base = f"{self.config.race.value}, {self.config.height_cm}cm, {self.config.skin_tone} skin"
        if self.config.special_traits:
            base += f", traits: {', '.join(self.config.special_traits)}"
        return base
        
    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update({
            'race': self.config.race.value,
            'height': self.config.height_cm,
            'weight': self.config.weight_kg,
            'skin': self.config.skin_tone,
            'eyes': f"{self.config.eye_color} {self.config.eye_shape}",
            'ears': f"{self.config.ear_type} ({self.config.ear_length}x)",
            'traits': self.config.special_traits,
            'part_modifiers': self.part_modifiers
        })
        return base
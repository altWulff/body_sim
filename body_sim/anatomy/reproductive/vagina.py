# === anatomy/reproductive/vagina.py ===
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import math

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus

@dataclass 
class VaginaType:
    type_name: str = "human"
    depth_factor: float = 1.0
    tightness: float = 1.0
    elasticity: float = 1.0
    max_stretch_ratio: float = 3.0
    has_cervical_pouch: bool = False
    extra_depth: bool = False
    has_ridges: bool = False
    ridge_count: int = 0
    has_tentacles: bool = False
    self_lubricating: bool = False
    glows: bool = False
    can_expand: bool = False
    photosensitive: bool = False
    is_slime: bool = False
    can_reform: bool = False

    @classmethod
    def HUMAN(cls):
        return cls("human", 1.0, 1.0, 1.0, 3.0)
        
    @classmethod
    def DRAGON(cls):
        return cls("dragon", 1.5, 0.8, 1.5, 4.0, extra_depth=True)

@dataclass
class Vagina(AnatomicalComponent):
    vagina_type: VaginaType = field(default_factory=VaginaType.HUMAN)
    base_depth: float = 10.0
    base_width: float = 3.0
    max_stretch_ratio: float = 3.0
    muscle_tone: float = 0.5
    is_aroused: bool = False
    lubrication: float = 0.0
    current_stretch: float = 1.0
    current_penetration_depth: float = 0.0
    
    def __post_init__(self):
        super().__init__("vagina", max_volume=200)
        self._apply_type_stats()
        self._recalculate_dimensions()
        
    def _apply_type_stats(self):
        stats = self.vagina_type
        self.max_stretch_ratio = stats.max_stretch_ratio
        self.current_stretch = stats.tightness
        self.base_depth *= stats.depth_factor
        
    def _recalculate_dimensions(self):
        r = self.current_width / 2
        self.volume = math.pi * r * r * self.current_depth
        
    @property
    def current_depth(self) -> float:
        arousal_bonus = 0.2 if self.is_aroused else 0.0
        return self.base_depth * (1 + (self.current_stretch - 1) * 0.3) * (1 + arousal_bonus)

    @property
    def current_width(self) -> float:
        arousal_bonus = 0.2 if self.is_aroused else 0.0
        return self.base_width * (self.current_stretch + arousal_bonus)

    @property
    def tightness(self) -> float:
        stretch_factor = 1.0 / self.current_stretch if self.current_stretch > 0 else 1.0
        return min(1.0, stretch_factor * self.muscle_tone)

    def stimulate(self, intensity: float = 0.1, source: str = None) -> None:
        super().stimulate(intensity, source)
        self.lubrication = min(1.0, self.lubrication + intensity * 0.5)
        if self.arousal > 0.5: 
            self.is_aroused = True
            self._recalculate_dimensions()

    def penetrate(self, penis: 'Penis') -> bool:
        if not penis.can_penetrated(self.current_width):
            required_stretch = penis.current_diameter / self.base_width
            if required_stretch > self.max_stretch_ratio: 
                return False
            self.current_stretch = required_stretch
            
        self.current_penetration_depth = min(penis.current_length, self.current_depth)
        self.stimulate(0.3)
        return True

    def withdraw(self) -> None:
        self.current_penetration_depth = 0.0
        self.current_stretch = max(1.0, self.current_stretch * 0.95)
        
    def stretch(self, amount: float):
        new_stretch = self.current_stretch * (1 + amount)
        if new_stretch <= self.max_stretch_ratio:
            self.current_stretch = new_stretch
            self._recalculate_dimensions()
    
    def recover(self, dt: float = 1.0):
        if self.current_stretch > 1.0:
            self.current_stretch = max(1.0, self.current_stretch - self.vagina_type.elasticity * 0.1 * dt)
            self._recalculate_dimensions()
    
    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        if self.arousal < 0.3: 
            self.is_aroused = False
        if not self.is_aroused:
            self.recover(delta_time)
        self.lubrication = max(0.0, self.lubrication - 0.1 * delta_time)
        
    def get_description(self) -> str:
        desc = f"{self.vagina_type.type_name} vagina"
        features = []
        if self.vagina_type.has_cervical_pouch: features.append("cervical pouch")
        if self.vagina_type.extra_depth: features.append("deep")
        if self.vagina_type.has_ridges: features.append(f"{self.vagina_type.ridge_count} ridges")
        if features: 
            desc += " (" + ", ".join(features) + ")"
        return desc
        
    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update({
            'type': self.vagina_type.type_name,
            'depth': self.current_depth,
            'width': self.current_width,
            'stretch': self.current_stretch,
            'lubrication': self.lubrication,
            'tightness': self.tightness,
            'penetration_depth': self.current_penetration_depth
        })
        return base
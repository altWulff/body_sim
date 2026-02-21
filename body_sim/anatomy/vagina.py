"""
Влагалище - женский половой орган.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Any, TYPE_CHECKING
import math

from body_sim.anatomy.base import Genital
from body_sim.core.enums import VaginaType, VaginaState
from body_sim.systems.penetration import PenetrableWithFluid

if TYPE_CHECKING:
    from .penis import Penis


@dataclass
class Vagina(Genital, PenetrableWithFluid):
    vagina_type: VaginaType = field(default=VaginaType.HUMAN)
    state: VaginaState = field(default=VaginaState.NORMAL)
    base_depth: float = 10.0
    base_width: float = 3.0
    max_stretch_ratio: float = 3.0
    elasticity: float = 1.0
    muscle_tone: float = 0.5
    is_aroused: bool = False
    lubrication: float = 0.0
    inserted_objects: List[Any] = field(default_factory=list)
    current_penetration: Optional[Penis] = None
    current_stretch: float = 1.0
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

    def __post_init__(self):
        Genital.__init__(self)
        PenetrableWithFluid.__init__(self)
        self._apply_type_stats()
        self._recalculate_dimensions()
        self.canal_length = self.base_depth
        self.rest_diameter = self.base_width
        self.max_stretch_ratio = getattr(self.vagina_type, 'max_stretch_ratio', 3.0)
    
    def _apply_type_stats(self):
        stats = self.vagina_type
        self.has_cervical_pouch = stats.has_cervical_pouch
        self.extra_depth = stats.extra_depth
        self.has_ridges = stats.has_ridges
        self.ridge_count = stats.ridge_count
        self.has_tentacles = stats.has_tentacles
        self.self_lubricating = stats.self_lubricating
        self.glows = stats.glows
        self.can_expand = stats.can_expand
        self.photosensitive = stats.photosensitive
        self.is_slime = stats.is_slime
        self.can_reform = stats.can_reform
        self.current_stretch = stats.tightness
        self.elasticity = stats.elasticity

    def _recalculate_dimensions(self):
        r = self.current_width / 2
        self.volume = math.pi * r * r * self.current_depth
        
    def get_landmarks(self):
        from body_sim.systems.advanced_penetration import DepthLandmark, PenetrationDepthZone
        return [
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_INTROITUS, depth_cm=0.0,
                min_diameter=1.0, max_diameter=6.0, resistance_factor=0.5,
                description="Вход во влагалище"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_CANAL,
                depth_cm=self.canal_length * 0.5, min_diameter=2.0,
                max_diameter=self.rest_diameter * self.max_stretch_ratio,
                resistance_factor=0.3, description="Влагалищный канал"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_FORNIX,
                depth_cm=self.canal_length * 0.95, min_diameter=2.5,
                max_diameter=8.0, resistance_factor=0.4,
                description="Своды (глубоко)", stimulation_bonus=0.8
            ),
        ]

    @property
    def current_depth(self) -> float:
        return self.base_depth * (1 + (self.current_stretch - 1) * 0.3) * self.vagina_type.depth_factor

    @property
    def current_width(self) -> float:
        arousal_bonus = 0.2 if self.is_aroused else 0.0
        if self.current_stretch > 0:
            return self.base_width * (self.current_stretch + arousal_bonus) * (1 / self.vagina_type.tightness)
        return self.base_width

    @property
    def tightness(self) -> float:
        stretch_factor = 1.0 / self.current_stretch
        return min(1.0, stretch_factor * self.muscle_tone)

    def stimulate(self, intensity: float = 0.1) -> None:
        super().stimulate(intensity)
        self.lubrication = min(1.0, self.lubrication + intensity * 0.5)
        if self.arousal > 0.5: self.is_aroused = True

    def penetrate(self, penis: Penis) -> bool:
        if not penis.can_penetrated(self.current_width):
            required_stretch = penis.current_diameter / self.base_width
            if required_stretch > self.max_stretch_ratio: return False
            self.current_stretch = required_stretch
        self.current_penetration = penis
        self.stimulate(0.3)
        return True

    def withdraw(self) -> None:
        self.current_penetration = None
        self.current_stretch = max(1.0, self.current_stretch * 0.95)

    def contract(self, amount: float = 0.1) -> None:
        self.muscle_tone = min(1.0, self.muscle_tone + amount)

    def relax(self, amount: float = 0.1) -> None:
        self.muscle_tone = max(0.0, self.muscle_tone - amount)

    def tick(self, dt: float) -> None:
        super().tick(dt)
        if self.arousal < 0.3: self.is_aroused = False
        if not self.current_penetration:
            self.current_stretch = max(1.0, self.current_stretch * 0.95)
        self.lubrication = max(0.0, self.lubrication - 0.1 * dt)

    def get_insertable_object(self) -> Any:
        from body_sim.systems.penetration import InsertableObject
        return InsertableObject(
            name="vagina", length=self.current_depth,
            diameter=self.current_width, rigidity=0.3, texture="mucosa"
        )

    def update_arousal(self, amount: float):
        self.arousal = max(0.0, min(1.0, self.arousal + amount))
        if self.arousal > 0.5:
            self.is_aroused = True
            self.state = VaginaState.AROUSED
            self.lubrication = min(1.0, self.lubrication + 0.1)
            self.current_width = self.base_width * (1.2 + self.arousal * 0.3)
            self._recalculate_dimensions()
        else:
            self.is_aroused = False
            self.state = VaginaState.NORMAL
    
    def stretch(self, amount: float):
        new_stretch = self.current_stretch * (1 + amount)
        if new_stretch <= self.max_stretch:
            self.current_stretch = new_stretch
            self.current_width *= (1 + amount)
            self._recalculate_dimensions()
    
    def recover(self):
        if self.current_stretch > 1.0:
            self.current_stretch = max(1.0, self.current_stretch - self.elasticity * 0.1)
            self._recalculate_dimensions()
    
    def get_description(self) -> str:
        desc = f"{self.vagina_type.type_name} влагалище"
        features = []
        if self.has_cervical_pouch: features.append("цервикальный мешок")
        if self.extra_depth: features.append("глубокое")
        if self.has_ridges: features.append(f"{self.ridge_count} гребней")
        if self.has_tentacles: features.append("щупальца")
        if self.self_lubricating: features.append("самосмазывающееся")
        if self.glows: features.append("светится")
        if self.can_expand: features.append("расширяемое")
        if self.is_slime: features.append("слизистое")
        if features: desc += " (" + ", ".join(features) + ")"
        return desc
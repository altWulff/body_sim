# === body/body.py ===
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum, auto

from body_sim.core.events import EventBus
from body_sim.core.components import BaseComponent
from body_sim.appearance.core import AppearanceComponent, Race, AppearanceConfig
from body_sim.anatomy.reproductive.system import ReproductiveSystem
from body_sim.anatomy.reproductive.vagina import Vagina, VaginaType
from body_sim.anatomy.reproductive.uterus import Uterus
from body_sim.anatomy.reproductive.clitoris import Clitoris
from body_sim.anatomy.reproductive.penis import Penis
from body_sim.anatomy.reproductive.scrotum import Scrotum
from body_sim.anatomy.digestive import DigestiveSystem
from body_sim.anatomy.breasts import Breasts, CupSize  # Используем существующий класс


class Sex(Enum):
    NONE = auto()
    MALE = auto()
    FEMALE = auto()
    FUTANARI = auto()


@dataclass
class Body:
    name: str = "Unnamed"
    sex: Sex = Sex.FEMALE
    race: Race = Race.HUMAN
    age: float = 25.0
    height: float = 170.0
    weight: float = 60.0
    
    event_bus: EventBus = field(default_factory=EventBus, repr=False)
    appearance: Optional[AppearanceComponent] = None
    digestive_system: Optional[DigestiveSystem] = None
    reproductive_system: Optional[ReproductiveSystem] = None
    breasts: Optional[Breasts] = None
    
    _listeners: Dict[str, List] = field(default_factory=dict, repr=False)
    
    def __post_init__(self):
        if self.appearance is None:
            config = AppearanceConfig(
                race=self.race,
                height_cm=self.height,
                weight_kg=self.weight,
                skin_tone="fair",
                eye_color="brown",
                eye_shape="almond",
                ear_type="human",
                ear_length=1.0
            )
            self.appearance = AppearanceComponent(config)
        
        self.digestive_system = DigestiveSystem()
        
        # Инициализация груди для женских тел
        if self.sex in (Sex.FEMALE, Sex.FUTANARI):
            cup_size = self._determine_breast_size()
            self.breasts = Breasts(cup_size)  # Используем существующий класс
        
        if self.reproductive_system is None:
            self._setup_reproductive()
    
    def _determine_breast_size(self) -> CupSize:
        """Определить размер груди на основе параметров тела."""
        race_cups = {
            Race.SUCCUBUS: CupSize.D,
            Race.DEMON: CupSize.D,
            Race.HIGH_ELF: CupSize.B,
            Race.DARK_ELF: CupSize.C,
            Race.HUMAN: CupSize.C,
            Race.BEASTKIN: CupSize.C,
        }
        
        base = race_cups.get(self.race, CupSize.C)
        
        # Корректировка от BMI
        bmi = self.weight / ((self.height/100) ** 2)
        if bmi > 30:
            sizes = list(CupSize)
            idx = min(len(sizes)-1, sizes.index(base) + 2)
            return sizes[idx]
        elif bmi < 18:
            sizes = list(CupSize)
            idx = max(0, sizes.index(base) - 1)
            return sizes[idx]
        
        return base
            
    def _setup_reproductive(self):
        self.reproductive_system = ReproductiveSystem()
        
        if self.sex == Sex.FEMALE or self.sex == Sex.FUTANARI:
            vagina = Vagina(vagina_type=VaginaType.HUMAN(), base_depth=12.0)
            self.reproductive_system.add_vagina(vagina)
            
            uterus = Uterus()
            self.reproductive_system.add_uterus(uterus)
            
            clitoris = Clitoris(base_length=1.5, can_transform=(self.race == Race.DEMON))
            self.reproductive_system.add_clitoris(clitoris)
            
        if self.sex == Sex.MALE or self.sex == Sex.FUTANARI:
            scrotum = Scrotum()
            self.reproductive_system.add_scrotum(scrotum)
            
            penis = Penis(base_length=16.0, base_girth=12.0, scrotum=scrotum)
            self.reproductive_system.add_penis(penis)
            
    def transform_clitoris_to_penis(self, clitoris_idx: int = 0, 
                                    target_length: float = 10.0,
                                    target_girth: float = 8.0) -> bool:
        if not self.reproductive_system or clitoris_idx >= len(self.reproductive_system.clitorises):
            return False
            
        clitoris = self.reproductive_system.clitorises[clitoris_idx]
        if not clitoris.can_transform:
            return False
            
        new_penis = clitoris.transform_to_penis(target_length, target_girth)
        
        if self.reproductive_system.scrotums:
            new_penis.scrotum = self.reproductive_system.scrotums[0]
            
        self.reproductive_system.add_penis(new_penis)
        return True
        
    def stimulate(self, region: str, index: int = 0, intensity: float = 0.1):
        if not self.reproductive_system:
            return
            
        if region == "clitoris" and index < len(self.reproductive_system.clitorises):
            self.reproductive_system.clitorises[index].stimulate(intensity)
        elif region == "penis" and index < len(self.reproductive_system.penises):
            self.reproductive_system.penises[index].stimulate(intensity)
        elif region == "vagina" and index < len(self.reproductive_system.vaginas):
            self.reproductive_system.vaginas[index].stimulate(intensity)
        elif region == "breast" and self.breasts:
            breast = self.breasts.left if index == 0 else self.breasts.right
            breast.stimulate(intensity)
            
    def ejaculate(self, penis_index: int = 0) -> Dict[str, Any]:
        if not self.reproductive_system or penis_index >= len(self.reproductive_system.penises):
            return {"success": False, "reason": "no_penis"}
            
        penis = self.reproductive_system.penises[penis_index]
        result = penis.ejaculate()
        return result
        
    def inflate_uterus(self, uterus_idx: int = 0, ratio: float = 2.0):
        if not self.reproductive_system or uterus_idx >= len(self.reproductive_system.uteri):
            return False
            
        uterus = self.reproductive_system.uteri[uterus_idx]
        return uterus.inflate(ratio)
        
    def stretch_uterus(self, uterus_idx: int = 0, ratio: float = 2.0):
        if not self.reproductive_system or uterus_idx >= len(self.reproductive_system.uteri):
            return False
            
        uterus = self.reproductive_system.uteri[uterus_idx]
        return uterus.stretch(ratio)
        
    def update(self, delta_time: float = 1.0):
        """Обновить все системы тела."""
        if self.digestive_system:
            self.digestive_system.update(delta_time, self.event_bus)
        if self.reproductive_system:
            self.reproductive_system.update(delta_time, self.event_bus)
        if self.breasts:
            self.breasts.update(delta_time, self.event_bus)
            
    def get_full_state(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'sex': self.sex.name,
            'race': self.race.value,
            'appearance': self.appearance.get_state() if self.appearance else None,
            'digestive': self.digestive_system.get_state() if self.digestive_system else None,
            'reproductive': self.reproductive_system.get_state() if self.reproductive_system else None,
            'breasts': self.breasts.get_state() if self.breasts else None
        }

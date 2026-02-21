"""
Пенис - мужской половой орган.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING
import math

from .base import Genital
from body_sim.core.enums import PenisType, PenisState, FluidType
from body_sim.systems.penetration import InsertableObject

if TYPE_CHECKING:
    from .scrotum import Scrotum


@dataclass
class Penis(Genital):
    base_length: float = 15.0
    base_girth: float = 12.0
    penis_type: PenisType = field(default=PenisType.HUMAN)
    state: PenisState = field(default=PenisState.FLACCID)
    erect_length_multiplier: float = 1.3
    erect_girth_multiplier: float = 1.2
    is_erect: bool = False
    urethra_diameter: float = 0.6
    urethra_expandable: bool = True
    foreskin: bool = True
    foreskin_retracted: bool = False
    knot_size: float = 0.0
    flare_width: float = 0.0
    is_transformed_clitoris: bool = False
    original_clitoris_size: float = 0.0
    scrotum: Optional[Scrotum] = field(default=None, repr=False)
    erection_factor: float = 1.3
    knot_girth: float = 0.0
    has_knot: bool = False
    knot_factor: float = 1.0
    has_barbs: bool = False
    barb_count: int = 0
    has_ridges: bool = False
    ridge_count: int = 0
    has_spines: bool = False
    is_prehensile: bool = False
    flare_factor: float = 1.0
    taper_ratio: float = 1.0
    count: int = 1
    is_horseshoe: bool = False
    has_spiral: bool = False
    spiral_turns: int = 0
    has_ribs: bool = False
    rib_count: int = 0
    is_split: bool = False
    split_depth: float = 0.0
    glows: bool = False
    is_knotted: bool = False
 
    def __post_init__(self):
        self._apply_type_stats()
        self._recalculate_dimensions()
    
    def _apply_type_stats(self):
        stats = self.penis_type
        self.has_knot = stats.has_knot
        self.knot_factor = stats.knot_factor
        self.has_barbs = stats.has_barbs
        self.barb_count = stats.barb_count
        self.has_ridges = stats.has_ridges
        self.ridge_count = stats.ridge_count
        self.has_spines = stats.has_spines
        self.is_prehensile = stats.is_prehensile
        self.flare_factor = stats.flare_factor
        self.taper_ratio = stats.taper_ratio
        self.count = stats.count
        self.is_horseshoe = stats.is_horseshoe
        self.has_spiral = stats.has_spiral
        self.spiral_turns = stats.spiral_turns
        self.has_ribs = stats.has_ribs
        self.rib_count = stats.rib_count
        self.is_split = stats.is_split
        self.split_depth = stats.split_depth
        self.glows = stats.glows
        
        if self.penis_type.id in ["equine", "flared"]:
            self.urethra_diameter = 0.9
        elif self.penis_type.id in ["canine", "knotted"]:
            self.urethra_diameter = 0.7
        elif self.penis_type.id in ["feline", "tapered"]:
            self.urethra_diameter = 0.4
    
    def _recalculate_dimensions(self):
        if self.has_knot:
            self.knot_girth = self.current_girth * self.knot_factor
        else:
            self.knot_girth = self.current_girth
        self.flare_girth = self.current_girth * self.flare_factor

    @property
    def current_urethra_diameter(self) -> float:
        base = self.urethra_diameter
        if self.is_erect and self.urethra_expandable:
            return base * (1.2 + self.arousal * 0.2)
        return base

    def getInsertableObject(self) -> InsertableObject:
        return InsertableObject(
            name=self.name or "penis",
            length=self.current_length,
            diameter=self.current_diameter,
            rigidity=0.9 if self.is_erect else 0.4,
            texture="skin",
            inserted_depth=0.0
        )
    
    def get_available_fluids(self) -> Dict[FluidType, float]:
        if self.scrotum:
            return self.scrotum.total_stored_fluids
        return {}
    
    def get_available_volume(self, fluid_type: FluidType = FluidType.CUM) -> float:
        return self.get_available_fluids().get(fluid_type, 0.0)
    
    def has_scrotum(self) -> bool:
        return self.scrotum is not None
    
    def _get_ejaculate_multiplier(self) -> float:
        mult = 1.0
        type_multipliers = {
            "human": 1.0, "equine": 1.5, "canine": 1.3, "knotted": 1.4,
            "flared": 1.2, "tentacle": 0.8, "demon": 1.3, "dragon": 1.2,
            "feline": 0.9, "tapered": 0.85, "double": 0.7,
        }
        type_id = self.penis_type.id
        mult *= type_multipliers.get(type_id, 1.0)
        
        if self.has_knot: mult *= 1.2
        if self.flare_factor > 1.3: mult *= 1.15
        if self.has_ribs or self.has_ridges: mult *= 0.95
        if self.taper_ratio < 0.8: mult *= 0.9
        if self.has_spiral: mult *= 0.85
        if self.is_split: mult *= 0.8
            
        return mult
    
    def calculate_max_ejaculate_volume(self, force: float = 1.0) -> float:
        d_cm = self.current_urethra_diameter / 10.0
        area = math.pi * (d_cm / 2) ** 2
        type_mult = self._get_ejaculate_multiplier()
        pressure_mult = self.scrotum.pressure_multiplier if self.scrotum else 1.0
        
        base_length = 2.0 + force * 3.0
        pressure_boost = (pressure_mult - 1.0) * 2.0
        ejaculate_length = base_length + pressure_boost
        
        max_volume = area * ejaculate_length * force * type_mult * pressure_mult * 500
        return max(1.0, max_volume)
    
    def produce_cum_for_encounter(self, arousal_boost: float = 1.0) -> float:
        """Проверка доступности спермы."""
        return self.get_available_volume()
    
    def ejaculate(self, amount: Optional[float] = None, 
                  fluid_type: FluidType = FluidType.CUM,
                  force: float = 1.0) -> Dict[str, Any]:
        if not self.scrotum:
            return {"amount": 0.0, "pulses": 0, "reason": "no_scrotum"}
        
        available = self.get_available_volume(fluid_type)
        if available <= 0:
            return {"amount": 0.0, "pulses": 0, "reason": "empty"}
        
        pressure_mult = self.scrotum.pressure_multiplier
        max_per_pulse = self.calculate_max_ejaculate_volume(force)
        
        if amount is None:
            base_ratio = 0.3 + force * 0.5
            pressure_bonus = min((pressure_mult - 1.0) * 0.3, 0.4)
            desired_amount = available * (base_ratio + pressure_bonus)
        else:
            desired_amount = amount
        
        desired_amount = min(desired_amount, available)
        
        total_ejaculated = 0.0
        pulses = 0
        remaining = desired_amount
        
        while remaining > 0.1 and pulses < 5:
            pulse_amount = min(remaining, max_per_pulse)
            actual = self.scrotum.drain_fluid(fluid_type, pulse_amount)
            if actual <= 0: break
            total_ejaculated += actual
            remaining -= actual
            pulses += 1
        
        return {
            "amount": total_ejaculated,
            "pulses": pulses,
            "max_per_pulse": max_per_pulse,
            "total_requested": desired_amount,
            "remaining_in_testicles": self.get_available_volume(fluid_type),
            "pressure_mult": pressure_mult,
            "pressure_tier": self.scrotum.pressure_tier if self.scrotum else "none",
            "zone": "VAGINA_DEEP",
            "depth": getattr(self, 'inserted_depth', 0.0),
            "volume": total_ejaculated,
            "target": "vagina"
        }
    
    def ejaculate_all(self, force: float = 1.0) -> Dict[str, Any]:
        available = self.get_available_volume()
        return self.ejaculate(amount=available, force=force)

    @property
    def current_length(self) -> float:
        return self.base_length * (self.erect_length_multiplier if self.is_erect else 1.0) * self.penis_type.length_factor

    @property
    def current_girth(self) -> float:
        return self.base_girth * (self.erect_girth_multiplier if self.is_erect else 1.0) * self.penis_type.girth_factor

    @property
    def current_diameter(self) -> float:
        return self.current_girth / math.pi

    @property
    def volume(self) -> float:
        r = self.current_girth / (2 * math.pi)
        length = self.current_length
        volume = math.pi * r ** 2 * length * 0.8
        flare_r = (self.flare_girth / math.pi) / 2
        volume += (1/3) * math.pi * flare_r * flare_r * (length * 0.2)
        if self.has_knot:
            knot_r = (self.knot_girth / math.pi) / 2
            volume += (4/3) * math.pi * knot_r * knot_r * knot_r * 0.3
        return volume

    def stimulate(self, intensity: float = 0.1) -> None:
        super().stimulate(intensity)
        if self.arousal > 0.7 and not self.is_erect:
            self.erect()

    def erect(self) -> None:
        self.is_erect = True
        if self.foreskin:
            self.foreskin_retracted = True

    def flaccid(self) -> None:
        self.is_erect = False
        self.arousal = 0.0
        if self.foreskin:
            self.foreskin_retracted = False

    def can_penetrated(self, orifice_diameter: float) -> bool:
        return self.current_diameter <= orifice_diameter * 1.2

    def update_arousal(self, amount: float):
        self.arousal = max(0.0, min(1.0, self.arousal + amount))
        self._update_erection()
        
    def _update_erection(self):
        if self.arousal > 0.6:
            self.is_erect = True
            self.state = PenisState.ERECT
        elif self.arousal > 0.3:
            self.is_erect = False
            self.state = PenisState.SEMI_ERECT
        else:
            self.is_erect = False
            self.state = PenisState.FLACCID
            self._recalculate_dimensions()
    
    def get_description(self) -> str:
        desc = f"{self.penis_type.type_name} пенис"
        features = []
        if self.has_knot: features.append(f"узел ×{self.knot_factor:.1f}")
        if self.has_barbs: features.append(f"{self.barb_count} шипов")
        if self.has_ridges: features.append(f"{self.ridge_count} гребней")
        if self.has_spines: features.append("шипы")
        if self.is_prehensile: features.append("хватательный")
        if self.has_ribs: features.append(f"{self.rib_count} рёбер")
        if self.has_spiral: features.append(f"спираль {self.spiral_turns} витков")
        if self.is_split: features.append(f"раздвоенный на {self.split_depth:.0%}")
        if self.glows: features.append("светится")
        
        if self.has_scrotum():
            cum_amount = self.get_available_volume()
            urethra = self.current_urethra_diameter
            features.append(f"уретра {urethra:.1f}мм")
            features.append(f"спермы: {cum_amount:.1f}мл")
        
        if features:
            desc += " (" + ", ".join(features) + ")"
        return desc

    def transform_type(self, new_type: PenisType) -> Dict[str, Any]:
        old_type = self.penis_type
        old_length = self.current_length
        old_girth = self.current_girth
        
        self.penis_type = new_type
        self._apply_type_stats()
        self._recalculate_dimensions()
        
        if new_type.id in ["equine", "flared"]: self.urethra_diameter = 0.9
        elif new_type.id in ["canine", "knotted"]: self.urethra_diameter = 0.7
        elif new_type.id in ["feline", "tapered"]: self.urethra_diameter = 0.4
        else: self.urethra_diameter = 0.6
        
        if self.is_erect:
            self._update_erection()
        
        features = []
        if self.has_knot: features.append(f"Knot ×{self.knot_factor:.1f}")
        if self.has_barbs: features.append(f"Barbs ({self.barb_count})")
        if self.has_ridges: features.append(f"Ridges ({self.ridge_count})")
        if self.has_spines: features.append("Spines")
        if self.is_prehensile: features.append("Prehensile")
        if self.has_ribs: features.append(f"Ribs ({self.rib_count})")
        if self.has_spiral: features.append(f"Spiral ({self.spiral_turns} turns)")
        if self.is_split: features.append(f"Split {self.split_depth:.0%}")
        if self.glows: features.append("Glowing")
        
        return {
            "old_type": old_type, "new_type": new_type,
            "old_length": old_length, "new_length": self.current_length,
            "old_girth": old_girth, "new_girth": self.current_girth,
            "length_ratio": self.current_length / old_length if old_length > 0 else 1.0,
            "girth_ratio": self.current_girth / old_girth if old_girth > 0 else 1.0,
            "size_changed": abs(self.current_length - old_length) > 0.1,
            "new_features": features,
            "ejaculate_mult": self._get_ejaculate_multiplier(),
            "urethra_diameter": self.urethra_diameter,
            "success": True
        }
    
    @staticmethod
    def get_available_types() -> List[Tuple[str, str, str]]:
        return [
            ("human", "Обычный", "white"), ("knotted", "Узловатый", "red"),
            ("tapered", "Заостренный", "purple"), ("flared", "Расширенный", "magenta"),
            ("barbed", "Шипастый", "dark_red"), ("double", "Двойной", "cyan"),
            ("prehensile", "Хватательный", "green"), ("equine", "Конский", "black"),
            ("canine", "Собачий", "red"), ("feline", "Кошачий", "pink"),
            ("dragon", "Драконий", "purple"), ("demon", "Демонический", "red"),
            ("tentacle", "Щупальцевый", "green"), ("horseshoe", "Подковообразный", "pink"),
            ("spiral", "Спиральный", "blue"), ("ribbed", "Ребристый", "orange"),
            ("bifurcated", "Раздвоенный", "pink"),
        ]
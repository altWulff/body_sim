# body_sim/anatomy/genitals.py
"""
Гениталии - пенис, влагалище, клитор, анус, яички.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import math

from body_sim.anatomy.base import Genital
from body_sim.core.enums import (
    AnusType,
    PenisType, 
    PenisState,
    TesticleSize,
    VaginaType, 
    VaginaState,
    ScrotumType,
    OvaryType,
    FluidType
)
from body_sim.systems.penetration import PenetrableOrgan, InsertableObject, PenetrableWithFluid


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
    foreskin: bool = True
    foreskin_retracted: bool = False
    knot_size: float = 0.0
    flare_width: float = 0.0
    is_transformed_clitoris: bool = False
    original_clitoris_size: float = 0.0
    
    # НОВОЕ: Ссылка на мошонку (хранилище спермы)
    scrotum: Optional['Scrotum'] = field(default=None, repr=False)
    
    # УБРАНО: cum_reservoir, current_cum_volume - сперма только в яичках!
    
    # Эрекция
    erection_factor: float = 1.3
    # Убран дубликат is_erect!
    
    # УБРАНО: cum_regen_rate - регенерация только в яичках
    
    knot_girth: float = 0.0
    
    # Особые характеристики типа
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
        """Применяем характеристики типа."""
        self._apply_type_stats()
        self._recalculate_dimensions()
        # УБРАН расчет резервуара спермы - он теперь только в Scrotum/Testicle
    
    def _apply_type_stats(self):
        """Применить характеристики типа пениса."""
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
    
    def _recalculate_dimensions(self):
        """Пересчитать размеры с учётом типа."""
        if self.has_knot:
            self.knot_girth = self.current_girth * self.knot_factor
        else:
            self.knot_girth = self.current_girth
        
        self.flare_girth = self.current_girth * self.flare_factor

    def getInsertableObject(self) -> InsertableObject:
        """Преобразовать в InsertableObject для пенетрации"""
        return InsertableObject(
            name=self.name or "penis",
            length=self.current_length,
            diameter=self.current_diameter,
            rigidity=0.9 if self.is_erect else 0.4,
            texture="skin",
            inserted_depth=0.0
        )
    
    # НОВЫЕ МЕТОДЫ для работы со спермой из яичек:
    
    def get_available_fluids(self) -> Dict[FluidType, float]:
        """Получить доступные жидкости из яичек (пенис - только трубка)."""
        if self.scrotum:
            return self.scrotum.total_stored_fluids
        return {}
    
    def get_available_volume(self, fluid_type: FluidType = FluidType.CUM) -> float:
        """Сколько спермы/жидкости доступно в яичках."""
        return self.get_available_fluids().get(fluid_type, 0.0)
    
    def has_scrotum(self) -> bool:
        """Подключены ли яички."""
        return self.scrotum is not None
    
    def produce_cum_for_encounter(self, arousal_boost: float = 1.0) -> float:
        """
        Забирает сперму из яичек для эякуляции.
        Вызывается при оргазме. Возвращает объем забранной спермы.
        """
        if not self.scrotum:
            return 0.0
            
        # Забираем пропорционально возбуждению (но не больше чем есть)
        available = self.get_available_volume(FluidType.CUM)
        amount = available * min(1.0, 0.5 + arousal_boost * 0.5)
        
        return self.scrotum.drain_fluid(FluidType.CUM, amount)
    
    def ejaculate(self, amount: Optional[float] = None, 
                  fluid_type: FluidType = FluidType.CUM,
                  force: float = 1.0) -> float:
        """
        Эякуляция. Пенис забирает жидкость из яичек и "доставляет" её.
        Без яичек эякуляция невозможна (возвращает 0).
        """
        if not self.scrotum:
            return 0.0
            
        available = self.get_available_volume(fluid_type)
        
        if amount is None:
            # По умолчанию забираем всё или пропорционально силе оргазма
            amount = available * force
        
        # Забираем из яичек через мошонку
        actual = self.scrotum.drain_fluid(fluid_type, amount)
        return actual
    
    def ejaculate_all(self, ratio: float = 1.0) -> Dict[FluidType, float]:
        """Полная эякуляция всех доступных жидкостей из яичек."""
        if not self.scrotum:
            return {}
        return self.scrotum.drain_all(ratio)
    
    # УБРАНЫ старые методы (не нужны, т.к. сперма не хранится в пенисе):
    # - produce_cum() 
    # - regenerate_cum()
    # - старое свойство volume (которое было для спермы)
    
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
        """Объем самого пениса (ткани), не спермы!"""
        r = self.current_girth / (2 * math.pi)
        length = self.current_length
        
        # Объем ткани пениса
        volume = math.pi * r ** 2 * length * 0.8
        
        # Добавляем объем головки
        flare_r = (self.flare_girth / math.pi) / 2
        volume += (1/3) * math.pi * flare_r * flare_r * (length * 0.2)
        
        # Добавляем объем узла
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
        """Обновить уровень возбуждения."""
        self.arousal = max(0.0, min(1.0, self.arousal + amount))
        self._update_erection()
    
    def _update_erection(self):
        """Обновить состояние эрекции."""
        if self.arousal > 0.6:
            self.is_erect = True
            self.state = PenisState.ERECT
            self.current_length = self.base_length * self.penis_type.length_factor * self.erection_factor
            self.current_girth = self.base_girth * self.penis_type.girth_factor * (1 + (self.arousal - 0.6) * 0.3)
        elif self.arousal > 0.3:
            self.is_erect = False
            self.state = PenisState.SEMI_ERECT
            self.current_length = self.base_length * self.penis_type.length_factor * (1 + self.arousal * 0.3)
        else:
            self.is_erect = False
            self.state = PenisState.FLACCID
            self._recalculate_dimensions()
        
        self.current_diameter = self.current_girth / math.pi
    
    def get_description(self) -> str:
        """Получить описание пениса."""
        desc = f"{self.penis_type.type_name} пенис"
        
        features = []
        if self.has_knot:
            features.append(f"узел ×{self.knot_factor:.1f}")
        if self.has_barbs:
            features.append(f"{self.barb_count} шипов")
        if self.has_ridges:
            features.append(f"{self.ridge_count} гребней")
        if self.has_spines:
            features.append("шипы")
        if self.is_prehensile:
            features.append("хватательный")
        if self.has_ribs:
            features.append(f"{self.rib_count} рёбер")
        if self.has_spiral:
            features.append(f"спираль {self.spiral_turns} витков")
        if self.is_split:
            features.append(f"раздвоенный на {self.split_depth:.0%}")
        if self.glows:
            features.append("светится")
        
        # Добавляем инфо о сперме из яичек
        if self.has_scrotum():
            cum_amount = self.get_available_volume(FluidType.CUM)
            features.append(f"спермы: {cum_amount:.1f}мл")
        
        if features:
            desc += " (" + ", ".join(features) + ")"
        
        return desc


@dataclass
class Clitoris(Genital):
    base_length: float = 1.5
    base_diameter: float = 0.5
    is_enlarged: bool = False
    enlargement_ratio: float = 1.0
    is_erect: bool = False
    erection_multiplier: float = 2.0
    can_transform: bool = True
    is_transformed: bool = False
    transformed_penis: Optional[Penis] = None

    @property
    def current_length(self) -> float:
        if self.is_transformed and self.transformed_penis:
            return self.transformed_penis.current_length
        
        length = self.base_length
        if self.is_enlarged:
            length *= self.enlargement_ratio
        if self.is_erect:
            length *= self.erection_multiplier
        return length

    def stimulate(self, intensity: float = 0.1) -> None:
        super().stimulate(intensity)
        if intensity > 0.3:
            self.is_erect = True

    def transform_to_penis(self, target_length: float = 10.0, target_girth: float = 8.0) -> Penis:
        if self.is_transformed:
            return self.transformed_penis
        
        self.is_transformed = True
        self.transformed_penis = Penis(
            name=f"transformed_from_{self.name}",
            base_length=target_length,
            base_girth=target_girth,
            is_transformed_clitoris=True,
            original_clitoris_size=self.base_length,
            sensitivity=self.sensitivity * 1.5
        )
        return self.transformed_penis

    def revert_to_clitoris(self) -> None:
        self.is_transformed = False
        self.transformed_penis = None
        self.is_enlarged = False
        self.enlargement_ratio = 1.0


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
    # Особые характеристики
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
        """Применяем характеристики типа."""
        Genital.__init__(self)
        PenetrableWithFluid.__init__(self)
        self._apply_type_stats()
        self._recalculate_dimensions()
        # Синхронизация параметров PenetrableOrgan с Vagina
        self.canal_length = self.base_depth
        self.rest_diameter = self.base_width
        self.max_stretch_ratio = getattr(self.vagina_type, 'max_stretch_ratio', 3.0)
    
    def _apply_type_stats(self):
        """Применить характеристики типа влагалища."""
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
        
        # Применяем модификаторы
        self.current_stretch = stats.tightness
        self.elasticity = stats.elasticity

    def _recalculate_dimensions(self):
        """Пересчитать размеры."""
        # Объём приблизительно
        r = self.current_width / 2
        self.volume = math.pi * r * r * self.current_depth
        
    def get_landmarks(self):
        """Возвращает анатомические отметки для глубокого проникновения."""
        from body_sim.systems.advanced_penetration import DepthLandmark, PenetrationDepthZone
        
        landmarks = [
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_INTROITUS,
                depth_cm=0.0,
                min_diameter=1.0,
                max_diameter=6.0,
                resistance_factor=0.5,
                description="Вход во влагалище"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_CANAL,
                depth_cm=self.canal_length * 0.5,
                min_diameter=2.0,
                max_diameter=self.rest_diameter * self.max_stretch_ratio,
                resistance_factor=0.3,
                description="Влагалищный канал"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_FORNIX,
                depth_cm=self.canal_length * 0.95,
                min_diameter=2.5,
                max_diameter=8.0,
                resistance_factor=0.4,
                description="Своды (глубоко)",
                stimulation_bonus=0.8
            ),
        ]
        
        # Если есть матка - добавляем путь к ней
        # Это будет дополнено AdvancedPenetrationEncounter
        return landmarks

    @property
    def current_depth(self) -> float:
        return self.base_depth * (1 + (self.current_stretch - 1) * 0.3) * self.vagina_type.depth_factor

    @property
    def current_width(self) -> float:
        arousal_bonus = 0.2 if self.is_aroused else 0.0
        return self.base_width * (self.current_stretch + arousal_bonus) * (1 / self.vagina_type.tightness) if self.current_stretch > 0 else self.base_width

    @property
    def tightness(self) -> float:
        stretch_factor = 1.0 / self.current_stretch
        return min(1.0, stretch_factor * self.muscle_tone)

    def stimulate(self, intensity: float = 0.1) -> None:
        super().stimulate(intensity)
        self.lubrication = min(1.0, self.lubrication + intensity * 0.5)
        if self.arousal > 0.5:
            self.is_aroused = True

    def penetrate(self, penis: Penis) -> bool:
        if not penis.can_penetrated(self.current_width):
            required_stretch = penis.current_diameter / self.base_width
            if required_stretch > self.max_stretch_ratio:
                return False
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
        if self.arousal < 0.3:
            self.is_aroused = False
        if not self.current_penetration:
            self.current_stretch = max(1.0, self.current_stretch * 0.95)
        self.lubrication = max(0.0, self.lubrication - 0.1 * dt)

    def get_insertable_object(self) -> InsertableObject:
        """Для совместимости если vagina используется как active"""
        return InsertableObject(
            name="vagina",
            length=self.current_depth,
            diameter=self.current_width,
            rigidity=0.3,
            texture="mucosa"
        )

    def update_arousal(self, amount: float):
        """Обновить возбуждение."""
        self.arousal = max(0.0, min(1.0, self.arousal + amount))
        
        if self.arousal > 0.5:
            self.is_aroused = True
            self.state = VaginaState.AROUSED
            self.lubrication = min(1.0, self.lubrication + 0.1)
            
            # При возбуждении влагалище расширяется
            self.current_width = self.base_width * (1.2 + self.arousal * 0.3)
            self._recalculate_dimensions()
        else:
            self.is_aroused = False
            self.state = VaginaState.NORMAL
    
    def stretch(self, amount: float):
        """Растянуть влагалище."""
        new_stretch = self.current_stretch * (1 + amount)
        if new_stretch <= self.max_stretch:
            self.current_stretch = new_stretch
            self.current_width *= (1 + amount)
            self._recalculate_dimensions()
    
    def recover(self):
        """Восстановление эластичности."""
        if self.current_stretch > 1.0:
            self.current_stretch = max(1.0, self.current_stretch - self.elasticity * 0.1)
            self._recalculate_dimensions()
    
    def get_description(self) -> str:
        """Получить описание влагалища."""
        desc = f"{self.vagina_type.type_name} влагалище"
        
        features = []
        if self.has_cervical_pouch:
            features.append("цервикальный мешок")
        if self.extra_depth:
            features.append("глубокое")
        if self.has_ridges:
            features.append(f"{self.ridge_count} гребней")
        if self.has_tentacles:
            features.append("щупальца")
        if self.self_lubricating:
            features.append("самосмазывающееся")
        if self.glows:
            features.append("светится")
        if self.can_expand:
            features.append("расширяемое")
        if self.is_slime:
            features.append("слизистое")
        
        if features:
            desc += " (" + ", ".join(features) + ")"
        
        return desc



@dataclass
class Anus(Genital):
    anus_type: AnusType = AnusType.AVERAGE
    base_diameter: float = 2.5
    max_diameter: float = 6.0
    sphincter_tone: float = 0.7
    is_gaping: bool = False
    gaping_size: float = 0.0
    inserted_object: Optional[Any] = None

    @property
    def current_diameter(self) -> float:
        if self.is_gaping:
            return self.gaping_size
        return self.base_diameter * (1 - self.sphincter_tone * 0.5)

    @property
    def can_hold(self) -> bool:
        return self.sphincter_tone > 0.3 and not self.is_gaping

    def relax(self, amount: float = 0.1) -> None:
        self.sphincter_tone = max(0.0, self.sphincter_tone - amount)

    def contract(self, amount: float = 0.1) -> None:
        self.sphincter_tone = min(1.0, self.sphincter_tone + amount)

    def stretch(self, diameter: float) -> bool:
        if diameter > self.max_diameter:
            return False
        self.is_gaping = True
        self.gaping_size = diameter
        return True

    def close(self) -> None:
        self.is_gaping = False
        self.gaping_size = 0.0

    def tick(self, dt: float) -> None:
        super().tick(dt)
        if not self.inserted_object and not self.is_gaping:
            self.sphincter_tone = min(0.7, self.sphincter_tone + 0.02 * dt)


@dataclass
class Testicle:
    name: str = "testicle"
    size: TesticleSize = TesticleSize.AVERAGE
    length: float = field(init=False)
    width: float = field(init=False)
    volume: float = field(init=False)
    fluid_production_rates: Dict[FluidType, float] = field(default_factory=dict)
    storage_capacity: float = field(init=False)
    stored_fluids: Dict[FluidType, float] = field(default_factory=dict)
    temperature: float = 34.0
    is_overheated: bool = False
    is_damaged: bool = False
    damage_level: float = 0.0
    sperm_count: float = 100.0  # миллионы
    sensitivity: float = 1.0

    def __post_init__(self):
        self.length = self.size.length
        self.width = self.length * 0.7
        self.volume = self.size.volume
        self.storage_capacity = self.volume * 2.0
        
        if not self.fluid_production_rates:
            self.fluid_production_rates = {FluidType.CUM: 0.3}
        
        for fluid_type in self.fluid_production_rates:
            self.stored_fluids[fluid_type] = 0.0

    @property
    def total_stored(self) -> float:
        return sum(self.stored_fluids.values())

    @property
    def fullness(self) -> float:
        return self.total_stored / self.storage_capacity if self.storage_capacity > 0 else 0

    @property
    def can_produce(self) -> bool:
        return not self.is_overheated and self.damage_level < 0.8

    def produce(self, dt: float, arousal: float = 0.0, stimulation: float = 1.0) -> Dict[FluidType, float]:
        produced = {}
        if not self.can_produce:
            return produced
        
        arousal_boost = 1.0 + (arousal * 2.0)
        temp_penalty = 0.5 if self.is_overheated else 1.0
        damage_penalty = 1.0 - (self.damage_level * 0.5)

        for fluid_type, base_rate in self.fluid_production_rates.items():
            effective_rate = base_rate * arousal_boost * stimulation * temp_penalty * damage_penalty
            amount = effective_rate * dt
            available_space = self.storage_capacity - self.total_stored
            amount = min(amount, available_space * 0.9)
            
            self.stored_fluids[fluid_type] = self.stored_fluids.get(fluid_type, 0) + amount
            produced[fluid_type] = amount
        
        return produced

    def drain(self, fluid_type: FluidType, amount: float) -> float:
        available = self.stored_fluids.get(fluid_type, 0)
        taken = min(amount, available)
        self.stored_fluids[fluid_type] = available - taken
        return taken

    def drain_all(self, ratio: float = 1.0) -> Dict[FluidType, float]:
        taken = {}
        for fluid_type, amount in self.stored_fluids.items():
            take_amount = amount * ratio
            self.stored_fluids[fluid_type] = amount - take_amount
            taken[fluid_type] = take_amount
        return taken

    def add_fluid_production(self, fluid_type: FluidType, rate: float) -> None:
        self.fluid_production_rates[fluid_type] = rate
        if fluid_type not in self.stored_fluids:
            self.stored_fluids[fluid_type] = 0.0

    def overheat(self, amount: float = 0.1) -> None:
        self.temperature += amount
        if self.temperature > 37.5:
            self.is_overheated = True

    def cool_down(self, amount: float = 0.2) -> None:
        self.temperature = max(34.0, self.temperature - amount)
        if self.temperature < 36.5:
            self.is_overheated = False

    def damage(self, amount: float) -> None:
        self.damage_level = min(1.0, self.damage_level + amount)
        self.is_damaged = self.damage_level > 0.1

    def heal(self, amount: float) -> None:
        self.damage_level = max(0.0, self.damage_level - amount)
        self.is_damaged = self.damage_level > 0.1

    def tick(self, dt: float, arousal: float = 0.0) -> None:
        if self.temperature > 34.5:
            self.temperature -= 0.05 * dt
        self.produce(dt, arousal)


@dataclass
class Scrotum:
    scrotum_type: ScrotumType = field(default=ScrotumType.STANDARD)
    has_testicles: bool = True
    testicle_size: TesticleSize = TesticleSize.AVERAGE
    testicle_count: int = 2
    testicles: List[Testicle] = field(default_factory=list)
    is_retracted: bool = False
    scrotum_volume: float = field(init=False)
    retracts: bool = False
    swings: bool = False
    has_sheath: bool = False
    is_internal: bool = False
    has_segments: bool = False
    segment_count: int = 1

    def __post_init__(self):
        stats = self.scrotum_type
        self.retracts = stats.retracts
        self.swings = stats.swings
        self.has_sheath = stats.has_sheath
        self.is_internal = stats.is_internal
        self.has_segments = stats.has_segments
        self.segment_count = stats.segment_count
        if self.has_testicles:
            for i in range(self.testicle_count):
                self.testicles.append(Testicle(
                    name=f"testicle_{i}",
                    size=self.testicle_size
                ))
        
        if self.testicles:
            self.scrotum_volume = sum(t.volume for t in self.testicles) * 1.5
        else:
            self.scrotum_volume = 50.0

    @property
    def total_storage_capacity(self) -> float:
        return sum(t.storage_capacity for t in self.testicles) * self.scrotum_type.capacity

    @property
    def total_stored_fluids(self) -> Dict[FluidType, float]:
        totals = {}
        for testicle in self.testicles:
            for fluid_type, amount in testicle.stored_fluids.items():
                totals[fluid_type] = totals.get(fluid_type, 0) + amount
        return totals

    @property
    def total_stored_volume(self) -> float:
        return sum(self.total_stored_fluids.values())

    @property
    def fullness(self) -> float:
        if self.total_storage_capacity <= 0:
            return 0
        return self.total_stored_volume / self.total_storage_capacity

    def get_testicle(self, index: int) -> Optional[Testicle]:
        if 0 <= index < len(self.testicles):
            return self.testicles[index]
        return None

    def drain_fluid(self, fluid_type: FluidType, amount: float) -> float:
        total_available = sum(t.stored_fluids.get(fluid_type, 0) for t in self.testicles)
        if total_available <= 0:
            return 0
        
        taken_total = 0
        ratio = amount / total_available
        
        for testicle in self.testicles:
            available = testicle.stored_fluids.get(fluid_type, 0)
            take = available * ratio
            testicle.stored_fluids[fluid_type] = available - take
            taken_total += take
        
        return taken_total

    def add_testicle_fluid_production(self, testicle_idx: int, fluid_type: FluidType, rate: float) -> None:
        testicle = self.get_testicle(testicle_idx)
        if testicle:
            testicle.add_fluid_production(fluid_type, rate)

    def overheat_testicle(self, index: int, amount: float = 0.1) -> None:
        testicle = self.get_testicle(index)
        if testicle:
            testicle.overheat(amount)

    def damage_testicle(self, index: int, amount: float) -> None:
        testicle = self.get_testicle(index)
        if testicle:
            testicle.damage(amount)

    def heal_testicle(self, index: int, amount: float) -> None:
        testicle = self.get_testicle(index)
        if testicle:
            testicle.heal(amount)

    def tick(self, dt: float, arousal: float = 0.0) -> None:
        for testicle in self.testicles:
            testicle.tick(dt, arousal)
        self.is_retracted = arousal > 0.95



def create_penis(penis_type: PenisType = PenisType.HUMAN, 
                 base_length: Optional[float] = None,
                 base_girth: Optional[float] = None) -> Penis:
    """Создать пенис заданного типа."""
    length = base_length if base_length else 15.0
    girth = base_girth if base_girth else 12.0
    
    return Penis(
        base_length=length,
        base_girth=girth,
        penis_type=penis_type
    )


def create_vagina(vagina_type: VaginaType = VaginaType.HUMAN,
                  base_depth: Optional[float] = None) -> Vagina:
    """Создать влагалище заданного типа."""
    depth = base_depth if base_depth else 10.0
    
    return Vagina(
        base_depth=depth,
        vagina_type=vagina_type
    )


def create_scrotum(scrotum_type: ScrotumType = ScrotumType.STANDARD,
                   testicle_count: int = 2) -> Scrotum:
    """Создать мошонку заданного типа."""
    testicles = [Testicle() for _ in range(testicle_count)]
    
    return Scrotum(
        scrotum_type=scrotum_type,
        testicles=testicles
    )

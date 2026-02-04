# body_sim/anatomy/uterus.py
"""
Матка (uterus/womb) с системой пролапса.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Tuple
from enum import Enum, auto
import math

from body_sim.core.enums import (
    FluidType, 
    Sex, 
    UterusState, 
    CervixState, 
    OvaryState, 
    FallopianTubeState
)
from body_sim.core.fluids import BreastFluid



@dataclass
class UterineWall:
    """Стенка матки с физическими свойствами."""
    thickness: float = 1.0           # см (толщина)
    elasticity: float = 1.0          # 0-1 (эластичность)
    integrity: float = 1.0           # 0-1 (целостность тканей)
    stretch_ratio: float = 1.0       # текущее растяжение
    
    # Усталость тканей от растяжения
    fatigue: float = 0.0             # 0-1
    
    def can_stretch(self, target_ratio: float) -> bool:
        """Может ли растянуться до целевого соотношения."""
        max_stretch = 3.0 * self.elasticity * self.integrity
        return target_ratio <= max_stretch
    
    def stretch(self, ratio: float) -> bool:
        """Попытка растяжения."""
        if not self.can_stretch(ratio):
            self.integrity -= 0.1  # Повреждение при перерастяжении
            return False
        
        self.stretch_ratio = ratio
        self.fatigue += (ratio - 1.0) * 0.1
        self.fatigue = min(1.0, self.fatigue)
        return True
    
    def recover(self, dt: float):
        """Восстановление."""
        self.fatigue = max(0.0, self.fatigue - 0.01 * dt)
        if self.stretch_ratio > 1.0:
            recovery = 0.001 * self.elasticity * dt
            self.stretch_ratio = max(1.0, self.stretch_ratio - recovery)


@dataclass
class Cervix:
    """Шейка матки."""
    length: float = 3.0              # см (длина)
    diameter: float = 2.5            # см (диаметр отверстия)
    max_dilation: float = 10.0       # см (максимальное раскрытие)
    
    state: CervixState = field(default=CervixState.CLOSED)
    current_dilation: float = 0.0    # текущее раскрытие
    
    # Связь с влагалищем
    vaginal_connection: Optional[Any] = field(default=None, repr=False)
    
    def dilate(self, amount: float) -> bool:
        """Растворение шейки."""
        new_dilation = min(self.current_dilation + amount, self.max_dilation)
        
        if new_dilation > self.diameter * 0.5:
            self.state = CervixState.DILATED
        if new_dilation >= self.diameter * 2:
            self.state = CervixState.FULLY_OPEN
            
        self.current_dilation = new_dilation
        return True
    
    def contract(self):
        """Сокращение."""
        self.current_dilation = max(0.0, self.current_dilation - 0.5)
        if self.current_dilation < 0.5:
            self.state = CervixState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Открыта ли шейка."""
        return self.current_dilation > 0.5
    
    @property
    def effective_diameter(self) -> float:
        """Эффективный диаметр прохода."""
        if self.state == CervixState.EVERTED:
            return self.max_dilation * 2  # При выворачивании проход максимален
        return self.current_dilation


@dataclass
class Ovary:
    """
    Яичник с фолликулами и яйцеклетками.
    При выворачивании может быть вытолкнут наружу через фаллопиеву трубу.
    """
    name: str = "ovary"
    side: str = "left"               # 'left' или 'right'
    
    # Размеры
    length: float = 3.0              # см
    width: float = 2.0               # см
    thickness: float = 1.5           # см
    
    # Состояние
    state: OvaryState = field(default=OvaryState.NORMAL)
    
    # Фолликулы
    follicle_count: int = 5          # Количество фолликулов
    follicle_sizes: List[float] = field(default_factory=lambda: [0.5]*5)  # см
    
    # Физиология
    hormone_production: float = 1.0  # 0-1 (уровень гормонов)
    blood_supply: float = 1.0        # 0-1 (кровоснабжение)
    
    # Положение (0 = норма, 1 = полностью вывернут)
    prolapse_degree: float = 0.0
    
    # Связь с трубой
    attached_tube: Optional['FallopianTube'] = field(default=None, repr=False)
    
    # Содержимое при выворачивании
    ruptured_follicles: int = 0
    
    def calculate_volume(self) -> float:
        """Объём яичника (мл)."""
        return self.length * self.width * self.thickness * 0.8
    
    def enlarge_follicles(self, amount: float):
        """Увеличить фолликулы (овуляция/кисты)."""
        for i in range(len(self.follicle_sizes)):
            self.follicle_sizes[i] = min(2.5, self.follicle_sizes[i] + amount)
        
        max_size = max(self.follicle_sizes)
        if max_size > 1.5:
            self.state = OvaryState.ENLARGED
    
    def rupture_follicle(self, index: int) -> bool:
        """Разрыв фолликула (овуляция)."""
        if 0 <= index < len(self.follicle_sizes):
            if self.follicle_sizes[index] > 1.0:
                self.follicle_sizes[index] = 0.3  # Уменьшается после разрыва
                self.ruptured_follicles += 1
                return True
        return False
    
    def evert(self, degree: float = 1.0):
        """Вывернуть яичник наружу."""
        self.prolapse_degree = min(1.0, self.prolapse_degree + degree)
        if self.prolapse_degree > 0.7:
            self.state = OvaryState.EVERTED
        elif self.prolapse_degree > 0.3:
            self.state = OvaryState.PROLAPSED
    
    def reposition(self, amount: float = 0.5) -> bool:
        """Вправить яичник."""
        if self.state == OvaryState.EVERTED and amount < 0.7:
            return False  # Требуется сильное вмешательство
        
        self.prolapse_degree = max(0.0, self.prolapse_degree - amount)
        if self.prolapse_degree < 0.2:
            self.state = OvaryState.NORMAL
        elif self.prolapse_degree < 0.5:
            self.state = OvaryState.PROLAPSED
        return True
    
    @property
    def is_everted(self) -> bool:
        """Полностью ли вывернут."""
        return self.state == OvaryState.EVERTED
    
    @property
    def visible_externally(self) -> bool:
        """Виден ли снаружи."""
        return self.prolapse_degree > 0.5
    
    @property
    def external_description(self) -> str:
        """Описание внешнего вида при выворачивании."""
        if not self.visible_externally:
            return ""
        
        desc = [f"{self.side.upper()} OVARY EXPOSED"]
        
        # Описание фолликулов на поверхности
        visible_follicles = [f"{s:.1f}cm" for s in self.follicle_sizes if s > 0.8]
        if visible_follicles:
            desc.append(f"Follicles: {', '.join(visible_follicles)}")
        
        if self.ruptured_follicles > 0:
            desc.append(f"Ruptured: {self.ruptured_follicles}")
        
        if self.blood_supply < 0.5:
            desc.append("⚠️ ISCHEMIC")
        
        return " | ".join(desc)
    
    def __str__(self) -> str:
        state_emoji = {
            OvaryState.NORMAL: "🟢",
            OvaryState.ENLARGED: "🟡",
            OvaryState.PROLAPSED: "🟠",
            OvaryState.EVERTED: "🔴",
            OvaryState.TORSION: "⚫"
        }.get(self.state, "⚪")
        
        if self.is_everted:
            return (
                f"{state_emoji} Ovary ({self.side}) [{self.state.name}]\n"
                f"   🔴 EXTERNALLY VISIBLE - {self.external_description}\n"
                f"   Prolapse: {self.prolapse_degree:.0%}, "
                f"Volume: {self.calculate_volume():.1f}ml"
            )
        
        return (
            f"{state_emoji} Ovary ({self.side}) [{self.state.name}]\n"
            f"   Size: {self.length}×{self.width}×{self.thickness}cm, "
            f"Follicles: {self.follicle_count}\n"
            f"   Hormones: {self.hormone_production:.0%}, "
            f"Blood supply: {self.blood_supply:.0%}"
        )


@dataclass
class FallopianTube:
    """
    Фаллопиева труба соединяет матку с яичником.
    При инверсии матки отверстие трубы видно снаружи.
    """
    name: str = "fallopian_tube"
    side: str = "left"               # 'left' или 'right'
    
    # Размеры
    length: float = 10.0             # см (длина)
    diameter: float = 0.3            # см (диаметр)
    uterine_opening: float = 0.1     # см (отверстие в матке)
    ovarian_opening: float = 0.5     # см (отверстие к яичнику - фимбрии)
    
    # Состояние
    state: FallopianTubeState = field(default=FallopianTubeState.NORMAL)
    
    # Эластичность
    elasticity: float = 1.0          # 0-1
    max_stretch_ratio: float = 3.0   # максимальное растяжение
    
    # Текущее растяжение
    current_stretch: float = 1.0
    
    # Связи
    uterus: Optional[Any] = field(default=None, repr=False)
    ovary: Optional[Ovary] = field(default=None, repr=False)
    
    # Содержимое
    contained_fluid: float = 0.0     # мл (жидкость в трубе)
    contained_ovum: Optional[Any] = None  # яйцеклетка
    
    def __post_init__(self):
        if self.ovary:
            self.ovary.attached_tube = self
    
    @property
    def current_length(self) -> float:
        """Текущая длина с учётом растяжения."""
        return self.length * self.current_stretch
    
    @property
    def is_stretched(self) -> bool:
        """Натянута ли труба."""
        return self.current_stretch > 1.5
    
    @property
    def can_prolapse_ovary(self) -> bool:
        """Может ли яичник выпасть через эту трубу."""
        if not self.ovary:
            return False
        # Яичник может выпасть если труба растянута и отверстие достаточно велико
        return (self.current_stretch > 2.0 and 
                self.ovary.calculate_volume() < self.ovarian_opening * 10)
    
    def stretch(self, ratio: float) -> bool:
        """Растянуть трубу."""
        if ratio > self.max_stretch_ratio:
            self.state = FallopianTubeState.BLOCKED  # Перерастяжение
            return False
        
        self.current_stretch = ratio
        
        if ratio > 2.0:
            self.state = FallopianTubeState.DILATED
        elif ratio > 1.5:
            self.state = FallopianTubeState.NORMAL
            
        return True
    
    def evert_with_ovary(self):
        """Вывернуть трубу с яичником наружу."""
        self.state = FallopianTubeState.EVERTED_WITH_OVARY
        if self.ovary:
            self.ovary.evert(1.0)
    
    def reposition(self):
        """Вправить трубу."""
        self.state = FallopianTubeState.NORMAL
        self.current_stretch = max(1.0, self.current_stretch - 0.5)
        if self.ovary:
            self.ovary.reposition(0.5)
    
    @property
    def uterine_opening_visible(self) -> bool:
        """Видно ли отверстие в матке (при инверсии)."""
        if not self.uterus:
            return False
        # При инверсии/выворачивании матки
        return (hasattr(self.uterus, 'state') and 
                self.uterus.state in (UterusState.EVERTED, UterusState.INVERTED))
    
    @property
    def external_description(self) -> str:
        """Описание при внешнем виде (инверсия)."""
        if not self.uterine_opening_visible:
            return ""
        
        desc = [f"{self.side.upper()} TUBE OPENING"]
        desc.append(f"Ø{self.uterine_opening:.1f}cm")
        
        if self.is_stretched:
            desc.append(f"stretched {self.current_stretch:.1f}x")
        
        if self.ovary and self.ovary.visible_externally:
            desc.append(f"→ OVARY EXPOSED")
        
        if self.contained_fluid > 0:
            desc.append(f"fluid:{self.contained_fluid:.1f}ml")
        
        return " | ".join(desc)
    
    def __str__(self) -> str:
        state_emoji = {
            FallopianTubeState.NORMAL: "🟢",
            FallopianTubeState.DILATED: "🟡",
            FallopianTubeState.BLOCKED: "⛔",
            FallopianTubeState.PROLAPSED: "🟠",
            FallopianTubeState.EVERTED_WITH_OVARY: "🔴"
        }.get(self.state, "⚪")
        
        if self.uterine_opening_visible:
            return (
                f"{state_emoji} Tube ({self.side}) [{self.state.name}]\n"
                f"   👁️ EXTERNAL OPENING: {self.external_description}\n"
                f"   Length: {self.current_length:.1f}cm (×{self.current_stretch:.1f})"
            )
        
        return (
            f"{state_emoji} Tube ({self.side}) [{self.state.name}]\n"
            f"   Length: {self.current_length:.1f}cm, "
            f"Ø{self.diameter}cm\n"
            f"   Openings: uterine {self.uterine_opening}cm, "
            f"ovarian {self.ovarian_opening}cm"
        )


@dataclass
class Uterus:
    """
    Матка с системой пролапса и полного выворачивания.
    Содержит фаллопиевы трубы и яичники.
    
    При полном пролапсе (EVERTED):
    - Вся матка выворачивается через влагалище наружу
    - Внутренний объём становится внешним
    - Все содержимое (жидкости, предметы) вываливается
    - Видны отверстия фаллопиевых труб
    - Через них возможно вывернуть яичники
    """
    
    name: str = "uterus"
    
    # Базовые размеры (нормальное состояние)
    base_length: float = 7.0         # см (длина матки)
    base_width: float = 5.0          # см (ширина)
    base_depth: float = 3.0          # см (толщина стенок)
    
    # Внутренний объём
    cavity_volume: float = 50.0      # мл (объём полости)
    
    # Компоненты
    cervix: Cervix = field(default_factory=Cervix)
    walls: UterineWall = field(default_factory=UterineWall)
    
    # Фаллопиевы трубы и яичники
    left_tube: Optional[FallopianTube] = field(default=None)
    right_tube: Optional[FallopianTube] = field(default=None)
    left_ovary: Optional[Ovary] = field(default=None)
    right_ovary: Optional[Ovary] = field(default=None)
    
    # Состояние
    state: UterusState = field(default=UterusState.NORMAL)
    prolapse_stage: float = 0.0      # 0-1 (степень опущения)
    
    # Позиция (0 = норма, 1 = полный пролапс)
    descent_position: float = 0.0
    
    # Содержимое полости
    fluids: Dict[FluidType, float] = field(default_factory=dict)
    inserted_objects: List[Any] = field(default_factory=list)
    
    # Физиология
    muscle_tone: float = 0.7         # тонус мышц матки
    ligament_integrity: float = 1.0  # целостность связок
    pelvic_floor_strength: float = 0.7  # сила тазового дна
    
    # При полном пролапсе - вывернутая конфигурация
    everted_volume: float = field(init=False)  # объём вывернутой матки
    
    # События
    _listeners: Dict[str, List[Callable]] = field(default_factory=dict)
    
    def __post_init__(self):
        self.everted_volume = self.cavity_volume * 1.5  # +50% при выворачивании
        
        # Инициализация труб и яичников если не заданы
        if self.left_tube is None:
            self.left_tube = FallopianTube(side="left", uterus=self)
        if self.right_tube is None:
            self.right_tube = FallopianTube(side="right", uterus=self)
        if self.left_ovary is None:
            self.left_ovary = Ovary(side="left")
            self.left_tube.ovary = self.left_ovary
            self.left_ovary.attached_tube = self.left_tube
        if self.right_ovary is None:
            self.right_ovary = Ovary(side="right")
            self.right_tube.ovary = self.right_ovary
            self.right_ovary.attached_tube = self.right_tube
    
    # ======================
    # EVENTS
    # ======================
    
    def on(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)
    
    def _emit(self, event: str, **data):
        for cb in self._listeners.get(event, []):
            cb(self, **data)
    
    # ======================
    # PROPERTIES
    # ======================
    
    @property
    def tubes(self) -> List[FallopianTube]:
        """Список труб."""
        return [t for t in [self.left_tube, self.right_tube] if t]
    
    @property
    def ovaries(self) -> List[Ovary]:
        """Список яичников."""
        return [o for o in [self.left_ovary, self.right_ovary] if o]
    
    @property
    def current_length(self) -> float:
        """Текущая длина с учётом состояния."""
        if self.state == UterusState.EVERTED:
            # При выворачивании длина увеличивается (выворачивается наружу)
            return self.base_length * (1 + self.prolapse_stage * 2)
        return self.base_length * (1 - self.descent_position * 0.3)
    
    @property
    def current_volume(self) -> float:
        """Текущий внутренний объём."""
        if self.state in (UterusState.EVERTED, UterusState.INVERTED):
            # При выворачивании внутренний объём минимален
            return self.cavity_volume * 0.1
        stretch_factor = self.walls.stretch_ratio ** 3
        return self.cavity_volume * stretch_factor
    
    @property
    def available_volume(self) -> float:
        """Свободный объём в полости."""
        fluid_volume = sum(self.fluids.values())
        objects_volume = sum(
            getattr(obj, 'volume', 0) or getattr(obj, 'effective_volume', 0)
            for obj in self.inserted_objects
        )
        return max(0, self.current_volume - fluid_volume - objects_volume)
    
    @property
    def is_everted(self) -> bool:
        """Полностью ли вывернута."""
        return self.state == UterusState.EVERTED
    
    @property
    def is_inverted(self) -> bool:
        """Инвертирована ли (внутрь)."""
        return self.state == UterusState.INVERTED
    
    @property
    def is_prolapsed(self) -> bool:
        """Есть ли пролапс любой степени."""
        return self.state in (UterusState.DESCENDED, UterusState.PROLAPSED, UterusState.EVERTED)
    
    @property
    def external_visible_volume(self) -> float:
        """
        Объём, видимый снаружи при пролапсе.
        При полном выворачивании - весь внутренний объём + стенки.
        """
        if self.state == UterusState.EVERTED:
            # Внутренняя поверхность снаружи
            return self.everted_volume
        elif self.state == UterusState.PROLAPSED:
            return self.cavity_volume * self.prolapse_stage * 0.5
        return 0.0
    
    @property
    def tube_openings_visible(self) -> bool:
        """Видны ли отверстия фаллопиевых труб."""
        return self.is_everted or self.is_inverted
    
    @property
    def everted_ovaries(self) -> List[Ovary]:
        """Список вывернутых наружу яичников."""
        return [o for o in self.ovaries if o and o.is_everted]
    
    @property
    def external_description(self) -> str:
        """Описание внешнего вида при выворачивании."""
        if not self.is_everted:
            return ""
        
        parts = ["🔴 EVERTED UTERUS - INTERNAL SURFACE EXPOSED"]
        
        # Отверстия труб
        if self.tube_openings_visible:
            parts.append("\n  VISIBLE TUBE OPENINGS:")
            for tube in self.tubes:
                if tube:
                    parts.append(f"    • {tube.external_description}")
        
        # Вывернутые яичники
        everted = self.everted_ovaries
        if everted:
            parts.append("\n  EVERTED OVARIES:")
            for ovary in everted:
                parts.append(f"    • {ovary.external_description}")
        
        return "\n".join(parts)
    
    # ======================
    # FLUID MANAGEMENT
    # ======================
    
    def add_fluid(self, fluid_type: FluidType, amount: float) -> float:
        """Добавить жидкость в полость."""
        if self.state == UterusState.EVERTED:
            # При выворачивании жидкость вытекает наружу
            self._emit("fluid_ejected", fluid_type=fluid_type, amount=amount, reason="everted")
            return 0.0
        
        available = self.available_volume
        actual = min(amount, available)
        
        self.fluids[fluid_type] = self.fluids.get(fluid_type, 0) + actual
        
        if actual < amount:
            self._emit("overflow", fluid_type=fluid_type, overflow=amount - actual)
        
        if actual > 0:
            self._emit("fluid_added", fluid_type=fluid_type, amount=actual)
        
        return actual
    
    def remove_fluid(self, fluid_type: Optional[FluidType] = None, amount: Optional[float] = None) -> Dict[FluidType, float]:
        """Удалить жидкость."""
        removed = {}
        
        if fluid_type:
            available = self.fluids.get(fluid_type, 0)
            to_remove = amount if amount is not None else available
            actual = min(to_remove, available)
            removed[fluid_type] = actual
            self.fluids[fluid_type] = available - actual
            if self.fluids[fluid_type] <= 0:
                del self.fluids[fluid_type]
        else:
            # Удалить все
            for ft in list(self.fluids.keys()):
                available = self.fluids[ft]
                to_remove = amount if amount is not None else available
                actual = min(to_remove, available)
                removed[ft] = actual
                self.fluids[ft] -= actual
                if self.fluids[ft] <= 0:
                    del self.fluids[ft]
        
        return removed
    
    def eject_all_contents(self) -> Dict[str, Any]:
        """
        Принудительное изгнание всего содержимого.
        Используется при полном выворачивании.
        """
        ejected = {
            'fluids': self.fluids.copy(),
            'objects': self.inserted_objects.copy(),
            'total_volume': sum(self.fluids.values()) + sum(
                getattr(obj, 'volume', 0) or getattr(obj, 'effective_volume', 0)
                for obj in self.inserted_objects
            )
        }
        
        # Очищаем
        self.fluids.clear()
        for obj in self.inserted_objects:
            if hasattr(obj, 'is_inserted'):
                obj.is_inserted = False
        self.inserted_objects.clear()
        
        self._emit("total_ejection", **ejected)
        return ejected
    
    # ======================
    # OBJECT INSERTION
    # ======================
    
    def insert_object(self, obj: Any) -> bool:
        """Вставить предмет в матку (через шейку)."""
        if self.state == UterusState.EVERTED:
            return False  # Невозможно вставить в вывернутую матку
        
        obj_volume = getattr(obj, 'volume', 0) or getattr(obj, 'effective_volume', 0)
        
        if obj_volume > self.available_volume:
            return False
        
        # Проверка прохода через шейку
        obj_diameter = getattr(obj, 'diameter', 0) or getattr(obj, 'effective_diameter', 0)
        if obj_diameter > self.cervix.effective_diameter * 1.2:
            # Нужно растянуть шейку
            if not self.cervix.dilate(obj_diameter - self.cervix.effective_diameter):
                return False
        
        self.inserted_objects.append(obj)
        if hasattr(obj, 'is_inserted'):
            obj.is_inserted = True
        if hasattr(obj, 'inserted_depth'):
            obj.inserted_depth = getattr(obj, 'length', 0)
        
        self._emit("object_inserted", object=obj)
        return True
    
    def remove_object(self, index: int) -> Optional[Any]:
        """Извлечь предмет."""
        if 0 <= index < len(self.inserted_objects):
            obj = self.inserted_objects.pop(index)
            if hasattr(obj, 'is_inserted'):
                obj.is_inserted = False
            self._emit("object_removed", object=obj)
            return obj
        return None
    
    # ======================
    # TUBE & OVARY MANIPULATION
    # ======================
    
    def stretch_tube(self, side: str, ratio: float) -> bool:
        """Растянуть фаллопиеву трубу."""
        tube = self.left_tube if side == "left" else self.right_tube
        if not tube:
            return False
        
        success = tube.stretch(ratio)
        
        # При сильном растяжении яичник может начать выпадать
        if success and ratio > 2.5 and tube.ovary:
            if tube.can_prolapse_ovary:
                tube.ovary.evert(0.3)
                self._emit("ovary_starting_prolapse", side=side, ovary=tube.ovary)
        
        return success
    
    def evert_ovary(self, side: str, force: float = 1.0) -> bool:
        """
        Вывернуть яичник наружу через трубу.
        Требует растянутой трубы и видимого отверстия (инверсия/выворачивание).
        """
        tube = self.left_tube if side == "left" else self.right_tube
        ovary = self.left_ovary if side == "left" else self.right_ovary
        
        if not tube or not ovary:
            return False
        
        # Проверка условий
        if not self.tube_openings_visible:
            self._emit("evert_failed", reason="tube_openings_not_visible", side=side)
            return False
        
        if tube.current_stretch < 2.0:
            self._emit("evert_failed", reason="tube_not_stretched_enough", side=side)
            return False
        
        # Выворачивание
        tube.evert_with_ovary()
        
        # Дополнительное усилие
        if force > 0.5:
            ovary.evert(force)
        
        self._emit("ovary_everted", side=side, ovary=ovary, tube=tube)
        return True
    
    def reposition_ovary(self, side: str, amount: float = 0.5) -> bool:
        """Вправить яичник."""
        ovary = self.left_ovary if side == "left" else self.right_ovary
        tube = self.left_tube if side == "left" else self.right_tube
        
        if not ovary:
            return False
        
        success = ovary.reposition(amount)
        
        if success and tube:
            tube.reposition()
        
        return success
    
    def ovulate(self, side: str, follicle_idx: int = -1) -> bool:
        """Овуляция - разрыв фолликула и выход яйцеклетки."""
        ovary = self.left_ovary if side == "left" else self.right_ovary
        tube = self.left_tube if side == "left" else self.right_tube
        
        if not ovary or not tube:
            return False
        
        # Если яичник вывернут - овуляция наружу
        if ovary.is_everted:
            if ovary.rupture_follicle(follicle_idx if follicle_idx >= 0 else 0):
                self._emit("external_ovulation", side=side, ovary=ovary)
                return True
            return False
        
        # Нормальная овуляция в трубу
        if ovary.rupture_follicle(follicle_idx if follicle_idx >= 0 else 0):
            # Яйцеклетка попадает в трубу
            tube.contained_ovum = {"stage": "fertilizable", "side": side}
            self._emit("ovulation", side=side, tube=tube)
            return True
        
        return False
    
    # ======================
    # PROLAPSE MECHANICS
    # ======================
    
    def calculate_prolapse_risk(self) -> float:
        """Рассчитать риск пролапса."""
        risk = 0.0
        
        # Слабость связок
        risk += (1.0 - self.ligament_integrity) * 0.3
        
        # Слабость тазового дна
        risk += (1.0 - self.pelvic_floor_strength) * 0.3
        
        # Перерастяжение стенок
        if self.walls.stretch_ratio > 2.0:
            risk += (self.walls.stretch_ratio - 2.0) * 0.2
        
        # Внутреннее давление (от жидкостей и предметов)
        fill_ratio = 1.0 - (self.available_volume / max(self.current_volume, 1))
        risk += fill_ratio * 0.2
        
        # Усталость тканей
        risk += self.walls.fatigue * 0.1
        
        # Тяжесть яичников
        ovary_weight = sum(o.calculate_volume() for o in self.ovaries if o)
        risk += ovary_weight * 0.001
        
        return min(1.0, risk)
    
    def apply_strain(self, force: float) -> bool:
        """
        Приложить силу (например, при родах, сильном напряжении).
        Возвращает True, если произошёл пролапс.
        """
        # Проверка на пролапс
        risk = self.calculate_prolapse_risk()
        
        if force * risk > 0.5:
            return self._progress_prolapse(force * risk)
        
        return False
    
    def _progress_prolapse(self, amount: float) -> bool:
        """Прогрессирование пролапса."""
        old_state = self.state
        
        self.descent_position = min(1.0, self.descent_position + amount * 0.1)
        self.prolapse_stage = self.descent_position
        
        # Растяжение труб при пролапсе
        for tube in self.tubes:
            if tube:
                tube.stretch(1.0 + self.descent_position * 2)
        
        # Определение стадии
        if self.descent_position < 0.3:
            self.state = UterusState.DESCENDED
        elif self.descent_position < 0.7:
            self.state = UterusState.PROLAPSED
        else:
            # Полное выворачивание!
            if self.state != UterusState.EVERTED:
                self._complete_eversion()
        
        if self.state != old_state:
            self._emit("state_change", old=old_state, new=self.state)
            return True
        
        return False
    
    def _complete_eversion(self):
        """Полное выворачивание матки наизнанку."""
        self.state = UterusState.EVERTED
        self.cervix.state = CervixState.EVERTED
        
        # Выталкивание всего содержимого
        ejected = self.eject_all_contents()
        
        # Физические изменения
        self.walls.stretch_ratio = 2.5  # Сильное растяжение
        self.walls.fatigue = 1.0  # Максимальная усталость
        
        # Трубы теперь видны снаружи
        for tube in self.tubes:
            if tube:
                tube.state = FallopianTubeState.PROLAPSED
        
        self._emit("complete_eversion", ejected=ejected)
    
    def invert(self, force: float = 1.0) -> bool:
        """
        Инверсия матки (внутрь) - редкое но опасное состояние.
        При этом отверстия труб также видны, но направлены внутрь.
        """
        if self.state != UterusState.NORMAL:
            return False
        
        self.state = UterusState.INVERTED
        self.walls.stretch_ratio = 2.0
        
        # Трубы втянуты, но их отверстия видны
        for tube in self.tubes:
            if tube:
                tube.current_stretch = 2.5
        
        self._emit("inversion", force=force)
        return True
    
    def reduce_prolapse(self, amount: float) -> bool:
        """
        Попытка уменьшить пролапс (ручная репозиция, лечение).
        """
        if self.state == UterusState.EVERTED:
            # Полное выворачивание требует медицинского вмешательства
            if amount < 0.5:
                return False
            # Успешная репозиция
            self.state = UterusState.PROLAPSED
        
        self.descent_position = max(0.0, self.descent_position - amount)
        self.prolapse_stage = self.descent_position
        
        # Вправление яичников
        for ovary in self.ovaries:
            if ovary and ovary.state in (OvaryState.PROLAPSED, OvaryState.EVERTED):
                ovary.reposition(amount * 0.5)
        
        # Восстановление труб
        for tube in self.tubes:
            if tube:
                tube.current_stretch = max(1.0, tube.current_stretch - amount)
                if tube.state == FallopianTubeState.EVERTED_WITH_OVARY:
                    tube.state = FallopianTubeState.PROLAPSED
        
        if self.descent_position < 0.1:
            self.state = UterusState.NORMAL
            self.cervix.state = CervixState.CLOSED
        
        return True
    
    # ======================
    # TICK & UPDATE
    # ======================
    
    def tick(self, dt: float = 1.0):
        """Обновление состояния."""
        # Восстановление стенок
        self.walls.recover(dt)
        
        # Обновление яичников
        for ovary in self.ovaries:
            if ovary:
                # Гормональная функция
                ovary.hormone_production = max(0.0, ovary.hormone_production - 0.001 * dt)
                
                # Кровоснабжение вывернутых яичников ухудшается
                if ovary.is_everted:
                    ovary.blood_supply = max(0.3, ovary.blood_supply - 0.01 * dt)
                    if ovary.blood_supply < 0.5:
                        ovary.state = OvaryState.TORSION
        
        # Естественное сокращение шейки
        if self.cervix.state not in (CervixState.EVERTED, CervixState.FULLY_OPEN):
            self.cervix.contract()
        
        # При выворачивании - поддержание состояния
        if self.state == UterusState.EVERTED:
            # Постепенное ухудшение без лечения
            self.ligament_integrity = max(0.1, self.ligament_integrity - 0.001 * dt)
            self.walls.integrity = max(0.3, self.walls.integrity - 0.001 * dt)
        
        # Проверка на спонтанный пролапс
        elif self.state == UterusState.NORMAL:
            risk = self.calculate_prolapse_risk()
            if risk > 0.8:
                self._progress_prolapse(0.1)
    
    # ======================
    # UTILITY
    # ======================
    
    def __str__(self) -> str:
        state_emoji = {
            UterusState.NORMAL: "🟢",
            UterusState.DESCENDED: "🟡",
            UterusState.PROLAPSED: "🟠",
            UterusState.EVERTED: "🔴",
            UterusState.INVERTED: "⚫"
        }.get(self.state, "⚪")
        
        contents = []
        if self.fluids:
            total_fluid = sum(self.fluids.values())
            contents.append(f"{total_fluid:.0f}ml fluid")
        if self.inserted_objects:
            contents.append(f"{len(self.inserted_objects)} objects")
        
        contents_str = f" ({', '.join(contents)})" if contents else " (empty)"
        
        # Базовая информация
        lines = [
            f"{state_emoji} Uterus [{self.state.name}]",
            f"   Volume: {self.current_volume:.0f}ml{contents_str}",
            f"   Descent: {self.descent_position:.0%}",
            f"   Cervix: {self.cervix.state.name} ({self.cervix.current_dilation:.1f}cm)",
            f"   Walls: stretch={self.walls.stretch_ratio:.1f}x, fatigue={self.walls.fatigue:.0%}"
        ]
        
        # При выворачивании - детальное описание
        if self.is_everted:
            lines.append(f"\n{self.external_description}")
        
        # Информация о трубах и яичниках
        lines.append(f"\n   Fallopian Tubes:")
        for tube in self.tubes:
            if tube:
                lines.append(f"      {tube}")
        
        lines.append(f"\n   Ovaries:")
        for ovary in self.ovaries:
            if ovary:
                lines.append(f"      {ovary}")
        
        return "\n".join(lines)
    
         
@dataclass
class UterusSystem:
    """Система маток для тела (поддержка множественных маток для фантастики)."""
    
    uteri: List[Uterus] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.uteri:
            self.uteri.append(Uterus())
    
    @property
    def primary(self) -> Optional[Uterus]:
        """Основная матка."""
        return self.uteri[0] if self.uteri else None
    
    def add_uterus(self, uterus: Uterus) -> int:
        """Добавить дополнительную матку."""
        self.uteri.append(uterus)
        return len(self.uteri) - 1
    
    def tick(self, dt: float = 1.0):
        """Обновление всех маток."""
        for uterus in self.uteri:
            uterus.tick(dt)
    
    def __iter__(self):
        return iter(self.uteri)
    
    def __len__(self):
        return len(self.uteri)
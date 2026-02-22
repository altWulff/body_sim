# body_sim/anatomy/mouth.py
"""
Рот и глоточная система с возможностью пенетрации и хранения жидкости.

Особенности:
- Губы с различными состояниями (сжатые, приоткрытые, раздутые)
- Полость рта с объемом и вместимостью
- Глотка/гортань как проход в пищевод
- Рефлексы (рвотный, давительный)
- Система пенетрации аналогичная вагине
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
import math

from body_sim.core.enums import FluidType, LipState, MouthState, ThroatState
from body_sim.core.fluids import FluidMixture, BreastFluid
from body_sim.core.constants import PRESSURE_LEAK_MIN



@dataclass
class Lips:
    """Губы с физическими свойствами."""
    fullness: float = 1.0            # Полнота (0.5-2.0)
    elasticity: float = 0.8          # Эластичность
    stretch_ratio: float = 1.0       # Растяжение
    puff_ratio: float = 1.0          # Надутость
    
    state: LipState = field(default=LipState.CLOSED)
    fatigue: float = 0.0             # Усталость
    numbness: float = 0.0            # Онемение
    
    # Размеры
    base_height: float = 0.8         # см (толщина)
    base_width: float = 4.0          # см (ширина рта)
    
    @property
    def effective_opening(self) -> float:
        """Эффективное отверстие рта."""
        if self.state == LipState.CLOSED:
            return 0.0
        base = self.base_width * (self.stretch_ratio ** 0.5)
        if self.state == LipState.OPEN:
            return base * 0.7
        elif self.state == LipState.STRETCHED:
            return base * self.stretch_ratio
        return base * 0.3
    
    def stretch(self, ratio: float) -> bool:
        """Растянуть губы."""
        max_stretch = 5.0 * self.elasticity
        if ratio > max_stretch:
            self.fatigue += 0.1
            return False
        
        self.stretch_ratio = ratio
        if ratio > 2.0:
            self.state = LipState.STRETCHED
            self.numbness += 0.05
        elif ratio > 1.5:
            self.state = LipState.OPEN
            
        return True
    
    def puff(self, ratio: float):
        """Раздуть губы (воздухом или жидкостью)."""
        self.puff_ratio = max(1.0, min(ratio, 3.0))
        if self.puff_ratio > 1.5:
            self.state = LipState.PUFFED
    
    def relax(self, dt: float):
        """Восстановление."""
        if self.stretch_ratio > 1.0:
            recovery = 0.01 * self.elasticity * dt
            self.stretch_ratio = max(1.0, self.stretch_ratio - recovery)
        self.fatigue = max(0.0, self.fatigue - 0.02 * dt)
        self.numbness = max(0.0, self.numbness - 0.01 * dt)
        
        if self.state in (LipState.STRETCHED, LipState.PUFFED) and self.stretch_ratio <= 1.2:
            self.state = LipState.SLIGHTLY_OPEN if self.fatigue > 0.3 else LipState.CLOSED


@dataclass
class Throat:
    """Глотка и гортань."""
    length: float = 12.0             # см (длина)
    base_diameter: float = 2.0       # см (диаметр)
    
    state: ThroatState = field(default=ThroatState.CLOSED)
    current_diameter: float = field(init=False)
    
    # Растяжение
    stretch_ratio: float = 1.0
    max_stretch: float = 4.0
    elasticity: float = 0.6
    
    # Спазмы и рефлексы
    gag_reflex_threshold: float = 0.7  # Порог рвотного рефлекса
    constriction: float = 0.0          # Спазм (0-1)
    
    # Соединения
    esophagus_connection: Optional[Any] = field(default=None, repr=False)
    stomach_connection: Optional[Any] = field(default=None, repr=False)
    
    def __post_init__(self):
        self.current_diameter = self.base_diameter
    
    @property
    def is_open(self) -> bool:
        return self.state in (ThroatState.RELAXED, ThroatState.PENETRATED, ThroatState.STRETCHED)
    
    @property
    def effective_diameter(self) -> float:
        """Эффективный диаметр с учетом спазма."""
        constriction_mod = 1.0 - (self.constriction * 0.8)
        return self.current_diameter * constriction_mod * self.stretch_ratio
    
    def open(self, amount: float = 0.5):
        """Открыть глотку."""
        self.constriction = max(0.0, self.constriction - amount)
        if self.constriction < 0.3:
            self.state = ThroatState.RELAXED
    
    def constrict(self, amount: float = 0.5):
        """Сжать глотку (рефлекс)."""
        self.constriction = min(1.0, self.constriction + amount)
        self.state = ThroatState.CONSTRICTED
    
    def stretch(self, ratio: float) -> bool:
        """Растянуть глотку."""
        if ratio > self.max_stretch:
            return False
        self.stretch_ratio = ratio
        self.current_diameter = self.base_diameter * ratio
        self.state = ThroatState.STRETCHED
        return True
    
    def trigger_gag_reflex(self) -> bool:
        """Вызвать рвотный рефлекс."""
        if self.constriction < self.gag_reflex_threshold:
            self.constrict(0.8)
            return True
        return False
    
    def tick(self, dt: float):
        """Обновление состояния."""
        # Постепенное расслабление
        if self.constriction > 0:
            self.constriction = max(0.0, self.constriction - 0.1 * dt)
        if self.constriction < 0.2 and self.state == ThroatState.CONSTRICTED:
            self.state = ThroatState.CLOSED


@dataclass
class Mouth:
    """
    Полость рта с системой пенетрации и жидкостей.
    """
    name: str = "mouth"
    
    # Компоненты
    lips: Lips = field(default_factory=Lips)
    throat: Throat = field(default_factory=Throat)
    
    # Объемы
    base_volume: float = 80.0        # мл (пустой рот)
    max_volume: float = 400.0        # мл (растянутый)
    current_volume: float = field(init=False)
    
    # Жидкость
    mixture: FluidMixture = field(default_factory=FluidMixture)
    saliva_production: float = 1.0   # Скорость слюноотделения
    
    # Состояние
    state: MouthState = field(default=MouthState.EMPTY)
    
    # Растяжение щек
    cheek_stretch: float = 1.0
    max_cheek_stretch: float = 3.0
    
    # Пенетрация
    inserted_object: Optional[Any] = field(default=None, repr=False)
    penetration_depth: float = 0.0   # Глубина проникновения
    
    # Рефлексы
    gag_triggered: bool = False
    choking: bool = False
    
    # События
    _listeners: Dict[str, List[Callable]] = field(default_factory=dict)
    
    def __post_init__(self):
        self.current_volume = self.base_volume
    
    # ============ EVENTS ============
    
    def on(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)
    
    def _emit(self, event: str, **data):
        for cb in self._listeners.get(event, []):
            cb(self, **data)
    
    # ============ PROPERTIES ============
    
    @property
    def filled(self) -> float:
        """Объем жидкости + объем объекта."""
        fluid = self.mixture.total()
        obj_volume = getattr(self.inserted_object, 'volume', 0) if self.inserted_object else 0
        return fluid + obj_volume
    
    @property
    def available_volume(self) -> float:
        return self.current_volume - self.filled
    
    @property
    def fill_ratio(self) -> float:
        return self.filled / self.current_volume if self.current_volume > 0 else 0
    
    @property
    def can_breathe(self) -> bool:
        """Может ли дышать носом/ртом."""
        if self.choking:
            return False
        if self.inserted_object and self.penetration_depth > self.throat.length * 0.8:
            return False
        return True
    
    # ============ FLUID MANAGEMENT ============
    
    def add_fluid(self, fluid: 'FluidType | BreastFluid', amount: float) -> float:
        """Добавить жидкость в рот."""
        if amount <= 0:
            return 0.0
        
        fluid_type = fluid.fluid_type if isinstance(fluid, BreastFluid) else fluid
        available = self.available_volume
        actual = min(amount, available)
        
        if actual > 0:
            self.mixture.add(fluid_type, actual)
            # Реакция на вкус может вызвать слюноотделение
            if actual > 10:
                self.saliva_production = min(3.0, self.saliva_production + 0.5)
        
        self._update_state()
        self._emit("fluid_added", amount=actual, type=fluid_type)
        return actual
    
    def remove_fluid(self, amount: float) -> float:
        """Убрать жидкость (глотание/выплевывание)."""
        if amount <= 0:
            return 0.0
        actual = min(amount, self.mixture.total())
        self.mixture.remove(actual)
        self._update_state()
        return actual
    
    def swallow(self, amount: float = None) -> float:
        """Проглотить жидкость в пищевод/желудок."""
        if not self.throat.esophagus_connection:
            return 0.0
        
        available = self.mixture.total()
        to_swallow = amount if amount is not None else available
        to_swallow = min(to_swallow, available)
        
        if to_swallow <= 0:
            return 0.0
        
        # Проверяем проходимость
        if self.throat.state == ThroatState.CONSTRICTED:
            to_swallow *= 0.1  # Затруднено глотание
        
        # Передаем в соединение
        swallowed = self.throat.esophagus_connection.receive_fluid(
            dict(self.mixture.components), to_swallow
        )
        
        if swallowed > 0:
            self.mixture.remove(swallowed)
            self._emit("swallowed", amount=swallowed)
        
        self._update_state()
        return swallowed
    
    def produce_saliva(self, dt: float):
        """Выработка слюны."""
        amount = self.saliva_production * dt * 0.5  # мл/тик
        if self.available_volume > 0:
            self.add_fluid(FluidType.SALIVA, min(amount, self.available_volume))
    
    # ============ PENETRATION SYSTEM ============
    
    def insert_object(self, obj: Any, force: bool = False) -> bool:
        """Вставить объект в рот."""
        if self.inserted_object is not None and not force:
            return False
        
        obj_diameter = getattr(obj, 'diameter', 0) or getattr(obj, 'effective_diameter', 0)
        
        # Проверяем помещается ли
        if obj_diameter > self.lips.effective_opening * 1.5 and not force:
            return False
        
        # Растягиваем губы
        if obj_diameter > self.lips.effective_opening:
            required_stretch = obj_diameter / self.lips.base_width
            if not self.lips.stretch(required_stretch) and not force:
                return False
        
        self.inserted_object = obj
        if hasattr(obj, 'is_inserted'):
            obj.is_inserted = True
        
        self._emit("object_inserted", object=obj)
        self._update_state()
        return True
    
    def advance_object(self, depth: float) -> float:
        """Продвинуть объект глубже (в глотку)."""
        if not self.inserted_object:
            return 0.0
        
        new_depth = self.penetration_depth + depth
        max_depth = self.throat.length + 2.0  # +2см в пищевод
        
        actual_depth = min(new_depth, max_depth)
        moved = actual_depth - self.penetration_depth
        self.penetration_depth = actual_depth
        
        # Проверяем глотку
        if self.penetration_depth > self.throat.length * 0.5:
            self.throat.open(0.3)
        
        if self.penetration_depth > self.throat.length * 0.8:
            # Риск рвотного рефлекса
            if not self.gag_triggered and self.throat.trigger_gag_reflex():
                self.gag_triggered = True
                self.state = MouthState.GAGGING
                self._emit("gag_reflex_triggered")
        
        if self.penetration_depth > self.throat.length:
            # В пищеводе
            if not self.can_breathe:
                self.choking = True
                self.state = MouthState.CHOKING
                self._emit("choking")
        
        # Растяжение глотки
        obj_diam = getattr(self.inserted_object, 'diameter', 2.0)
        if obj_diam > self.throat.effective_diameter:
            required = obj_diam / self.throat.base_diameter
            self.throat.stretch(required)
        
        self._update_state()
        return moved
    
    def retract_object(self, amount: float) -> float:
        """Вытянуть объект."""
        if not self.inserted_object:
            return 0.0
        
        new_depth = max(0.0, self.penetration_depth - amount)
        moved = self.penetration_depth - new_depth
        self.penetration_depth = new_depth
        
        # Восстановление дыхания
        if self.penetration_depth < self.throat.length * 0.8:
            self.choking = False
            if self.state == MouthState.CHOKING:
                self.state = MouthState.TENSE
        
        if self.penetration_depth < self.throat.length * 0.3:
            self.gag_triggered = False
            self.throat.open(0.5)
        
        self._update_state()
        return moved
    
    def remove_object(self) -> Optional[Any]:
        """Убрать объект изо рта."""
        if not self.inserted_object:
            return None
        
        obj = self.inserted_object
        self.inserted_object = None
        self.penetration_depth = 0.0
        
        if hasattr(obj, 'is_inserted'):
            obj.is_inserted = False
        
        # Расслабление
        self.throat.open(1.0)
        self.gag_triggered = False
        self.choking = False
        
        self._emit("object_removed", object=obj)
        self._update_state()
        return obj
    
    # ============ STATE MANAGEMENT ============
    
    def _update_state(self):
        """Обновить состояние рта."""
        if self.choking:
            self.state = MouthState.CHOKING
        elif self.gag_triggered:
            self.state = MouthState.GAGGING
        elif self.fill_ratio > 0.9:
            self.state = MouthState.STUFFED
        elif self.fill_ratio > 0.7:
            self.state = MouthState.DISTENDED
        elif self.fill_ratio > 0.3:
            self.state = MouthState.TENSE
        elif self.filled > 0:
            self.state = MouthState.NORMAL
        else:
            self.state = MouthState.EMPTY
    
    def stretch_cheeks(self, ratio: float) -> bool:
        """Раздуть щеки (наполнением)."""
        if ratio > self.max_cheek_stretch:
            return False
        self.cheek_stretch = ratio
        self.current_volume = self.base_volume * (ratio ** 2)
        return True
    
    # ============ TICK ============
    
    def tick(self, dt: float = 1.0) -> Dict[str, Any]:
        """Обновление."""
        # Слюноотделение
        self.produce_saliva(dt)
        
        # Восстановление
        self.lips.relax(dt)
        self.throat.tick(dt)
        
        # Постепенное глотание слюны
        if self.mixture.total() > 20 and self.fill_ratio > 0.5:
            if self.throat.state != ThroatState.CONSTRICTED:
                self.swallow(2.0 * dt)
        
        self._update_state()
        
        return {
            "state": self.state.name,
            "fill_ratio": round(self.fill_ratio, 2),
            "fluid": round(self.mixture.total(), 1),
            "can_breathe": self.can_breathe,
            "gag": self.gag_triggered,
            "depth": round(self.penetration_depth, 1),
            "lips": self.lips.state.name,
            "throat": self.throat.state.name
        }
    
    def get_landmarks(self):
        """Анатомические отметки для пенетрации."""
        from body_sim.systems.advanced_penetration import DepthLandmark, PenetrationDepthZone
        
        return [
            DepthLandmark(
                zone=PenetrationDepthZone.MOUTH_ENTRANCE,
                depth_cm=0,
                min_diameter=0.5,
                max_diameter=self.lips.base_width * self.lips.stretch_ratio,
                resistance_factor=0.3 if self.lips.state != LipState.CLOSED else 0.8,
                description="Вход в рот (губы)"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.MOUTH_CAVITY,
                depth_cm=4.0,
                min_diameter=3.0,
                max_diameter=6.0 * self.cheek_stretch,
                resistance_factor=0.2,
                description="Полость рта"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.OROPHARYNX,
                depth_cm=8.0,
                min_diameter=2.0,
                max_diameter=self.throat.effective_diameter,
                resistance_factor=0.5 if self.throat.state != ThroatState.RELAXED else 0.3,
                description="Небная минда"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.HYPOPHARYNX,
                depth_cm=self.throat.length * 0.7,
                min_diameter=1.5,
                max_diameter=self.throat.effective_diameter * 0.8,
                resistance_factor=0.7,
                description="Глотка (начало рвотного рефлекса)",
                stimulation_bonus=1.5 if not self.gag_triggered else 0.0
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.ESOPHAGUS_ENTRANCE,
                depth_cm=self.throat.length,
                min_diameter=1.2,
                max_diameter=self.throat.effective_diameter * 0.6,
                resistance_factor=0.9,
                description="Вход в пищевод",
                can_pass=self.throat.is_open
            ),
        ]


@dataclass
class MouthSystem:
    """Система ртов (для множественных существ)."""
    mouths: List[Mouth] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.mouths:
            self.mouths.append(Mouth())
    
    @property
    def primary(self) -> Optional[Mouth]:
        return self.mouths[0] if self.mouths else None
    
    def tick(self, dt: float = 1.0):
        for mouth in self.mouths:
            mouth.tick(dt)

# body_sim/anatomy/stomach.py
"""
Желудок с системой инфляции, пенетрации и пищеварения.

Особенности:
- Инфляция как у матки (до 500x растяжения)
- Сфинктер кардии (аналог шейки матки)
- Пенетрация из пищевода/рта
- Хранение и переваривание жидкостей/твердой пищи
- Рефлюкс (обратный поток)
- Растяжение стенок с риском разрыва
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Tuple
from enum import Enum, auto
import math

from body_sim.core.enums import FluidType, StomachState, CardiaState, DigestionState
from body_sim.core.fluids import FluidMixture, BreastFluid
from body_sim.core.constants import UTERUS_MAX_STRETCH, PRESSURE_LEAK_MIN


@dataclass
class StomachWall:
    """Стенка желудка с физическими свойствами."""
    thickness: float = 0.3           # см (тонкая стенка)
    elasticity: float = 0.9          # 0-1 (высокая эластичность желудка)
    integrity: float = 1.0           # 0-1 (целостность)
    stretch_ratio: float = 1.0       # текущее растяжение
    fatigue: float = 0.0             # 0-1 (усталость)
    
    # Для инфляции
    plasticity: float = 0.4          # Пластичность (0-1)
    peak_stretch: float = 1.0        # Пиковое растяжение
    is_permanently_stretched: bool = False
    
    def can_stretch(self, target_ratio: float) -> bool:
        """Может ли растянуться (до 500x)."""
        max_stretch = UTERUS_MAX_STRETCH * self.elasticity * self.integrity
        return target_ratio <= max_stretch
    
    def stretch(self, ratio: float) -> bool:
        """Попытка растяжения до 500x."""
        if ratio > UTERUS_MAX_STRETCH:
            self.integrity = max(0.0, self.integrity - 0.1)
            return False
        
        # При растяжении >100x быстрая потеря целостности
        if ratio > 100.0:
            integrity_loss = (ratio - 100.0) * 0.001
            self.integrity = max(0.01, self.integrity - integrity_loss)
        elif ratio > 10.0:
            integrity_loss = (ratio - 10.0) * 0.0001
            self.integrity = max(0.1, self.integrity - integrity_loss)
        
        self.stretch_ratio = ratio
        self.peak_stretch = max(self.peak_stretch, ratio)
        self.fatigue = min(1.0, self.fatigue + (ratio - 1.0) * 0.01)
        
        if ratio >= 2.0:
            self.is_permanently_stretched = True
        
        return True
    
    def recover(self, dt: float):
        """Восстановление с учётом пластичности."""
        self.fatigue = max(0.0, self.fatigue - 0.005 * dt)
        
        if self.stretch_ratio > 1.0:
            elastic_part = (self.stretch_ratio - 1.0) * (1.0 - self.plasticity)
            plastic_part = (self.stretch_ratio - 1.0) * self.plasticity
            
            recovery = 0.0005 * self.elasticity * dt  # Медленнее чем матка
            new_elastic = max(0, elastic_part - recovery)
            
            self.stretch_ratio = 1.0 + plastic_part + new_elastic
    
    def get_skin_tension(self) -> float:
        """Натяжение стенки (0-1)."""
        if self.stretch_ratio <= 1.0:
            return 0.0
        return min(1.0, (self.stretch_ratio - 1.0) / 3.0)
    
    def get_stretch_marks_risk(self) -> float:
        """Риск растяжек."""
        tension = self.get_skin_tension()
        return tension * tension * (1.0 - self.elasticity)


@dataclass
class Cardia:
    """Сфинктер кардии - вход в желудок из пищевода."""
    diameter: float = 2.5            # см (диаметр)
    max_dilation: float = 10.0       # см (максимальное раскрытие)
    
    state: CardiaState = field(default=CardiaState.CLOSED)
    current_dilation: float = 0.0
    
    # Для инфляции
    inflation_ratio: float = 1.0
    base_dilation: float = 0.1
    
    # Компетентность (сопротивление рефлюксу)
    competence: float = 0.9          # 0-1
    reflux_threshold: float = 0.8    # Давление для рефлюкса
    
    # Соединения
    esophagus_connection: Optional[Any] = field(default=None, repr=False)
    stomach_connection: Optional[Any] = field(default=None, repr=False)
    
    def __post_init__(self):
        self.current_dilation = self.base_dilation
    
    @property
    def is_open(self) -> bool:
        return self.current_dilation > self.base_dilation * 1.5
    
    @property
    def effective_diameter(self) -> float:
        """Эффективный диаметр прохода."""
        return self.current_dilation * self.inflation_ratio
    
    def dilate(self, amount: float) -> bool:
        """Растворение кардии."""
        new_dilation = min(self.current_dilation + amount, self.max_dilation * self.inflation_ratio)
        
        if new_dilation > self.diameter * 0.5:
            self.state = CardiaState.OPEN
        if new_dilation >= self.diameter * 2:
            self.state = CardiaState.DILATED
        
        self.current_dilation = new_dilation
        return True
    
    def contract(self):
        """Сокращение."""
        self.current_dilation = max(self.base_dilation, self.current_dilation - 0.3)
        if self.current_dilation < 0.5:
            self.state = CardiaState.CLOSED
    
    def inflate(self, ratio: float):
        """Инфляция кардии."""
        self.inflation_ratio = max(1.0, min(ratio, 3.0))
        self.diameter *= self.inflation_ratio
        self.max_dilation *= self.inflation_ratio
    
    def check_reflux(self, stomach_pressure: float) -> bool:
        """Проверка на рефлюкс (обратный поток)."""
        if self.competence < 0.3:
            return stomach_pressure > 0.3
        return stomach_pressure > self.reflux_threshold / self.competence


@dataclass
class Stomach:
    """
    Желудок с системой инфляции и пенетрации.
    
    Аналогичен матке, но с:
    - Кислотностью (acid_level)
    - Системой пищеварения
    - Более быстрым восстановлением
    - Рефлюксом в пищевод
    """
    name: str = "stomach"
    
    # Базовые размеры (пустой желудок)
    base_volume: float = 100.0       # мл
    base_length: float = 25.0        # см
    base_width: float = 10.0         # см
    
    # Компоненты
    cardia: Cardia = field(default_factory=Cardia)
    walls: StomachWall = field(default_factory=StomachWall)
    pylorus: Optional[Any] = field(default=None)  # Выход в кишечник
    
    # Состояние
    state: StomachState = field(default=StomachState.EMPTY)
    digestion: DigestionState = field(default=DigestionState.EMPTY)
    
    # Система инфляции (как у матки)
    inflation_ratio: float = 1.0     # Коэффициент инфляции
    
    # Жидкости и содержимое
    mixture: FluidMixture = field(default_factory=FluidMixture)
    solid_content: float = 0.0       # Твердая пища (г)
    acid_level: float = 1.0          # pH фактор (1.0 = нормальная кислотность)
    
    # Пенетрация
    inserted_object: Optional[Any] = field(default=None, repr=False)
    penetration_depth: float = 0.0   # Глубина от кардии
    
    # События
    _listeners: Dict[str, List[Callable]] = field(default_factory=dict)
    
    # Физиология
    peristalsis_strength: float = 0.6
    digestion_rate: float = 1.0      # Скорость переваривания
    emptying_rate: float = 0.5       # Скорость опорожнения в кишечник
    
    def __post_init__(self):
        self.cardia.stomach_connection = self
    
    # ============ EVENTS ============
    
    def on(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)
    
    def _emit(self, event: str, **data):
        for cb in self._listeners.get(event, []):
            cb(self, **data)
    
    # ============ PROPERTIES ============
    
    @property
    def current_volume(self) -> float:
        """Текущий объем с учетом инфляции."""
        stretch_factor = self.inflation_ratio ** 3
        return self.base_volume * stretch_factor * (self.walls.stretch_ratio ** 3)
    
    @property
    def filled(self) -> float:
        """Общий объем содержимого."""
        fluid = self.mixture.total()
        obj_vol = getattr(self.inserted_object, 'volume', 0) if self.inserted_object else 0
        return fluid + obj_vol + self.solid_content
    
    @property
    def available_volume(self) -> float:
        return max(0, self.current_volume - self.filled)
    
    @property
    def fill_ratio(self) -> float:
        return self.filled / self.current_volume if self.current_volume > 0 else 0
    
    @property
    def is_ruptured(self) -> bool:
        return self.state == StomachState.RUPTURED or self.walls.integrity <= 0.05
    
    # ============ INFLATION SYSTEM ============
    
    def inflate(self, ratio: float) -> bool:
        """Инфлировать желудок."""
        if ratio > 4.0:
            self._emit("inflation_limit_reached", ratio=ratio)
            return False
        
        old_ratio = self.inflation_ratio
        self.inflation_ratio = ratio
        
        # Обновляем размеры
        self.cardia.inflate(ratio)
        
        self._update_state()
        
        if ratio > old_ratio:
            self._emit("inflated", old_ratio=old_ratio, new_ratio=ratio)
        
        return True
    
    def _update_state(self):
        """Обновить статус инфляции."""
        total_stretch = self.inflation_ratio * self.walls.stretch_ratio
        
        if total_stretch < 1.3:
            self.state = StomachState.NORMAL if self.filled > 0 else StomachState.EMPTY
        elif total_stretch < 2.0:
            self.state = StomachState.FILLED
        elif total_stretch < 3.0:
            self.state = StomachState.DISTENDED
        elif total_stretch < 4.0:
            self.state = StomachState.HYPERDISTENDED
        elif total_stretch < 8.0:
            self.state = StomachState.OVERSTUFFED
        elif total_stretch < 500.0:
            self.state = StomachState.RUPTURE_RISK
        else:
            self.state = StomachState.RUPTURED
            self._emit("ruptured", stretch=total_stretch)
    
    # ============ FLUID MANAGEMENT ============
    
    def add_fluid(self, fluid: 'FluidType | BreastFluid', amount: float) -> float:
        """Добавить жидкость с автоматическим растяжением."""
        if amount <= 0 or self.is_ruptured:
            return 0.0
        
        fluid_type = fluid.fluid_type if isinstance(fluid, BreastFluid) else fluid
        remaining = amount
        total_added = 0.0
        
        # Попытка добавить без растяжения
        available = self.available_volume
        if available > 0:
            add_now = min(remaining, available)
            self.mixture.add(fluid_type, add_now)
            total_added += add_now
            remaining -= add_now
        
        # Авто-растяжение если нужно
        if remaining > 0:
            needed_ratio = ((self.filled + remaining) / self.base_volume) ** (1/3)
            needed_ratio = min(needed_ratio, UTERUS_MAX_STRETCH)
            
            if needed_ratio > self.inflation_ratio * self.walls.stretch_ratio:
                # Пробуем инфлировать
                if self.inflation_ratio < 4.0:
                    target_inf = min(needed_ratio / self.walls.stretch_ratio, 4.0)
                    if target_inf > self.inflation_ratio:
                        self.inflate(target_inf)
                
                # Пробуем растянуть стенки
                target_stretch = needed_ratio / self.inflation_ratio
                if target_stretch > self.walls.stretch_ratio:
                    self.walls.stretch(min(target_stretch, UTERUS_MAX_STRETCH))
                
                # Добавляем что влезло
                available = self.available_volume
                if available > 0:
                    add_now = min(remaining, available)
                    self.mixture.add(fluid_type, add_now)
                    total_added += add_now
                    remaining -= add_now
        
        self._update_state()
        if total_added > 0:
            self._emit("fluid_added", amount=total_added, overflow=remaining)
        
        return total_added
    
    def remove_fluid(self, amount: float) -> float:
        """Удалить жидкость (рефлюкс/опорожнение)."""
        if amount <= 0:
            return 0.0
        actual = min(amount, self.mixture.total())
        self.mixture.remove(actual)
        self._update_state()
        return actual
    
    def drain_all(self) -> Dict['FluidType', float]:
        """Полное опорожнение."""
        removed = dict(self.mixture.components)
        total = sum(removed.values())
        self.mixture.components.clear()
        self.solid_content = 0.0
        self._emit("drained", amount=total)
        self._update_state()
        return removed
    
    def add_solid(self, amount: float) -> float:
        """Добавить твердую пищу."""
        space = self.available_volume
        actual = min(amount, space)
        self.solid_content += actual
        self._update_state()
        return actual
    
    # ============ PENETRATION SYSTEM ============
    
    def receive_from_esophagus(self, obj: Any, force: bool = False) -> bool:
        """Принять объект из пищевода (пенетрация)."""
        obj_diameter = getattr(obj, 'diameter', 0) or getattr(obj, 'effective_diameter', 0)
        
        # Открываем кардию
        if obj_diameter > self.cardia.effective_diameter:
            if not force:
                return False
            self.cardia.dilate(obj_diameter - self.cardia.effective_diameter)
        else:
            self.cardia.dilate(obj_diameter * 0.5)
        
        # Проверяем объем
        obj_volume = getattr(obj, 'volume', 0) or getattr(obj, 'effective_volume', 0)
        if obj_volume > self.available_volume:
            # Пытаемся растянуться
            needed = ((self.filled + obj_volume) / self.base_volume) ** (1/3)
            if not self.walls.can_stretch(needed / self.inflation_ratio):
                if not force:
                    return False
            self.walls.stretch(needed / self.inflation_ratio)
        
        self.inserted_object = obj
        self.penetration_depth = 0.0
        if hasattr(obj, 'is_inserted'):
            obj.is_inserted = True
        
        self._emit("object_inserted", object=obj)
        self._update_state()
        return True
    
    def advance_object(self, depth: float) -> float:
        """Продвинуть объект глубже в желудок."""
        if not self.inserted_object:
            return 0.0
        
        max_depth = self.base_length * self.inflation_ratio
        new_depth = min(self.penetration_depth + depth, max_depth)
        moved = new_depth - self.penetration_depth
        self.penetration_depth = new_depth
        
        # Если дошли до дна, можно выйти через пилорус (если открыт)
        if self.penetration_depth >= max_depth * 0.9 and self.pylorus:
            pass  # Логика выхода в кишечник
        
        return moved
    
    def remove_object(self) -> Optional[Any]:
        """Извлечь объект (обратно в пищевод)."""
        if not self.inserted_object:
            return None
        
        obj = self.inserted_object
        self.inserted_object = None
        self.penetration_depth = 0.0
        
        if hasattr(obj, 'is_inserted'):
            obj.is_inserted = False
        
        self.cardia.contract()
        self._emit("object_removed", object=obj)
        self._update_state()
        return obj
    
    # ============ DIGESTION ============
    
    def tick(self, dt: float = 1.0) -> Dict[str, Any]:
        """Обновление состояния."""
        if self.is_ruptured:
            return {"state": "RUPTURED", "integrity": self.walls.integrity}
        
        # 1. Восстановление стенок
        self.walls.recover(dt)
        
        # 2. Пищеварение
        if self.solid_content > 0:
            digested = self.solid_content * self.digestion_rate * 0.1 * dt
            self.solid_content -= digested
            # Переваренная пища становится жидкостью (chyme)
            if digested > 0:
                self.mixture.add(FluidType.CHYLE, digested)  # Химус
        
        # 3. Перистальтика и опорожнение
        if self.fill_ratio > 0.1 and self.pylorus:
            empty_amount = self.mixture.total() * self.emptying_rate * 0.05 * dt
            if empty_amount > 0:
                # В кишечник
                emptied = self.pylorus.receive_fluid(
                    dict(self.mixture.components), empty_amount
                )
                self.mixture.remove(emptied)
        
        # 4. Проверка рефлюкса
        pressure = self.pressure()
        if self.cardia.check_reflux(pressure):
            reflux_amount = (pressure - self.cardia.reflux_threshold) * 2.0 * dt
            if reflux_amount > 0:
                fluids = dict(self.mixture.components)
                for ftype, famount in fluids.items():
                    reflux_vol = min(famount, reflux_amount * (famount / sum(fluids.values())))
                    if reflux_vol > 0:
                        self.mixture.remove(reflux_vol)
                        # В пищевод
                        if self.cardia.esophagus_connection:
                            self.cardia.esophagus_connection.receive_reflux(ftype, reflux_vol)
                        self._emit("reflux", amount=reflux_vol, fluid=ftype)
        
        # 5. Обновление состояния
        self._update_state()
        
        # Закрытие кардии
        if self.fill_ratio < 0.5 and not self.inserted_object:
            self.cardia.contract()
        
        return {
            "state": self.state.name,
            "fill_ratio": round(self.fill_ratio, 2),
            "fluid": round(self.mixture.total(), 1),
            "solid": round(self.solid_content, 1),
            "pressure": round(pressure, 2),
            "integrity": round(self.walls.integrity, 2),
            "stretch": round(self.walls.stretch_ratio, 2),
            "inflation": round(self.inflation_ratio, 2)
        }
    
    def pressure(self) -> float:
        """Давление в желудке."""
        if self.filled <= 0:
            return 0.0
        
        fill_ratio = self.fill_ratio
        pressure = fill_ratio * 1.5  # Меньше чем в матке
        
        # Кислота увеличивает давление
        pressure *= (1.0 + self.acid_level * 0.2)
        
        # Эластичность
        elasticity_factor = 1.0 / max(0.1, self.walls.elasticity)
        pressure *= elasticity_factor
        
        # Инфляция снижает давление
        inflation_mod = 1.0 / (self.inflation_ratio ** 0.5)
        pressure *= inflation_mod
        
        # Растяжение
        stretch_penalty = (self.walls.stretch_ratio - 1.0) * 0.2
        pressure += stretch_penalty
        
        return pressure
    
    def get_landmarks(self):
        """Анатомические отметки для пенетрации."""
        from body_sim.systems.advanced_penetration import DepthLandmark, PenetrationDepthZone
        
        return [
            DepthLandmark(
                zone=PenetrationDepthZone.CARDIA,
                depth_cm=0,
                min_diameter=self.cardia.base_dilation,
                max_diameter=self.cardia.max_dilation * self.cardia.inflation_ratio,
                resistance_factor=0.6 if self.cardia.state == CardiaState.CLOSED else 0.2,
                description="Сфинктер кардии (вход в желудок)",
                can_pass=self.cardia.is_open
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.FUNDUS,
                depth_cm=self.base_length * 0.3 * self.inflation_ratio,
                min_diameter=5.0,
                max_diameter=self.base_width * self.inflation_ratio * 2,
                resistance_factor=0.3,
                description="Дно желудка"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.BODY_STOMACH,
                depth_cm=self.base_length * 0.6 * self.inflation_ratio,
                min_diameter=4.0,
                max_diameter=self.base_width * self.inflation_ratio * 3,
                resistance_factor=0.2,
                description="Тело желудка"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.ANTUM,
                depth_cm=self.base_length * 0.9 * self.inflation_ratio,
                min_diameter=3.0,
                max_diameter=self.base_width * self.inflation_ratio * 2,
                resistance_factor=0.4,
                description="Препилорический отдел"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.PYLORUS,
                depth_cm=self.base_length * self.inflation_ratio,
                min_diameter=0.5,
                max_diameter=2.0,
                resistance_factor=0.9,
                description="Сфинктер пилорус (выход в двенадцатиперстную кишку)",
                can_pass=False  # Обычно закрыт
            ),
        ]


@dataclass
class StomachSystem:
    """Система желудков."""
    stomachs: List[Stomach] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.stomachs:
            self.stomachs.append(Stomach())
    
    @property
    def primary(self) -> Optional[Stomach]:
        return self.stomachs[0] if self.stomachs else None
    
    def tick(self, dt: float = 1.0):
        for stomach in self.stomachs:
            stomach.tick(dt)

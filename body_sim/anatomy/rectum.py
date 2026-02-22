# body_sim/anatomy/rectum.py
"""
Прямая кишка (rectum) и сигмовидная колонка.
Соединяет анус с желудком для глубокой пенетрации.

Особенности:
- Система растяжения как у фаллопиевых труб
- Перистальтика (обратная - в сторону желудка)
- Хранение/транспорт содержимого
- Соединение с сфинктером пилоруса (задний вход в желудок)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Tuple
from enum import Enum, auto
import math

from body_sim.core.enums import FluidType, RectumState, PenetrationDepthZone
from body_sim.core.fluids import FluidMixture


@dataclass
class RectalWall:
    """Стенка прямой кишки."""
    thickness: float = 0.2           # см (тонкая)
    elasticity: float = 0.7
    integrity: float = 1.0
    stretch_ratio: float = 1.0
    fatigue: float = 0.0
    is_permanently_stretched: bool = False
    
    def stretch(self, ratio: float, max_stretch: float = 10.0) -> bool:
        if ratio > max_stretch:
            self.integrity -= 0.05
            return False
        self.stretch_ratio = ratio
        if ratio > 3.0:
            self.is_permanently_stretched = True
        self.fatigue = min(1.0, self.fatigue + (ratio - 1.0) * 0.05)
        return True
    
    def recover(self, dt: float):
        self.fatigue = max(0.0, self.fatigue - 0.02 * dt)
        if self.stretch_ratio > 1.0 and not self.is_permanently_stretched:
            self.stretch_ratio = max(1.0, self.stretch_ratio - 0.005 * dt)


@dataclass
class Rectum:
    """
    Прямая кишка соединяющая анус с желудком/кишечником.
    Аналогична FallopianTube но для нижнего отдела ЖКТ.
    """
    name: str = "rectum"
    
    # Размеры
    base_length: float = 15.0        # см
    base_diameter: float = 3.0       # см (расширенная часть)
    anal_canal_length: float = 4.0   # см (анальный канал)
    
    # Текущие размеры
    current_length: float = field(init=False)
    current_diameter: float = field(init=False)
    
    # Состояние
    state: RectumState = field(default=RectumState.EMPTY)
    wall: RectalWall = field(default_factory=RectalWall)
    
    # Растяжение/инфляция
    stretch_ratio: float = 1.0
    inflation_ratio: float = 1.0
    
    # Жидкость/содержимое
    fluid_content: float = 0.0
    max_capacity: float = 150.0      # мл
    mixture: FluidMixture = field(default_factory=FluidMixture)
    
    # Соединения
    anus_connection: Optional[Any] = field(default=None, repr=False)
    stomach_connection: Optional[Any] = field(default=None, repr=False)  # Для глубокой пенетрации
    colon_connection: Optional[Any] = field(default=None, repr=False)
    
    # Пенетрация
    inserted_object: Optional[Any] = field(default=None, repr=False)
    penetration_depth: float = 0.0   # Глубина от ануса
    
    # События
    _listeners: Dict[str, List[Callable]] = field(default_factory=dict)
    
    def __post_init__(self):
        self.current_length = self.base_length
        self.current_diameter = self.base_diameter
    
    def on(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)
    
    def _emit(self, event: str, **data):
        for cb in self._listeners.get(event, []):
            cb(self, **data)
    
    @property
    def total_length(self) -> float:
        """Общая длина с учетом растяжения."""
        return (self.base_length + self.anal_canal_length) * self.stretch_ratio
    
    @property
    def effective_diameter(self) -> float:
        return self.current_diameter * self.inflation_ratio * (self.wall.stretch_ratio ** 0.5)
    
    @property
    def filled(self) -> float:
        fluid = self.mixture.total()
        obj_vol = getattr(self.inserted_object, 'volume', 0) if self.inserted_object else 0
        return fluid + obj_vol
    
    @property
    def available_volume(self) -> float:
        return self.max_capacity * (self.inflation_ratio ** 2) - self.filled
    
    @property
    def fill_ratio(self) -> float:
        capacity = self.max_capacity * (self.inflation_ratio ** 2)
        return self.filled / capacity if capacity > 0 else 0
    
    # ============ PENETRATION SYSTEM ============
    
    def insert_object(self, obj: Any) -> bool:
        """Вставить объект через анус."""
        obj_diameter = getattr(obj, 'diameter', 0) or getattr(obj, 'effective_diameter', 0)
        
        # Проверяем диаметр
        if obj_diameter > self.effective_diameter:
            required_stretch = obj_diameter / self.base_diameter
            if not self.wall.stretch(required_stretch):
                return False
            self.current_diameter = self.base_diameter * required_stretch
        
        self.inserted_object = obj
        self.penetration_depth = 0.0
        if hasattr(obj, 'is_inserted'):
            obj.is_inserted = True
        
        self._update_state()
        self._emit("object_inserted", object=obj)
        return True
    
    def advance_object(self, depth: float) -> Tuple[float, bool]:
        """
        Продвинуть объект глубже к желудку.
        
        Returns:
            (продвинуто_см, достигнут_желудок)
        """
        if not self.inserted_object:
            return 0.0, False
        
        current_total = self.total_length
        new_depth = self.penetration_depth + depth
        
        # Проверяем достижение желудка
        reached_stomach = False
        if new_depth >= current_total and self.stomach_connection:
            # Переход в желудок
            excess = new_depth - current_total
            if self.stomach_connection.receive_from_rectum(self.inserted_object):
                self._emit("entered_stomach", object=self.inserted_object)
                self.inserted_object = None
                self.penetration_depth = 0.0
                return depth - excess, True
        
        actual_move = min(depth, current_total - self.penetration_depth)
        self.penetration_depth += actual_move
        
        # Растяжение при продвижении
        obj_diam = getattr(self.inserted_object, 'diameter', 2.0)
        if obj_diam > self.current_diameter * 0.8:
            new_stretch = (obj_diam / self.base_diameter) * 1.2
            if new_stretch > self.wall.stretch_ratio:
                self.wall.stretch(new_stretch)
                self.current_diameter = self.base_diameter * new_stretch
        
        self._update_state()
        return actual_move, False
    
    def retract_object(self, amount: float) -> float:
        """Вытянуть объект наружу."""
        if not self.inserted_object:
            return 0.0
        
        new_depth = max(0.0, self.penetration_depth - amount)
        moved = self.penetration_depth - new_depth
        self.penetration_depth = new_depth
        
        # Если вышли полностью
        if self.penetration_depth <= 0:
            pass  # Объект еще в rectum, но у входа
        
        return moved
    
    def remove_object(self) -> Optional[Any]:
        """Извлечь объект полностью."""
        if not self.inserted_object:
            return None
        
        obj = self.inserted_object
        self.inserted_object = None
        self.penetration_depth = 0.0
        
        if hasattr(obj, 'is_inserted'):
            obj.is_inserted = False
        
        self._emit("object_removed", object=obj)
        self._update_state()
        return obj
    
    def receive_from_stomach(self, obj: Any) -> bool:
        """Принять объект из желудка (обратное движение)."""
        if self.inserted_object is not None:
            return False
        self.inserted_object = obj
        self.penetration_depth = self.total_length  # У границы с желудком
        self._update_state()
        return True
    
    # ============ FLUID MANAGEMENT ============
    
    def add_fluid(self, fluid_type: FluidType, amount: float) -> float:
        """Добавить жидкость."""
        available = self.available_volume
        actual = min(amount, available)
        if actual > 0:
            self.mixture.add(fluid_type, actual)
        self._update_state()
        return actual
    
    def transfer_to_stomach(self, amount: float) -> float:
        """Передать жидкость в желудок."""
        if not self.stomach_connection:
            return 0.0
        
        available = self.mixture.total()
        transfer = min(amount, available)
        if transfer <= 0:
            return 0.0
        
        fluids = dict(self.mixture.components)
        transferred = self.stomach_connection.add_fluid(
            max(fluids.items(), key=lambda x: x[1])[0], transfer
        )
        self.mixture.remove(transferred)
        self._update_state()
        return transferred
    
    def _update_state(self):
        """Обновить состояние."""
        if self.filled <= 0:
            self.state = RectumState.EMPTY
        elif self.fill_ratio > 0.9:
            self.state = RectumState.FULL
        elif self.wall.stretch_ratio > 2.0:
            self.state = RectumState.STRETCHED
        elif self.fill_ratio > 0.5:
            self.state = RectumState.DISTENDED
        else:
            self.state = RectumState.NORMAL
    
    def tick(self, dt: float = 1.0) -> Dict[str, Any]:
        """Обновление."""
        self.wall.recover(dt)
        
        # Автоматическая передача в желудок при заполнении
        if self.fill_ratio > 0.8 and self.stomach_connection:
            self.transfer_to_stomach(self.mixture.total() * 0.1 * dt)
        
        return {
            "state": self.state.name,
            "fill_ratio": round(self.fill_ratio, 2),
            "stretch": round(self.wall.stretch_ratio, 2),
            "diameter": round(self.effective_diameter, 1),
            "depth": round(self.penetration_depth, 1),
            "length": round(self.total_length, 1)
        }
    
    def get_landmarks(self):
        """Анатомические отметки для пенетрации."""
        from body_sim.systems.advanced_penetration import DepthLandmark, PenetrationDepthZone
        
        return [
            DepthLandmark(
                zone=PenetrationDepthZone.ANAL_CANAL,
                depth_cm=0,
                min_diameter=1.5,
                max_diameter=self.base_diameter * 0.6 * self.wall.stretch_ratio,
                resistance_factor=0.7,
                description="Анальный канал (сфинктер)"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.RECTAL_AMPULLA,
                depth_cm=self.anal_canal_length,
                min_diameter=3.0,
                max_diameter=self.base_diameter * self.inflation_ratio * 3,
                resistance_factor=0.3,
                description="Ректальная ампула"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.RECTUM_BODY,
                depth_cm=self.anal_canal_length + self.base_length * 0.3,
                min_diameter=2.5,
                max_diameter=self.effective_diameter * 2,
                resistance_factor=0.4,
                description="Тело прямой кишки"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.SIGMOID_COLON,
                depth_cm=self.anal_canal_length + self.base_length * 0.8,
                min_diameter=2.0,
                max_diameter=self.effective_diameter * 1.5,
                resistance_factor=0.6,
                description="Сигмовидная колонка (переход к желудку)"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.COLON_STOMACH_JUNCTION,
                depth_cm=self.total_length,
                min_diameter=1.0,
                max_diameter=8.0,  # Растянутый пилорус
                resistance_factor=0.8,
                description="Вход в желудок (через пилорус)",
                can_pass=self.stomach_connection is not None
            ),
        ]


@dataclass
class RectumSystem:
    """Система прямой кишки."""
    rectums: List[Rectum] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.rectums:
            self.rectums.append(Rectum())
    
    @property
    def primary(self) -> Optional[Rectum]:
        return self.rectums[0] if self.rectums else None
    
    def tick(self, dt: float = 1.0):
        for rectum in self.rectums:
            rectum.tick(dt)

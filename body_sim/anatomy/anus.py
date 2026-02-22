# body_sim/anatomy/anus.py
"""
Анус - задний проход с системой глубокой пенетрации.
Связан с прямой кишкой (rectum) которая ведет к желудку.
"""
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List, Callable, Tuple
from enum import Enum, auto

from body_sim.core.enums import AnusType, FluidType, AnalSphincterState
from body_sim.core.fluids import FluidMixture



@dataclass
class AnalCanal:
    """Анальный канал (внутренняя часть)."""
    length: float = 4.0              # см
    base_diameter: float = 2.0       # см в расслабленном состоянии
    max_diameter: float = 8.0        # см предел растяжения
    
    current_diameter: float = field(init=False)
    stretch_ratio: float = 1.0
    
    def __post_init__(self):
        self.current_diameter = self.base_diameter
    
    def stretch(self, ratio: float) -> bool:
        if ratio > 5.0:  # Лимит анального канала
            return False
        self.stretch_ratio = ratio
        self.current_diameter = self.base_diameter * ratio
        return True


@dataclass
class Anus:
    """
    Анус с полной системой пенетрации.
    Является входом в rectum который соединяется с желудком.
    """
    name: str = "anus"
    anus_type: AnusType = AnusType.AVERAGE
    
    # Основные параметры
    base_diameter: float = 2.5
    max_diameter: float = 12.0       # Увеличен для extreme penetration
    sphincter_tone: float = 0.7      # 0-1 (0 = полностью расслаблен)
    
    # Канал
    canal: AnalCanal = field(default_factory=AnalCanal)
    sphincter_state: AnalSphincterState = field(default=AnalSphincterState.CLOSED)
    
    # Состояние
    is_gaping: bool = False
    gaping_size: float = 0.0
    prolapse_degree: float = 0.0     # Выпадение (0-1)
    
    # Соединение
    rectum_connection: Optional[Any] = field(default=None, repr=False)
    
    # Текущий объект
    inserted_object: Optional[Any] = field(default=None, repr=False)
    penetration_depth: float = 0.0   # Текущая глубина
    
    # Жидкость (для lubrication/заглатывания)
    fluid_content: float = 0.0
    mixture: FluidMixture = field(default_factory=FluidMixture)
    
    # События
    _listeners: Dict[str, List[Callable]] = field(default_factory=dict)
    
    # Физиология
    pain_tolerance: float = 0.6      # Болевой порог
    pleasure_sensitivity: float = 0.8
    
    def on(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)
    
    def _emit(self, event: str, **data):
        for cb in self._listeners.get(event, []):
            cb(self, **data)
    
    @property
    def current_diameter(self) -> float:
        """Эффективный диаметр отверстия."""
        if self.is_gaping:
            return self.gaping_size
        base = self.base_diameter * (1 - self.sphincter_tone * 0.6)
        return base * self.canal.stretch_ratio
    
    @property
    def can_hold(self) -> bool:
        """Может ли удерживать содержимое."""
        return self.sphincter_tone > 0.3 and not self.is_gaping and self.prolapse_degree < 0.5
    
    @property
    def total_depth_available(self) -> float:
        """Общая доступная глубина до желудка."""
        total = self.canal.length
        if self.rectum_connection:
            total += self.rectum_connection.total_length
        return total
    
    # ============ SPHINCTER CONTROL ============
    
    def relax(self, amount: float = 0.2) -> None:
        """Расслабить сфинктер."""
        old_tone = self.sphincter_tone
        self.sphincter_tone = max(0.0, self.sphincter_tone - amount)
        
        if self.sphincter_tone < 0.2:
            self.sphincter_state = AnalSphincterState.RELAXED
        elif self.sphincter_tone < 0.5:
            self.sphincter_state = AnalSphincterState.SLIGHTLY_OPEN
        
        if old_tone != self.sphincter_tone:
            self._emit("relaxed", tone=self.sphincter_tone)
    
    def contract(self, amount: float = 0.15) -> None:
        """Сжать сфинктер."""
        self.sphincter_tone = min(1.0, self.sphincter_tone + amount)
        if self.sphincter_tone > 0.7:
            self.sphincter_state = AnalSphincterState.CLOSED
            self.is_gaping = False
    
    def stretch(self, diameter: float) -> bool:
        """
        Растянуть анус до определенного диаметра.
        """
        if diameter > self.max_diameter:
            self._emit("stretch_failed", requested=diameter, max=self.max_diameter)
            return False
        
        required_ratio = diameter / self.base_diameter
        
        # Растягиваем канал
        if not self.canal.stretch(required_ratio):
            return False
        
        self.is_gaping = True
        self.gaping_size = diameter
        self.sphincter_state = AnalSphincterState.STRETCHED
        
        # Автоматическое расслабление при большом растяжении
        if required_ratio > 2.0:
            self.sphincter_tone = max(0.1, self.sphincter_tone - 0.3)
        
        self._emit("stretched", diameter=diameter, ratio=required_ratio)
        return True
    
    def close(self) -> None:
        """Закрыть анус."""
        self.is_gaping = False
        self.gaping_size = 0.0
        self.canal.stretch_ratio = 1.0
        self.canal.current_diameter = self.canal.base_diameter
        self.sphincter_tone = min(1.0, self.sphincter_tone + 0.4)
        self.sphincter_state = AnalSphincterState.CLOSED
    
    def prolapse(self, degree: float = 0.5):
        """Выпадение прямой кишки."""
        self.prolapse_degree = min(1.0, self.prolapse_degree + degree)
        if self.prolapse_degree > 0.3:
            self.sphincter_state = AnalSphincterState.PROLAPSED
            self.is_gaping = True
            self.gaping_size = self.base_diameter * (1 + self.prolapse_degree)
    
    def reposition(self, amount: float = 0.3) -> bool:
        """Вправить выпадение."""
        if self.prolapse_degree > 0.7 and amount < 0.5:
            return False
        self.prolapse_degree = max(0.0, self.prolapse_degree - amount)
        if self.prolapse_degree < 0.2:
            if not self.is_gaping:
                self.sphincter_state = AnalSphincterState.CLOSED
        return True
    
    # ============ PENETRATION SYSTEM ============
    
    def insert_object(self, obj: Any, force: bool = False) -> bool:
        """
        Вставить объект в анус.
        Проверяет диаметр, растягивает если нужно, передает в rectum.
        """
        obj_diameter = getattr(obj, 'diameter', 0) or getattr(obj, 'effective_diameter', 0)
        obj_volume = getattr(obj, 'volume', 0) or getattr(obj, 'effective_volume', 0)
        
        # Проверка диаметра
        if obj_diameter > self.current_diameter:
            if not force:
                return False
            if not self.stretch(obj_diameter):
                return False
        
        # Проверяем соединение с rectum
        if self.rectum_connection:
            if not self.rectum_connection.insert_object(obj):
                return False
        else:
            # Локальное хранение если нет соединения
            self.inserted_object = obj
            if hasattr(obj, 'is_inserted'):
                obj.is_inserted = True
        
        self.penetration_depth = 0.0
        self.sphincter_state = AnalSphincterState.GAPING
        
        self._emit("penetration_started", object=obj, diameter=obj_diameter)
        return True
    
    def advance_object(self, depth: float) -> Tuple[float, bool, str]:
        """
        Продвинуть объект глубже.
        
        Returns:
            (продвинуто_см, достигнут_конец_зоны, название_зоны)
        """
        if not self.rectum_connection or not self.rectum_connection.inserted_object:
            return 0.0, False, "none"
        
        # Движение через анальный канал (первые 4см)
        canal_remaining = self.canal.length - self.penetration_depth
        
        if canal_remaining > 0:
            # Движение по каналу
            move = min(depth, canal_remaining)
            self.penetration_depth += move
            remaining = depth - move
            
            if remaining <= 0:
                return depth, False, "anal_canal"
            
            # Переход в rectum
            depth = remaining
        
        # Движение в rectum
        if self.rectum_connection:
            moved, reached_stomach = self.rectum_connection.advance_object(depth)
            
            if reached_stomach:
                self._emit("reached_stomach", object=self.rectum_connection.inserted_object)
                return depth, True, "stomach"
            
            if self.penetration_depth >= self.canal.length:
                zone = "rectum"
                if self.rectum_connection.penetration_depth > self.rectum_connection.base_length * 0.8:
                    zone = "sigmoid"
                return depth, False, zone
        
        return depth, False, "unknown"
    
    def retract_object(self, amount: float) -> Tuple[float, bool]:
        """Вытянуть объект наружу."""
        if not self.rectum_connection or not self.rectum_connection.inserted_object:
            # Локальное извлечение
            if self.inserted_object:
                self.inserted_object = None
                self.penetration_depth = 0.0
                return amount, True
            return 0.0, False
        
        # Сначала из rectum
        if self.rectum_connection.penetration_depth > 0:
            rectum_retract = min(amount, self.rectum_connection.penetration_depth)
            moved = self.rectum_connection.retract_object(rectum_retract)
            remaining = amount - moved
            
            if remaining <= 0:
                return amount, False
            
            amount = remaining
        
        # Затем по каналу
        if self.penetration_depth > 0:
            canal_retract = min(amount, self.penetration_depth)
            self.penetration_depth -= canal_retract
            remaining = amount - canal_retract
            
            if self.penetration_depth <= 0:
                # Объект у входа
                return amount - remaining, True
        
        return amount, False
    
    def remove_object(self) -> Optional[Any]:
        """Полностью извлечь объект."""
        if self.rectum_connection and self.rectum_connection.inserted_object:
            obj = self.rectum_connection.remove_object()
            self.penetration_depth = 0.0
            self.close()
            self._emit("object_removed", object=obj)
            return obj
        
        if self.inserted_object:
            obj = self.inserted_object
            self.inserted_object = None
            self.penetration_depth = 0.0
            self.close()
            self._emit("object_removed", object=obj)
            return obj
        
        return None
    
    def get_current_object(self) -> Optional[Any]:
        """Получить текущий вставленный объект."""
        if self.rectum_connection:
            return self.rectum_connection.inserted_object
        return self.inserted_object
    
    # ============ FLUID ============
    
    def add_fluid(self, fluid_type: FluidType, amount: float) -> float:
        """Добавить жидкость (например, enema)."""
        # Передаем в rectum если есть соединение
        if self.rectum_connection:
            return self.rectum_connection.add_fluid(fluid_type, amount)
        
        available = self.max_diameter * 2 - self.fluid_content  # Условный объем
        actual = min(amount, available)
        self.fluid_content += actual
        self.mixture.add(fluid_type, actual)
        return actual
    
    # ============ TICK ============
    
    def tick(self, dt: float = 1.0) -> None:
        """Обновление физиологии."""
        # Постепенное восстановление тонуса
        if not self.get_current_object() and not self.is_gaping:
            self.sphincter_tone = min(0.7, self.sphincter_tone + 0.01 * dt)
            if self.sphincter_tone > 0.6 and self.sphincter_state == AnalSphincterState.RELAXED:
                self.sphincter_state = AnalSphincterState.CLOSED
        
        # Снижение растяжения канала
        if not self.get_current_object() and self.canal.stretch_ratio > 1.0:
            self.canal.stretch_ratio = max(1.0, self.canal.stretch_ratio - 0.01 * dt)
            self.canal.current_diameter = self.canal.base_diameter * self.canal.stretch_ratio
        
        # Обновление rectum
        if self.rectum_connection:
            self.rectum_connection.tick(dt)
    
    def get_status(self) -> Dict[str, Any]:
        """Статус для UI."""
        obj = self.get_current_object()
        return {
            "sphincter_tone": round(self.sphincter_tone, 2),
            "state": self.sphincter_state.name,
            "diameter": round(self.current_diameter, 1),
            "prolapse": round(self.prolapse_degree, 2),
            "depth": round(self.penetration_depth, 1),
            "total_depth": round(self.total_depth_available, 1),
            "has_object": obj is not None,
            "object_name": getattr(obj, 'name', str(obj)) if obj else None
        }

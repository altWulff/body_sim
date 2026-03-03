# anatomy/breasts.py

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus, EventType
from body_sim.core.fluids import FluidMixture, FluidType
from body_sim.systems.inflation import InflationSystem, InflationProfile
from body_sim.systems.lactation import LactationSystem, LactationProfile
from body_sim.systems.insertion import InsertionManager
from body_sim.systems.physics import PhysicsEngine
from body_sim.systems.pressure import PressureController

class CupSize(Enum):
    """Размеры груди."""
    AAA = 120; AA = 150; A = 180; B = 240; C = 310; D = 400; DD = 520
    E = 650; F = 800; G = 1000; H = 1250; I = 1550; J = 1900
    K = 2300; L = 2800; M = 3500; N = 4500; O = 6000; P = 8000
    Q = 12000; R = 18000; S = 28000; T = 45000; U = 75000
    V = 120000; W = 200000; X = 350000; Y = 600000; Z = 1000000
    
    @property
    def base_volume(self):
        return self.value


@dataclass
class NippleState:
    """Состояние соска."""
    diameter: float = 1.0  # см
    length: float = 0.8    # см
    gape_diameter: float = 0.0  # <-- Исправлено с 'gape' на 'gape_diameter'
    is_erect: bool = False
    is_open: bool = False
    sensitivity: float = 1.5
    
    def open(self, amount: Optional[float] = None):
        target = amount if amount is not None else self.diameter * 0.5
        self.gape_diameter = min(target, self.diameter)
        self.is_open = self.gape_diameter > 0.01
        
    def close(self):
        self.gape_diameter = 0.0
        self.is_open = False


@dataclass
class Areola:
    """Ареола с сосками."""
    diameter: float = 4.0
    color: str = "pink"
    nipples: List[NippleState] = field(default_factory=lambda: [NippleState()])
    
    def stimulate(self, intensity: float = 1.0):
        for nipple in self.nipples:
            nipple.is_erect = True
            
    def relax(self):
        for nipple in self.nipples:
            nipple.is_erect = False

class BreastComponent(AnatomicalComponent):
    """
    Компонент груди BodySim 2.0 с полной физикой.
    """
    
    PRESSURE_NORMAL = 0.5
    PRESSURE_TENSE = 1.0
    PRESSURE_LEAK = 0.8
    
    def __init__(self, name: str, cup_size: CupSize = CupSize.C, side: str = "left"):
        base_vol = cup_size.base_volume
        
        # Инициализируем базовый класс
        super().__init__(name, base_volume=base_vol, max_volume_multiplier=1.5)
        
        self.cup_size = cup_size
        self.side = side
        self._dynamic_cup = cup_size
        
        # Анатомия
        self.areola = Areola()
        
        # Системы
        self.inflation = InflationSystem(InflationProfile(
            max_stretch=3.0,
            plasticity=0.3,
            base_elasticity=1.0
        ))
        self.lactation = LactationSystem(LactationProfile())
        self.insertion = InsertionManager()
        self.pressure_controller = PressureController()
        
        # Переопределяем max_volume с учетом инфляции
        self._max_volume = base_vol * 1.5
        self.max_capacity = self._max_volume
        
        # Состояние
        self._state = "normal"
        self._auto_inflate = True
        self._sag = 0.0
        
        # Жидкости (уже есть в AnatomicalComponent, но убедимся)
        if not hasattr(self, 'mixture'):
            self.mixture = FluidMixture()
    
    @property
    def filled(self) -> float:
        """Текущее количество жидкости."""
        return self.mixture.total()
    
    @property
    def volume(self) -> float:
        """Текущий общий объем."""
        return self.current_volume
    
    @property
    def current_volume(self) -> float:
        """Общий текущий объем."""
        fluid_volume = self.mixture.total()
        objects_volume = self.insertion.total_volume
        
        stretch = self.inflation.profile.stretch_ratio
        tissue_volume = self._base_volume * stretch
        
        return tissue_volume + fluid_volume + objects_volume
    
    @property
    def available_volume(self) -> float:
        """Свободный объем."""
        return max(0.0, self._max_volume - self.filled)
    
    @property
    def fill_ratio(self) -> float:
        """Коэффициент заполнения."""
        if self._max_volume <= 0:
            return 0.0
        return min(1.0, self.filled / self._max_volume)
    
    @property
    def pressure(self) -> float:
        """Текущее давление."""
        return self.pressure_controller.current_pressure
    
    @property
    def sag(self) -> float:
        """Провисание."""
        return self._sag
    
    @property
    def elasticity(self) -> float:
        """Эластичность."""
        return self.inflation.profile.current_elasticity
    
    @property
    def current_cup(self) -> CupSize:
        """Динамический размер."""
        total_vol = self.current_volume
        for cup in reversed(list(CupSize)):
            if total_vol >= cup.base_volume:
                return cup
        return CupSize.AAA
    
    def add_fluid_by_type(self, fluid_type: FluidType, amount: float, source: str = None) -> float:
        """Добавить жидкость."""
        from body_sim.core.fluids import Fluid, FluidProperties
        
        # Проверяем необходимость инфляции
        current = self.mixture.total()
        available = self._max_volume - current
        
        if amount > available and self._auto_inflate:
            excess = amount - available
            inflate_amount = (excess / 100.0) * 0.05
            old_stretch = self.inflation.profile.stretch_ratio
            new_stretch = old_stretch + inflate_amount
            
            result = self.inflation.apply_stretch(new_stretch)
            self._max_volume = self._base_volume * 1.5 * self.inflation.profile.stretch_ratio
            self.max_capacity = self._max_volume
        
        # Добавляем жидкость
        actual = min(amount, self._max_volume - current)
        if actual > 0:
            self.mixture.add(fluid_type, actual, source or self.component_id)
        
        return actual
    
    def express(self, amount: float) -> float:
        """Выдаить молоко."""
        # Находим молоко
        milk_amount = self.mixture.get_amount(FluidType.MILK)
        to_remove = min(amount, milk_amount)
        
        if to_remove > 0:
            removed = self.mixture.remove(to_remove, [FluidType.MILK])
            return sum(removed.values())
        return 0.0
    
    def start_lactation(self):
        """Запустить лактацию."""
        self.lactation.start()
        
    def stop_lactation(self):
        """Остановить лактацию."""
        self.lactation.stop()
    
    def insert_object(self, obj_data: Dict) -> bool:
        """Вставить объект."""
        return self.insertion.insert(obj_data)
    
    def remove_object(self, name: str) -> Optional[Dict]:
        """Удалить объект."""
        obj = self.insertion.remove(name)
        return obj.__dict__ if obj else None
    
    def tick(self, dt: float = 1.0, event_bus: EventBus = None) -> Dict[str, Any]:
        """Обновить состояние."""
        # Инфляция
        target = self.inflation.calculate_target_stretch(self.current_volume, self._base_volume)
        self.inflation.apply_stretch(target, dt)
        self._max_volume = self._base_volume * 1.5 * self.inflation.profile.stretch_ratio
        
        # Физика
        self._sag = PhysicsEngine.calculate_sag(
            self.fill_ratio,
            fluid_density=self.mixture.density(),
            elasticity=self.elasticity,
            current_sag=self._sag,
            dt=dt
        )
        
        # Давление
        pressure = PhysicsEngine.calculate_pressure(
            self.filled,
            self._base_volume,
            self.mixture.viscosity(),
            self.elasticity,
            self._sag
        )
        self.pressure_controller.update(pressure)
        
        # Лактация
        lactation_result = self.lactation.tick(dt, self, event_bus)
        
        return {
            'state': self._state,
            'filled': self.filled,
            'pressure': pressure,
            'stretch': self.inflation.profile.stretch_ratio
        }
    
    def get_full_state(self) -> Dict[str, Any]:
        """Полное состояние."""
        return {
            'cup': self.current_cup.name,
            'filled': self.filled,
            'max_volume': self._max_volume,
            'pressure': self.pressure,
            'state': self._state,
            'lactation': self.lactation.profile.state.name
        }

class Breasts:
    """Контейнер для пары грудей."""
    
    def __init__(self, cup_size: CupSize = CupSize.C):
        self.left = BreastComponent("left_breast", cup_size, "left")
        self.right = BreastComponent("right_breast", cup_size, "right")
        self._event_bus: Optional[EventBus] = None
        self._cross_factor = 0.3  # Коэффициент перекрестной стимуляции
    
    def set_event_bus(self, event_bus: EventBus):
        """Установить EventBus для перекрестной стимуляции."""
        self._event_bus = event_bus
        self._setup_cross_stimulation()
    
    def _setup_cross_stimulation(self):
        """Настроить перекрестную стимуляцию через EventBus."""
        if not self._event_bus:
            return
            
        def on_stimulation(event):
            """Обработчик событий стимуляции."""
            if event.type != EventType.MODIFIER_APPLIED:
                return
                
            # Если стимулировали левую - возбуждаем правую
            if event.source == self.left.component_id:
                intensity = event.get('intensity', 0)
                if intensity > 0.5:
                    self.right.stimulate(intensity * self._cross_factor)
                    
            # Если стимулировали правую - возбуждаем левую
            elif event.source == self.right.component_id:
                intensity = event.get('intensity', 0)
                if intensity > 0.5:
                    self.left.stimulate(intensity * self._cross_factor)
        
        # Подписываемся на события
        self._event_bus.subscribe(EventType.MODIFIER_APPLIED, on_stimulation)
    
    def stimulate(self, side: str, intensity: float = 1.0):
        """Стимулировать одну грудь с эмиссией события."""
        breast = self.get_breast(side)
        if breast:
            # Прямая стимуляция
            result = breast.stimulate(intensity)
            
            # Эмитируем событие для перекрестной стимуляции
            if self._event_bus:
                self._event_bus.emit(Event(
                    type=EventType.MODIFIER_APPLIED,
                    source=breast.component_id,
                    data={
                        'intensity': intensity,
                        'action': 'stimulate',
                        'result': result
                    }
                ))
            return result
        return None
    
    def stimulate_both(self, intensity: float = 1.0):
        """Стимулировать обе груди."""
        self.stimulate("left", intensity)
        self.stimulate("right", intensity)
    
    def update(self, delta_time: float, event_bus: EventBus):
        """Обновить обе груди."""
        # Устанавливаем event_bus при первом вызове
        if not self._event_bus and event_bus:
            self.set_event_bus(event_bus)
            
        self.left.tick(delta_time, event_bus)
        self.right.tick(delta_time, event_bus)
    
    def get_state(self) -> Dict[str, Any]:
        return {
            'left': self.left.get_full_state(),
            'right': self.right.get_full_state()
        }
    
    def get_breast(self, side: str):
        """Получить грудь по стороне."""
        if side.lower() in ("left", "l", "0"):
            return self.left
        elif side.lower() in ("right", "r", "1"):
            return self.right
        return None
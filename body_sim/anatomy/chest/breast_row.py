# === chest/breast_row.py (исправленный) ===
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus
from body_sim.core.fluids import FluidMixture, FluidType
from body_sim.systems.inflation import InflationSystem, InflationProfile
from body_sim.systems.lactation import LactationSystem, LactationProfile
from body_sim.systems.insertion import InsertionManager
from body_sim.systems.physics import PhysicsEngine
from body_sim.systems.pressure import PressureController

from .cup_size import CupSize
from .nipple import Nipple, NipplePlug
from .areola import Areola
from .milk_ducts import MilkDuctSystem


@dataclass
class BreastRow(AnatomicalComponent):
    """
    Один ряд груди (левая/правая или дополнительные у фурри).
    Объединяет новую анатомию со старыми системами (инфляция, давление, физика).
    """
    index: int = 0
    side: str = "left"  # "left", "right", или "aux_N"
    cup_size: CupSize = field(default=CupSize.C)
    
    # Анатомические компоненты
    areola: Areola = field(default_factory=Areola)
    duct_system: MilkDuctSystem = field(default_factory=MilkDuctSystem)
    
    # Параметры ткани (не конфликтуют с родителем)
    firmness: float = 1.0  # 0=мягкая, 1=упругая
    glandular_density: float = 0.6
    
    # Системы (инициализируются в __post_init__)
    inflation: InflationSystem = field(init=False, repr=False)
    lactation: LactationSystem = field(init=False, repr=False)
    insertion: InsertionManager = field(init=False, repr=False)
    pressure_controller: PressureController = field(init=False, repr=False)
    
    # Жидкости и состояние
    mixture: FluidMixture = field(default_factory=FluidMixture)
    current_milk_volume: float = 0.0  # В железах
    
    # Приватные поля состояния
    _state: str = field(default="normal", repr=False)
    _auto_inflate: bool = field(default=True, repr=False)
    _sag: float = field(default=0.0, repr=False)
    _max_volume: float = field(init=False, repr=False)
    
    # Константы давления
    PRESSURE_NORMAL = 0.5
    PRESSURE_TENSE = 1.0
    PRESSURE_LEAK = 0.8
    
    def __post_init__(self):
        # Вычисляем базовый объем
        base_vol = self.cup_size.base_volume
        
        # Инициализация AnatomicalComponent с правильными аргументами
        # name - первый позиционный аргумент, base_volume и max_volume_multiplier - keyword args
        super().__init__(
            f"{self.side}_breast_{self.index}",  # name
            base_volume=base_vol, 
            max_volume_multiplier=1.5
        )
        
        # Теперь self.base_volume доступен от родителя
        self._max_volume = self.base_volume * 1.5
        
        # Инициализация систем
        self.inflation = InflationSystem(InflationProfile(
            max_stretch=3.0,
            plasticity=0.3,
            base_elasticity=1.0
        ))
        self.lactation = LactationSystem(LactationProfile())
        self.insertion = InsertionManager()
        self.pressure_controller = PressureController()
        
        # Настройка ареолы под размер
        self.areola.diameter = 3.0 + (self.cup_size.value / 100)
        if not self.areola.nipples:
            self.areola.nipples = [Nipple(diameter=self.areola.diameter * 0.25)]
    
    @property
    def filled(self) -> float:
        """Общий объем жидкости (молоко + другие)."""
        return self.mixture.total() + self.current_milk_volume
    
    @property
    def volume(self) -> float:
        """Текущий общий объем с учетом растяжения."""
        fluid_volume = self.mixture.total()
        objects_volume = getattr(self.insertion, 'total_volume', 0)
        
        stretch = self.inflation.profile.stretch_ratio
        tissue_volume = self.base_volume * stretch
        
        return tissue_volume + fluid_volume + objects_volume + self.current_milk_volume
    
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
        """Текущая эластичность."""
        return self.inflation.profile.current_elasticity
    
    @property
    def current_cup(self) -> CupSize:
        """Динамический размер с учетом растяжения и наполнения."""
        total_vol = self.volume
        return CupSize.from_volume(total_vol)
    
    # === Методы из старого BreastComponent ===
    
    def add_fluid_by_type(self, fluid_type: FluidType, amount: float, source: str = None) -> float:
        """Добавить жидкость с автоматической инфляцией при переполнении."""
        current = self.mixture.total()
        available = self._max_volume - current - self.current_milk_volume
        
        if amount > available and self._auto_inflate:
            excess = amount - available
            inflate_amount = (excess / 100.0) * 0.05
            old_stretch = self.inflation.profile.stretch_ratio
            new_stretch = old_stretch + inflate_amount
            
            self.inflation.apply_stretch(new_stretch)
            self._max_volume = self.base_volume * 1.5 * self.inflation.profile.stretch_ratio
        
        actual = min(amount, self._max_volume - current - self.current_milk_volume)
        if actual > 0:
            self.mixture.add(fluid_type, actual, source or getattr(self, 'component_id', 'unknown'))
        
        return actual
    
    def express(self, amount: float, pressure: float = 1.0) -> float:
        """
        Выдаить молоко. Сначала из протоков/синусов, 
        потом из желез.
        """
        # Из протоков
        from_ducts = self.duct_system.express(pressure)
        
        # Из молочной смеси (если молоко там)
        milk_in_mixture = self.mixture.get_amount(FluidType.MILK)
        to_remove = min(amount - from_ducts, milk_in_mixture)
        removed = 0.0
        if to_remove > 0:
            removed_dict = self.mixture.remove(to_remove, [FluidType.MILK])
            removed = sum(removed_dict.values())
        
        # Из желез (упрощенно)
        from_glands = min(amount - from_ducts - removed, self.current_milk_volume)
        self.current_milk_volume -= from_glands
        
        total = from_ducts + removed + from_glands
        
        # Стимуляция при сцеживании
        if total > 0:
            self.areola.stimulate(0.5)
        
        return total
    
    def start_lactation(self, intensity: float = 10.0):
        """Запустить лактацию."""
        self.lactation.start()
        if hasattr(self.lactation, 'profile') and hasattr(self.lactation.profile, 'production_rate'):
            self.lactation.profile.production_rate = intensity
    
    def stop_lactation(self):
        """Остановить лактацию."""
        self.lactation.stop()
    
    def insert_object(self, obj_data: Dict) -> bool:
        """Вставить объект в грудь."""
        return self.insertion.insert(obj_data)
    
    def remove_object(self, name: str) -> Optional[Dict]:
        """Удалить объект."""
        obj = self.insertion.remove(name)
        return obj.__dict__ if obj else None
    
    def stimulate(self, intensity: float = 1.0) -> dict:
        """Стимулировать грудь."""
        self.areola.stimulate(intensity)
        
        # Увеличиваем приток крови = небольшое увеличение объема
        temp_inflate = 1.0 + (intensity * 0.02)
        self.inflation.apply_stretch(temp_inflate)
        
        return {
            'sensitivity': sum(n.sensitivity for n in self.areola.nipples) if self.areola.nipples else 0,
            'state': 'stimulated'
        }
    
    def tick(self, dt: float = 1.0, event_bus: EventBus = None) -> Dict[str, Any]:
        """
        Обновление состояния (физика, инфляция, давление).
        """
        # Инфляция
        target = self.inflation.calculate_target_stretch(self.volume, self.base_volume)
        self.inflation.apply_stretch(target, dt)
        self._max_volume = self.base_volume * 1.5 * self.inflation.profile.stretch_ratio
        
        # Физика провисания
        fluid_density = self.mixture.density() if self.mixture.total() > 0 else 1.0
        self._sag = PhysicsEngine.calculate_sag(
            self.fill_ratio,
            fluid_density=fluid_density,
            elasticity=self.elasticity,
            current_sag=self._sag,
            dt=dt
        )
        
        # Давление
        calculated_pressure = PhysicsEngine.calculate_pressure(
            self.filled,
            self.base_volume,
            self.mixture.viscosity(),
            self.elasticity,
            self._sag
        )
        self.pressure_controller.update(calculated_pressure)
        
        # Лактация
        try:
            lactation_result = self.lactation.tick(dt, self, event_bus)
            if lactation_result and lactation_result.get('milk_produced'):
                self.current_milk_volume += lactation_result['milk_produced']
                # Перекачка в протоки
                num_ducts = max(1, len(self.duct_system.nipple_ducts))
                per_duct = lactation_result['milk_produced'] / num_ducts
                for duct in self.duct_system.nipple_ducts:
                    overflow = duct.receive_milk(per_duct)
                    if overflow > 0:
                        self.duct_system.lactiferous_sinuses += overflow
        except Exception:
            pass  # Лактация может быть не инициализирована полностью
        
        # Проверка на утечку при высоком давлении
        if (self.pressure > self.PRESSURE_LEAK and 
            self.areola.nipples and 
            not self.areola.nipples[0].plug):
            leak_amount = (self.pressure - self.PRESSURE_LEAK) * 0.1 * dt
            if self.duct_system.lactiferous_sinuses > 0:
                self.duct_system.lactiferous_sinuses = max(0, 
                    self.duct_system.lactiferous_sinuses - leak_amount)
        
        return {
            'state': self._state,
            'filled': self.filled,
            'pressure': self.pressure,
            'stretch': self.inflation.profile.stretch_ratio,
            'cup': self.current_cup.name
        }
    
    def update(self, delta_time: float, event_bus: EventBus):
        """AnatomicalComponent.update() -> tick()"""
        return self.tick(delta_time, event_bus)
    
    def get_full_state(self) -> Dict[str, Any]:
        """Полное состояние для совместимости со старым кодом."""
        return {
            'cup': self.current_cup.name,
            'base_cup': self.cup_size.name,
            'filled': self.filled,
            'max_volume': self._max_volume,
            'pressure': self.pressure,
            'stretch': self.inflation.profile.stretch_ratio,
            'sag': self._sag,
            'state': self._state,
            'lactation': (self.lactation.profile.state.name 
                         if hasattr(self.lactation, 'profile') and 
                            hasattr(self.lactation.profile, 'state') 
                         else 'inactive'),
            'areola': self.areola.get_state() if hasattr(self.areola, 'get_state') else {},
            'ducts': {
                'prolapse_total': self.duct_system.total_prolapse(),
                'flow_capacity': self.duct_system.get_flow_capacity()
            }
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Для AnatomicalComponent.get_state()"""
        return self.get_full_state()

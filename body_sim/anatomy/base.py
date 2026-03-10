# body_sim/anatomy/base.py
from typing import Dict, Any, List, Optional
from datetime import datetime

from body_sim.core.components import BaseComponent
from body_sim.core.fluids import FluidContainer, Fluid, FluidType
from body_sim.core.events import EventBus, EventType
from body_sim.systems.physics import PhysicsEngine

class AnatomicalComponent(BaseComponent, FluidContainer):
    """
    Улучшенный базовый анатомический компонент.
    Интегрирует физику, жидкости и возбуждение.
    """
    
    def __init__(self, name: str, base_volume: float = 100.0, max_volume_multiplier: float = 1.5, max_volume: float = None, sensitivity: float = 1.0):
        BaseComponent.__init__(self, name)
        
        # Определяем объемы
        self._base_volume = base_volume
        
        if max_volume is not None:
            # Обратная совместимость: если передан max_volume напрямую
            actual_max = max_volume
            self._max_volume_multiplier = max_volume / base_volume if base_volume > 0 else 1.5
        else:
            self._max_volume_multiplier = max_volume_multiplier
            actual_max = base_volume * max_volume_multiplier
            
        # Инициализируем FluidContainer
        FluidContainer.__init__(self, actual_max)
        
        self._current_max_volume = actual_max
        
        # Физиология
        self.sensitivity = sensitivity
        self.current_stimulation = 0.0
        self.pain_level = 0.0
        self.arousal = 0.0
        self.pleasure = 0.0
        
        # Физика
        self._elasticity = 1.0
        self._sag = 0.0
        self._pressure = 0.0
        
        # Объекты внутри
        self._inserted_objects: List[Dict] = []
        
    @property
    def base_volume(self) -> float:
        return self._base_volume
        
    @property
    def current_volume(self) -> float:
        """Общий текущий объем (ткань + жидкость + объекты)."""
        objects_vol = sum(obj.get('volume', 0) for obj in self._inserted_objects)
        return self._base_volume + self.mixture.total() + objects_vol
    
    @property
    def available_volume(self) -> float:
        return max(0.0, self._current_max_volume - self.mixture.total())
    
    @property
    def pressure(self) -> float:
        return self._pressure
    
    @property
    def elasticity(self) -> float:
        return self._elasticity
        
    def add_fluid_by_type(self, fluid_type: FluidType, amount: float, source: str = None) -> float:
        """Удобный метод добавления жидкости по типу."""
        fluid = Fluid(
            fluid_type=fluid_type,
            volume=amount,
            source_component=source or self.component_id
        )
        overflow = self.add_fluid(fluid)
        actual = amount - overflow
        
        if actual > 0:
            self._pending_events = getattr(self, '_pending_events', [])
            self._pending_events.append((EventType.FLUID_ADDED, {
                'type': fluid_type.value,
                'amount': actual,
                'overflow': overflow
            }))
            
        return actual
    
    def remove_fluid_by_type(self, amount: float, fluid_type: Optional[FluidType] = None) -> float:
        """Удалить жидкость."""
        removed = self.remove_fluid(amount, fluid_type)
        total = sum(f.volume for f in removed)
        
        if total > 0:
            self._pending_events = getattr(self, '_pending_events', [])
            self._pending_events.append((EventType.FLUID_REMOVED, {
                'amount': total,
                'types': [f.fluid_type.value for f in removed]
            }))
        return total
        
    def stimulate(self, amount: float, source: str = None, stimulation_type: str = "general"):
        """Стимулировать компонент."""
        self.current_stimulation = min(100.0, self.current_stimulation + amount * self.sensitivity)
        
        pleasure_gain = max(0.0, amount - 3.0) * self.sensitivity * 0.1
        pain_gain = max(0.0, amount - 8.0)
        
        self.pleasure = min(100.0, self.pleasure + pleasure_gain)
        self.pain_level = min(100.0, self.pain_level + pain_gain)
        self.arousal = min(1.0, self.arousal + amount * 0.01)
        
        return {
            'pleasure': pleasure_gain,
            'pain': pain_gain,
            'arousal': amount * 0.01
        }
    
    def calculate_pressure(self, external: float = 0.0) -> float:
        """Обновить и вернуть давление."""
        self._pressure = PhysicsEngine.calculate_pressure(
            self.mixture.total(),
            self._base_volume,
            self.mixture.viscosity(),
            self._elasticity,
            self._sag,
            external
        )
        return self._pressure
    
    def insert_object(self, obj_data: Dict) -> bool:
        """Вставить объект в полость."""
        obj_volume = obj_data.get('volume', 0)
        if self.current_volume + obj_volume <= self._current_max_volume * 1.5:
            self._inserted_objects.append(obj_data)
            return True
        return False
    
    def remove_object(self, obj_name: str) -> Optional[Dict]:
        """Удалить объект."""
        for i, obj in enumerate(self._inserted_objects):
            if obj.get('name') == obj_name:
                return self._inserted_objects.pop(i)
        return None
        
    def update(self, delta_time: float, event_bus: EventBus):
        """Базовое обновление с физикой."""
        super().update(delta_time, event_bus)
        
        # Обновление давления
        old_pressure = self._pressure
        self.calculate_pressure()
        
        if abs(self._pressure - old_pressure) > 0.1:
            event_bus.emit(Event(
                type=EventType.PRESSURE_CHANGE,
                source=self.component_id,
                data={
                    'old': old_pressure,
                    'new': self._pressure,
                    'fullness': self.get_fullness()
                }
            ))
        
        # Естественное снижение
        self.current_stimulation *= (0.95 ** delta_time)
        self.pain_level *= (0.90 ** delta_time)
        if self.arousal > 0:
            self.arousal = max(0.0, self.arousal - 0.02 * delta_time)
        if self.pleasure > 0:
            self.pleasure = max(0.0, self.pleasure - 0.05 * delta_time)
            
    def get_state(self) -> Dict[str, Any]:
        """Расширенное состояние."""
        base = super().get_state()
        base.update({
            'anatomy': {
                'base_volume': self._base_volume,
                'current_volume': self.current_volume,
                'max_volume': self._current_max_volume,
                'fullness': self.get_fullness(),
                'pressure': self._pressure,
                'elasticity': self._elasticity,
                'sag': self._sag
            },
            'physiology': {
                'sensitivity': self.sensitivity,
                'stimulation': self.current_stimulation,
                'arousal': self.arousal,
                'pleasure': self.pleasure,
                'pain': self.pain_level
            },
            'fluids': {
                'total': self.mixture.total(),
                'composition': {
                    ft.name: round(vol, 2) 
                    for ft, vol in self.mixture.composition().items()
                },
                'viscosity': self.mixture.viscosity(),
                'density': self.mixture.density()
            },
            'inserted_objects': len(self._inserted_objects)
        })
        return base

# body_sim/systems/fluid_container.py
from typing import Dict, Optional
from body_sim.core.fluids import FluidMixture, FLUID_DEFS
from body_sim.core.enums import FluidType

class FluidContainer:
    """
    Универсальный контейнер жидкости.
    Использует FluidMixture для хранения, добавляет управление объемом и давлением.
    """
    
    def __init__(self, base_volume: float = 100.0, max_stretch_ratio: float = 5.0):
        self.base_volume = base_volume
        self.max_volume = base_volume
        self.max_stretch_ratio = max_stretch_ratio
        
        # Используем существующий FluidMixture
        self.contents = FluidMixture()
        
        # Параметры состояния (как у uterus)
        self.pressure = 0.0
        self.leakage = 0.0
        self.inflation_ratio = 1.0
        self.leaking_factor = 0.02
        self.is_leaking = False
        
    @property
    def filled(self) -> float:
        """Общий объем через FluidMixture.total()"""
        return self.contents.total()
        
    @property
    def available_space(self) -> float:
        return max(0, self.max_volume - self.filled)
        
    @property
    def fill_percentage(self) -> float:
        if self.max_volume <= 0:
            return 0.0
        return (self.filled / self.max_volume) * 100
        
    def add_fluid(self, fluid_type: FluidType, amount: float) -> float:
        """
        Добавить жидкость. Возвращает сколько реально добавлено.
        Остаток идет в leakage.
        """
        if amount <= 0:
            return 0.0
            
        actual_add = min(amount, self.available_space)
        
        if actual_add > 0:
            self.contents.add(fluid_type, actual_add)
            self._update_state()
            
        # Переполнение
        if actual_add < amount:
            self.leakage += (amount - actual_add)
            
        return actual_add
        
    def remove_fluid(self, amount: float, fluid_type: Optional[FluidType] = None) -> float:
        """
        Удалить жидкость. 
        Если fluid_type=None - удаляет пропорционально всем через FluidMixture.remove().
        """
        if amount <= 0 or self.filled <= 0:
            return 0.0
            
        if fluid_type:
            # Удаляем конкретный тип напрямую из components
            if fluid_type in self.contents.components:
                available = self.contents.components[fluid_type]
                to_remove = min(amount, available)
                self.contents.components[fluid_type] -= to_remove
                if self.contents.components[fluid_type] <= 0.01:
                    del self.contents.components[fluid_type]
                self._update_state()
                return to_remove
            return 0.0
        else:
            # Пропорционально всем через существующий метод
            removed = self.contents.remove(amount)
            self._update_state()
            return removed if removed else 0.0
            
    def drain_all(self) -> Dict[FluidType, float]:
        """Полная очистка. Возвращает словарь удаленных жидкостей."""
        removed = dict(self.contents.components)
        self.contents = FluidMixture()  # Новый пустой контейнер
        self.leakage = 0
        self._update_state()
        return removed
        
    def get_composition(self) -> Dict[str, float]:
        """Состав для UI: {'MILK': 50.0, 'CUM': 30.0}"""
        return {k.name: round(v, 1) for k, v in self.contents.components.items()}
        
    def get_fluid_properties(self) -> dict:
        """Вязкость и плотность смеси через FLUID_DEFS"""
        return {
            'viscosity': self.contents.viscosity(FLUID_DEFS),
            'density': self.contents.density(FLUID_DEFS),
            'total': self.filled
        }
        
    # === Методы инфляции (как у uterus) ===
    def inflate(self, ratio: float) -> bool:
        if ratio < 1.0:
            ratio = 1.0
        if ratio > self.max_stretch_ratio:
            return False
        self.max_volume = self.base_volume * ratio
        self.inflation_ratio = ratio
        self._update_state()
        return True
        
    def deflate(self, recovery_rate: float = 0.1):
        if self.inflation_ratio > 1.0:
            target = max(1.0, self.inflation_ratio - recovery_rate)
            self.inflation_ratio = target
            self.max_volume = self.base_volume * target
            
    def _update_state(self):
        """Обновление давления и флага утечки"""
        fill_ratio = self.filled / self.max_volume if self.max_volume > 0 else 0
        
        if fill_ratio > 0.8:
            self.pressure = ((fill_ratio - 0.8) / 0.2) ** 2
        else:
            self.pressure = 0.0
            
        self.is_leaking = fill_ratio > 0.95
        
    def tick(self, dt: float = 1.0):
        """Утечка при переполнении и восстановление формы"""
        if self.is_leaking and self.pressure > 0 and self.filled > 0:
            leak_amount = self.pressure * self.leaking_factor * self.filled * dt
            self.remove_fluid(leak_amount)
            self.leakage += leak_amount
            
        if self.inflation_ratio > 1.0 and self.fill_percentage < 70:
            self.deflate(0.05 * dt)
            
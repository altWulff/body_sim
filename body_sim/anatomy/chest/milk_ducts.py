# anatomy/chest/milk_ducts.py
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class DuctState(Enum):
    NORMAL = "normal"
    DILATED = "dilated"  # Расширены
    PROLAPSED = "prolapsed"  # Выпадение
    SEVERED = "severed"  # Отсечены порталом
    EXTERNAL = "external"  # Вынесены наружу через портал

@dataclass
class MilkDuct:
    """Один молочный проток (15-20 в каждом соске)"""
    id: int
    state: DuctState = DuctState.NORMAL
    diameter: float = 0.05  # см в норме
    length: float = 2.0  # см от соска до долей
    milk_flow_rate: float = 0.0  # мл/мин
    prolapse_length: float = 0.0  # см выпавшего протока
    connected_to: Optional[str] = None  # ID портала или "external"
    internal_volume: float = 0.0  # Молоко внутри протока
    
    def dilate(self, factor: float):
        self.diameter *= factor
        if self.diameter > 0.3:
            self.state = DuctState.DILATED
            
    def prolapse(self, amount: float):
        """Выпадение протока наружу"""
        if self.state != DuctState.SEVERED:
            self.prolapse_length += amount
            self.state = DuctState.PROLAPSED
            
    def sever(self, portal_id: Optional[str] = None):
        """Отсечение порталом"""
        self.state = DuctState.SEVERED
        self.connected_to = portal_id
        
    def reconnect(self):
        """Восстановление соединения"""
        if self.state == DuctState.SEVERED:
            self.state = DuctState.NORMAL
            self.connected_to = None
            
    def receive_milk(self, amount: float) -> float:
        """Получение молока из долей"""
        overflow = 0.0
        self.internal_volume += amount
        max_volume = 3.14 * (self.diameter/2)**2 * self.length * 1000  # мл
        if self.internal_volume > max_volume:
            overflow = self.internal_volume - max_volume
            self.internal_volume = max_volume
        return overflow  # Переполнение идёт наружу при сильном давлении

@dataclass
class MilkDuctSystem:
    """Система протоков груди"""
    nipple_ducts: List[MilkDuct] = field(default_factory=list)  # 15-20 протоков
    collecting_ducts: List[MilkDuct] = field(default_factory=list)  # Собирающие протоки внутри
    lactiferous_sinuses: float = 0.0  # Молочные синусы (резервуары)
    
    def __post_init__(self):
        if not self.nipple_ducts:
            # Создаём 18 стандартных протоков
            self.nipple_ducts = [MilkDuct(id=i) for i in range(18)]
    
    def total_prolapse(self) -> float:
        """Общая длина выпавших протоков"""
        return sum(d.prolapse_length for d in self.nipple_ducts)
    
    def get_flow_capacity(self) -> float:
        """Пропускная способность в мл/мин"""
        active_ducts = [d for d in self.nipple_ducts 
                       if d.state not in [DuctState.SEVERED, DuctState.EXTERNAL]]
        return sum(3.14 * (d.diameter/2)**2 * 10 for d in active_ducts)  # Упрощённо
    
    def express(self, pressure: float) -> float:
        """Сцеживание под давлением"""
        if pressure > 2.0:  # сильное давление
            # Риск пролапса при высоком давлении и растянутых протоках
            for duct in self.nipple_ducts:
                if duct.diameter > 0.2 and duct.state == DuctState.DILATED:
                    duct.prolapse(0.1 * pressure)
        
        total_milk = self.lactiferous_sinuses
        self.lactiferous_sinuses = 0
        
        for duct in self.nipple_ducts:
            if duct.state == DuctState.NORMAL:
                total_milk += duct.internal_volume
                duct.internal_volume = 0
                
        return total_milk
    
    def severe_prolapse_repair(self):
        """Хирургическое восстановление после полного пролапса"""
        for duct in self.nipple_ducts:
            if duct.state == DuctState.PROLAPSED:
                duct.prolapse_length = 0
                duct.state = DuctState.NORMAL
                duct.diameter = max(0.05, duct.diameter * 0.8)  # Уменьшаем диаметр
                
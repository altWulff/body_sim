# anatomy/chest/breast_row.py
from dataclasses import dataclass, field
from typing import Optional
from .nipple import Nipple, NipplePlug
from .areola import Areola
from .milk_ducts import MilkDuctSystem

@dataclass
class BreastRow:
    """Один ряд грудной клетки"""
    index: int = 0
    size: float = 1.0  # 1=A, 2=B, 3=C и т.д.
    firmness: float = 1.0  # 0=мягкая, 1=упругая
    volume: float = field(init=False)
    
    # Анатомические компоненты
    nipple: Nipple = field(default_factory=Nipple)
    areola: Areola = field(default_factory=Areola)
    duct_system: MilkDuctSystem = field(default_factory=MilkDuctSystem)
    
    # Железистая ткань
    milk_glands_active: bool = False
    glandular_density: float = 0.6  # Доля железистой ткани
    milk_production_rate: float = 0.0  # мл/час
    current_milk_volume: float = 0.0  # мл в долях
    
    def __post_init__(self):
        self.volume = self.size * 250  # мл приблизительно
        # Настраиваем размер ареолы под размер груди
        self.areola.diameter = 3.0 + (self.size * 0.8)
        self.nipple.size = 0.5 + (self.size * 0.15)
        
    def lactate(self, delta_time: float):
        """Производство молока"""
        if self.milk_glands_active:
            produced = self.milk_production_rate * delta_time
            self.current_milk_volume += produced
            
            # Заполняем протоки
            per_duct = produced / len(self.duct_system.nipple_ducts)
            for duct in self.duct_system.nipple_ducts:
                overflow = duct.receive_milk(per_duct)
                if overflow > 0:
                    self.duct_system.lactiferous_sinuses += overflow
    
    def express(self, amount: float, pressure: float = 1.0) -> float:
        """Сцеживание молока"""
        # Сначала из синусов и протоков
        from_ducts = self.duct_system.express(pressure)
        
        # Затем из долей (упрощённо)
        from_glands = min(amount - from_ducts, self.current_milk_volume)
        self.current_milk_volume -= from_glands
        
        total = from_ducts + from_glands
        
        # Стимуляция при сцеживании
        self.nipple.erect()
        self.areola.stimulate()
        
        return total
    
    def get_total_milk(self) -> float:
        """Общее количество молока"""
        in_ducts = sum(d.internal_volume for d in self.duct_system.nipple_ducts)
        return self.current_milk_volume + in_ducts + self.duct_system.lactiferous_sinuses
    
    def stimulate(self):
        """Стимуляция соска и ареолы"""
        self.nipple.erect()
        self.areola.stimulate()
        if self.milk_glands_active:
            self.milk_production_rate = min(50, self.milk_production_rate + 0.1)
            
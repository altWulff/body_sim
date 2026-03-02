# anatomy/breasts.py

from typing import List

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus

class BreastRow:
    def __init__(self, index: int, size: float = 1.0):
        self.index = index
        self.size = size  # в условных единицах (1=A, 2=B, 3=C и т.д.)
        self.milk_glands_active = False
        self.milk_volume = 0.0
        self.max_milk = size * 200  # ml
        self.nipple_size = 0.5 + (size * 0.2)
        self.nipple_plug = None
        self.sensitivity = 1.0
        
    def lactate(self, amount: float):
        if self.milk_glands_active:
            self.milk_volume = min(self.max_milk, self.milk_volume + amount)
            
    def express(self, amount: float) -> float:
        taken = min(amount, self.milk_volume)
        self.milk_volume -= taken
        return taken

class Breasts(AnatomicalComponent):
    def __init__(self):
        super().__init__("breasts")
        self.rows: List[BreastRow] = [BreastRow(0, 3.0)]  # Одна пара по умолчанию
        self.areola_color = "pink"
        self.firmness = 1.0
        
    def add_row(self, size: float):
        new_row = BreastRow(len(self.rows), size)
        self.rows.append(new_row)
        
    def start_lactation(self, row_index: int = None):
        if row_index is None:
            for row in self.rows:
                row.milk_glands_active = True
        else:
            if 0 <= row_index < len(self.rows):
                self.rows[row_index].milk_glands_active = True
                
    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        for row in self.rows:
            if row.milk_glands_active:
                row.lactate(0.5 * delta_time)  # мл в час

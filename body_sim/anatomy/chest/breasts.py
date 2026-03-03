# anatomy/chest/breasts.py
from typing import List
from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus
from .breast_row import BreastRow

class Breasts(AnatomicalComponent):
    def __init__(self):
        super().__init__("breasts")
        self.rows: List[BreastRow] = [BreastRow(0, 3.0)]
        self.chest_circumference: float = 85.0  # Обхват под грудью
        self.intermammary_distance: float = 18.0  # Расстояние между сосками
        
    def add_row(self, size: float) -> BreastRow:
        """Добавить дополнительный ряд (для фурри/монстров)"""
        new_row = BreastRow(len(self.rows), size)
        self.rows.append(new_row)
        return new_row
    
    def remove_row(self, index: int):
        """Удалить ряд (редко используется)"""
        if 0 < index < len(self.rows):
            self.rows.pop(index)
            # Перенумеровываем
            for i, row in enumerate(self.rows):
                row.index = i
    
    def start_lactation(self, row_index: int = None, intensity: float = 10.0):
        """Запуск лактации"""
        targets = [self.rows[row_index]] if row_index is not None else self.rows
        
        for row in targets:
            row.milk_glands_active = True
            row.milk_production_rate = intensity
    
    def stop_lactation(self, row_index: int = None):
        """Остановка лактации"""
        targets = [self.rows[row_index]] if row_index is not None else self.rows
        for row in targets:
            row.milk_glands_active = False
            row.milk_production_rate = 0.0
    
    def express_all(self, amount_per_row: float = None, pressure: float = 1.0) -> float:
        """Сцеживание со всех рядов"""
        total = 0.0
        for row in self.rows:
            amount = amount_per_row or row.get_total_milk()
            total += row.express(amount, pressure)
        return total
    
    def get_total_milk(self) -> float:
        return sum(row.get_total_milk() for row in self.rows)
    
    def get_prolapsed_ducts_report(self) -> dict:
        """Отчёт о пролапсированных протоках для всех рядов"""
        report = {}
        for i, row in enumerate(self.rows):
            prolapse = row.duct_system.total_prolapse()
            if prolapse > 0:
                report[f"row_{i}"] = {
                    "total_prolapse_cm": prolapse,
                    "ducts_affected": sum(1 for d in row.duct_system.nipple_ducts 
                                         if d.state.name == "PROLAPSED")
                }
        return report
    
    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        for row in self.rows:
            row.lactate(delta_time)
            
            # Случайное опорожнение переполненных протоков
            if row.duct_system.lactiferous_sinuses > 5.0:
                # Молоко капает из сосков
                if not row.nipple.plug:
                    overflow = min(0.1 * delta_time, row.duct_system.lactiferous_sinuses)
                    row.duct_system.lactiferous_sinuses -= overflow
                    
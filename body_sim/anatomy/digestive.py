# anatomy/digestive.py

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.components import BaseComponent
from body_sim.core.events import EventBus

class Stomach(AnatomicalComponent):
    def __init__(self):
        super().__init__("stomach", max_volume=1500)
        self.ph_level = 1.5
        self.emptying_rate = 2.0  # ml/min
        self.peristalsis_active = False
        
    def digest(self, delta_time: float):
        # Пищеварение жидкостей
        for fluid in self.fluids:
            if fluid.fluid_type != FluidType.GASTRIC_JUICE:
                # Переваривание
                fluid.volume -= self.emptying_rate * delta_time / 60
        
        self.fluids = [f for f in self.fluids if f.volume > 0]

class Anus(AnatomicalComponent):
    def __init__(self):
        super().__init__("anus", max_volume=100)
        self.sphincter_tone = 1.0  # 0-1
        self.diameter = 0.0  # cm текущее растяжение
        self.max_diameter = 8.0
        self.connected_to_stomach = False  # Для экстремальных сценариев
        
    def penetrate(self, size: float, depth: float):
        self.diameter = max(self.diameter, size)
        if self.connected_to_stomach:
            # Прямая передача в желудок минуя кишечник
            pass
            
    def connect_to_stomach(self, stomach: Stomach):
        """Устанавливает прямое соединение (альтернативная анатомия)"""
        self.connected_to_stomach = True
        self.connect_to(stomach)

class Mouth(AnatomicalComponent):
    def __init__(self):
        super().__init__("mouth", max_volume=100)
        self.jaw_opening = 0.0  # cm
        self.max_opening = 6.0
        self.saliva_production = 1.0
        
    def open(self, amount: float):
        self.jaw_opening = min(amount, self.max_opening)
        
    def can_accept(self, size: float) -> bool:
        return self.jaw_opening >= size

class DigestiveSystem(BaseComponent):
    def __init__(self):
        super().__init__("digestive_system")
        self.mouth = Mouth()
        self.stomach = Stomach()
        self.anus = Anus()
        self.intestines = AnatomicalComponent("intestines", max_volume=2000)
        
    def update(self, delta_time: float, event_bus: EventBus):
        self.mouth.update(delta_time, event_bus)
        self.stomach.update(delta_time, event_bus)
        self.stomach.digest(delta_time)
        self.anus.update(delta_time, event_bus)
        self.intestines.update(delta_time, event_bus)
        
        # Связь ануса с желудком для специфических сценариев
        if self.anus.connected_to_stomach and self.anus.fluids:
            for fluid in self.anus.fluids[:]:
                self.anus.transfer_to(self.stomach, fluid.volume, event_bus=event_bus)

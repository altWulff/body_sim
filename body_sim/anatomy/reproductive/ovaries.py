# anatomy/reproductive/ovaries.py

from typing import List, Optional
from dataclasses import dataclass

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus
from body_sim.core.body import Body
from body_sim.core.fluids import Fluid, FluidType

@dataclass
class Gamete:
    id: str
    is_sperm: bool
    dna: str
    maturity: float = 0.0
    fertility: float = 1.0

class Ovaries(AnatomicalComponent):
    def __init__(self, side: str, body: Body = None):
        super().__init__(f"ovary_{side}", max_volume=50)
        self.side = side
        self.gametes: List[Gamete] = []
        self.follicles = 15
        self.hormone_estrogen = 1.0
        self.hormone_progesterone = 0.0
        self.can_spermatogenesis = False  # Для футанари-сценариев
        self.is_testis = False
        
    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        
        # Созревание
        for gamete in self.gametes:
            if gamete.maturity < 1.0:
                gamete.maturity += 0.001 * delta_time
                
        # Овуляция при созревании
        mature = [g for g in self.gametes if g.maturity >= 1.0 and not g.is_sperm]
        if mature and self.hormone_estrogen > 0.8:
            gamete = mature[0]
            event_bus.emit(Event(
                type=EventType.OVULATION,
                source=self.component_id,
                data={'gamete_id': gamete.id, 'side': self.side}
            ))
            
    def release_gamete(self) -> Optional[Gamete]:
        mature = [g for g in self.gametes if g.maturity >= 1.0]
        if mature:
            g = mature[0]
            self.gametes.remove(g)
            return g
        return None
        
    def transform_to_testis(self):
        self.is_testis = True
        self.can_spermatogenesis = True
        self.gametes = []  # Сброс яйцеклеток
        
    def produce_semen(self, volume: float) -> Fluid:
        if not self.can_spermatogenesis:
            raise ValueError("Cannot produce semen")
        return Fluid(
            fluid_type=FluidType.SEMEN,
            volume=volume,
            source_component=self.component_id,
            properties={'sperm_count': volume * 1000000}  # миллионы на мл
        )

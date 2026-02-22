from dataclasses import dataclass, field
from body_sim.core.enums import FluidType


@dataclass
class Esophagus:
    """Пищевод как соединительная труба между ртом и желудком."""
    length: float = 25.0         # см
    diameter: float = 2.5        # см
    
    stomach_connection: Optional[Any] = field(default=None, repr=False)
    mouth_connection: Optional[Any] = field(default=None, repr=False)
    
    # Перистальтика
    peristalsis_active: bool = False
    contents: FluidMixture = field(default_factory=FluidMixture)
    
    def receive_fluid(self, fluids: Dict[FluidType, float], amount: float) -> float:
        """Принять жидкость из рта."""
        if not self.stomach_connection:
            return 0.0
        
        # Перистальтика передает в желудок
        return self.stomach_connection.add_fluid(
            max(fluids.items(), key=lambda x: x[1])[0], amount
        )
    
    def receive_reflux(self, fluid_type: FluidType, amount: float):
        """Принять рефлюкс из желудка (обратно в рот)."""
        if self.mouth_connection:
            self.mouth_connection.add_fluid(fluid_type, amount)
    
    def tick(self, dt: float = 1.0):
        # Автоматическая передача в желудок
        if self.contents.total() > 0 and self.stomach_connection:
            amount = self.contents.total() * 0.5 * dt
            fluids = dict(self.contents.components)
            if fluids:
                transferred = self.stomach_connection.add_fluid(
                    max(fluids.items(), key=lambda x: x[1])[0], amount
                )
                self.contents.remove(transferred)
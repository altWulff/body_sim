# === anatomy/reproductive/scrotum.py ===
from dataclasses import dataclass, field
from typing import List, Dict, Any

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.fluids import Fluid, FluidType
from body_sim.core.events import EventBus


@dataclass
class Testicle:
    size: float = 1.0
    stored_fluids: Dict[FluidType, float] = field(default_factory=dict)
    production_rate: float = 0.1

    def produce(self, dt: float):
        self.stored_fluids[FluidType.SEMEN] = (
            self.stored_fluids.get(FluidType.SEMEN, 0) + self.production_rate * dt
        )

    def drain(self, amount: float) -> float:
        available = self.stored_fluids.get(FluidType.SEMEN, 0)
        take = min(amount, available)
        self.stored_fluids[FluidType.SEMEN] = available - take
        return take


@dataclass
class Scrotum(AnatomicalComponent):
    testicles: List[Testicle] = field(default_factory=lambda: [Testicle(), Testicle()])
    is_internal: bool = False
    total_storage_capacity: float = 100.0

    def __post_init__(self):
        super().__init__("scrotum", max_volume=self.total_storage_capacity)

    def drain_fluid(self, amount: float) -> List[Fluid]:
        drained = []
        per_testicle = amount / len(self.testicles) if self.testicles else 0

        for testicle in self.testicles:
            volume = testicle.drain(per_testicle)
            if volume > 0:
                drained.append(
                    Fluid(
                        fluid_type=FluidType.SEMEN,
                        volume=volume,
                        source_component=self.component_id,
                    )
                )
        return drained

    def update(self, delta_time: float, event_bus: EventBus, arousal: float = 0):
        super().update(delta_time, event_bus)
        for testicle in self.testicles:
            if arousal > 0.3:
                testicle.produce(delta_time)

    @property
    def total_stored(self) -> float:
        return sum(t.stored_fluids.get(FluidType.SEMEN, 0) for t in self.testicles)

    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update(
            {
                "testicles_count": len(self.testicles),
                "total_stored": self.total_stored,
                "is_internal": self.is_internal,
            }
        )
        return base

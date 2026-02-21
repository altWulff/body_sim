"""
Мошонка - хранилище яичек.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from body_sim.core.enums import ScrotumType, TesticleSize, FluidType
from .testicle import Testicle


@dataclass
class Scrotum:
    scrotum_type: ScrotumType = field(default=ScrotumType.STANDARD)
    has_testicles: bool = True
    testicle_size: TesticleSize = TesticleSize.AVERAGE
    testicle_count: int = 2
    testicles: List[Testicle] = field(default_factory=list)
    is_retracted: bool = False
    scrotum_volume: float = field(init=False)
    retracts: bool = False
    swings: bool = False
    has_sheath: bool = False
    is_internal: bool = False
    has_segments: bool = False
    segment_count: int = 1

    def __post_init__(self):
        stats = self.scrotum_type
        self.retracts = stats.retracts
        self.swings = stats.swings
        self.has_sheath = stats.has_sheath
        self.is_internal = stats.is_internal
        self.has_segments = stats.has_segments
        self.segment_count = stats.segment_count
        
        if self.has_testicles and not self.testicles:
            for i in range(self.testicle_count):
                self.testicles.append(Testicle(
                    name=f"testicle_{i}",
                    size=self.testicle_size
                ))
        
        if self.testicles:
            self.scrotum_volume = sum(t.volume for t in self.testicles) * 1.5
        else:
            self.scrotum_volume = 50.0

    @property
    def total_storage_capacity(self) -> float:
        return sum(t.storage_capacity for t in self.testicles) * self.scrotum_type.capacity

    @property
    def total_stored_fluids(self) -> Dict[FluidType, float]:
        totals = {}
        for testicle in self.testicles:
            for fluid_type, amount in testicle.stored_fluids.items():
                totals[fluid_type] = totals.get(fluid_type, 0) + amount
        return totals

    @property
    def total_stored_volume(self) -> float:
        return sum(self.total_stored_fluids.values())

    @property
    def fullness(self) -> float:
        if self.total_storage_capacity <= 0:
            return 0
        return self.total_stored_volume / self.total_storage_capacity

    def get_testicle(self, index: int) -> Optional[Testicle]:
        if 0 <= index < len(self.testicles):
            return self.testicles[index]
        return None

    def drain_fluid(self, fluid_type: FluidType, amount: float) -> float:
        total_available = sum(t.stored_fluids.get(fluid_type, 0) for t in self.testicles)
        if total_available <= 0:
            return 0
        
        taken_total = 0
        ratio = amount / total_available
        
        for testicle in self.testicles:
            available = testicle.stored_fluids.get(fluid_type, 0)
            take = available * ratio
            testicle.stored_fluids[fluid_type] = available - take
            taken_total += take
        
        return taken_total

    def add_testicle_fluid_production(self, testicle_idx: int, fluid_type: FluidType, rate: float) -> None:
        testicle = self.get_testicle(testicle_idx)
        if testicle:
            testicle.add_fluid_production(fluid_type, rate)

    def overheat_testicle(self, index: int, amount: float = 0.1) -> None:
        testicle = self.get_testicle(index)
        if testicle:
            testicle.overheat(amount)

    def damage_testicle(self, index: int, amount: float) -> None:
        testicle = self.get_testicle(index)
        if testicle:
            testicle.damage(amount)

    def heal_testicle(self, index: int, amount: float) -> None:
        testicle = self.get_testicle(index)
        if testicle:
            testicle.heal(amount)

    def tick(self, dt: float, arousal: float = 0.0) -> None:
        for testicle in self.testicles:
            testicle.tick(dt, arousal)
        self.is_retracted = arousal > 0.95
        
    @property
    def total_pressure(self) -> float:
        if not self.testicles:
            return 0.0
        return sum(t.pressure for t in self.testicles) / len(self.testicles)
    
    @property
    def pressure_multiplier(self) -> float:
        if not self.testicles:
            return 1.0
        return max(t.pressure_multiplier for t in self.testicles)
    
    @property
    def pressure_tier(self) -> str:
        tiers = [t.pressure_tier for t in self.testicles]
        if "rupture_risk" in tiers:
            return "rupture_risk"
        elif "critical" in tiers:
            return "critical"
        elif "high" in tiers:
            return "high"
        elif "low" in tiers:
            return "low"
        return "normal"
"""
Яички - производство и хранение спермы.
"""
from dataclasses import dataclass, field
from typing import Dict
from body_sim.core.enums import FluidType, TesticleSize


@dataclass
class Testicle:
    name: str = "testicle"
    size: TesticleSize = TesticleSize.AVERAGE
    length: float = field(init=False)
    width: float = field(init=False)
    volume: float = field(init=False)
    fluid_production_rates: Dict[FluidType, float] = field(default_factory=dict)
    storage_capacity: float = field(init=False)
    stored_fluids: Dict[FluidType, float] = field(default_factory=dict)
    temperature: float = 34.0
    is_overheated: bool = False
    is_damaged: bool = False
    damage_level: float = 0.0
    sperm_count: float = 100.0  # миллионы
    sensitivity: float = 1.0
    
    # Система давления
    pressure: float = 0.0
    max_pressure: float = 100.0
    pressure_tier: str = "normal"

    def __post_init__(self):
        self.length = self.size.length
        self.width = self.length * 0.7
        self.volume = self.size.volume
        self.storage_capacity = self.volume * 2.0
        
        if not self.fluid_production_rates:
            self.fluid_production_rates = {FluidType.CUM: 0.3}
        
        for fluid_type in self.fluid_production_rates:
            self.stored_fluids[fluid_type] = 0.0

    @property
    def total_stored(self) -> float:
        return sum(self.stored_fluids.values())

    @property
    def fullness(self) -> float:
        return self.total_stored / self.storage_capacity if self.storage_capacity > 0 else 0

    @property
    def can_produce(self) -> bool:
        return not self.is_overheated and self.damage_level < 0.8

    def produce(self, dt: float, arousal: float = 0.0, stimulation: float = 1.0) -> Dict[FluidType, float]:
        produced = {}
        if not self.can_produce:
            return produced
        
        arousal_boost = 1.0 + (arousal * 2.0)
        temp_penalty = 0.5 if self.is_overheated else 1.0
        damage_penalty = 1.0 - (self.damage_level * 0.5)

        for fluid_type, base_rate in self.fluid_production_rates.items():
            effective_rate = base_rate * arousal_boost * stimulation * temp_penalty * damage_penalty
            amount = effective_rate * dt
            available_space = self.storage_capacity - self.total_stored
            amount = min(amount, available_space * 0.9)
            
            self.stored_fluids[fluid_type] = self.stored_fluids.get(fluid_type, 0) + amount
            produced[fluid_type] = amount
        
        return produced

    def drain(self, fluid_type: FluidType, amount: float) -> float:
        available = self.stored_fluids.get(fluid_type, 0)
        taken = min(amount, available)
        self.stored_fluids[fluid_type] = available - taken
        return taken

    def drain_all(self, ratio: float = 1.0) -> Dict[FluidType, float]:
        taken = {}
        for fluid_type, amount in self.stored_fluids.items():
            take_amount = amount * ratio
            self.stored_fluids[fluid_type] = amount - take_amount
            taken[fluid_type] = take_amount
        return taken

    def add_fluid_production(self, fluid_type: FluidType, rate: float) -> None:
        self.fluid_production_rates[fluid_type] = rate
        if fluid_type not in self.stored_fluids:
            self.stored_fluids[fluid_type] = 0.0

    def overheat(self, amount: float = 0.1) -> None:
        self.temperature += amount
        if self.temperature > 37.5:
            self.is_overheated = True

    def cool_down(self, amount: float = 0.2) -> None:
        self.temperature = max(34.0, self.temperature - amount)
        if self.temperature < 36.5:
            self.is_overheated = False

    def damage(self, amount: float) -> None:
        self.damage_level = min(1.0, self.damage_level + amount)
        self.is_damaged = self.damage_level > 0.1

    def heal(self, amount: float) -> None:
        self.damage_level = max(0.0, self.damage_level - amount)
        self.is_damaged = self.damage_level > 0.1

    def tick(self, dt: float, arousal: float = 0.0) -> None:
        if self.temperature > 34.5:
            self.temperature -= 0.05 * dt
        self.produce(dt, arousal)
        self.update_pressure()
        
    def update_pressure(self) -> None:
        """Обновить давление на основе заполненности."""
        if self.storage_capacity <= 0:
            self.pressure = 0.0
            return
        
        fullness = self.fullness
        
        if fullness < 0.5:
            self.pressure = fullness * 20
            self.pressure_tier = "low"
        elif fullness < 0.8:
            self.pressure = 10 + (fullness - 0.5) * 100
            self.pressure_tier = "normal"
        elif fullness < 0.95:
            self.pressure = 40 + (fullness - 0.8) * 300
            self.pressure_tier = "high"
        elif fullness < 1.0:
            self.pressure = 85 + (fullness - 0.95) * 200
            self.pressure_tier = "critical"
        else:
            overflow = (self.total_stored - self.storage_capacity) / self.storage_capacity
            self.pressure = 95 + overflow * 100
            self.pressure_tier = "rupture_risk"
            
            if self.pressure > 120 and not self.is_damaged:
                self.damage(0.1)
    
    @property
    def pressure_multiplier(self) -> float:
        """Множитель силы эякуляции на основе давления."""
        if self.pressure < 20:
            return 0.5 + (self.pressure / 40)
        elif self.pressure < 80:
            return 1.0 + ((self.pressure - 20) / 60) * 0.5
        else:
            return 1.5 + min((self.pressure - 80) / 40, 1.0)
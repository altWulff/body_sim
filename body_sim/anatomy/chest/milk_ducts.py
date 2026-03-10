from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class DuctState(Enum):
    NORMAL = "normal"
    DILATED = "dilated"
    PROLAPSED = "prolapsed"
    SEVERED = "severed"
    EXTERNAL = "external"


@dataclass
class MilkDuct:
    id: int
    state: DuctState = DuctState.NORMAL
    diameter: float = 0.05  # см
    length: float = 2.0  # см
    milk_flow_rate: float = 0.0
    prolapse_length: float = 0.0
    connected_to: Optional[str] = None
    internal_volume: float = 0.0

    def dilate(self, factor: float):
        self.diameter *= factor
        if self.diameter > 0.3:
            self.state = DuctState.DILATED

    def prolapse(self, amount: float):
        if self.state != DuctState.SEVERED:
            self.prolapse_length += amount
            self.state = DuctState.PROLAPSED

    def sever(self, portal_id: Optional[str] = None):
        self.state = DuctState.SEVERED
        self.connected_to = portal_id

    def reconnect(self):
        if self.state == DuctState.SEVERED:
            self.state = DuctState.NORMAL
            self.connected_to = None

    def receive_milk(self, amount: float) -> float:
        overflow = 0.0
        self.internal_volume += amount
        max_volume = 3.14 * (self.diameter / 2) ** 2 * self.length * 1000
        if self.internal_volume > max_volume:
            overflow = self.internal_volume - max_volume
            self.internal_volume = max_volume
        return overflow


@dataclass
class MilkDuctSystem:
    nipple_ducts: List[MilkDuct] = field(default_factory=list)
    collecting_ducts: List[MilkDuct] = field(default_factory=list)
    lactiferous_sinuses: float = 0.0  # Резервуары

    def __post_init__(self):
        if not self.nipple_ducts:
            self.nipple_ducts = [MilkDuct(id=i) for i in range(18)]

    def total_prolapse(self) -> float:
        return sum(d.prolapse_length for d in self.nipple_ducts)

    def express(self, pressure: float) -> float:
        if pressure > 2.0:
            for duct in self.nipple_ducts:
                if duct.diameter > 0.2 and duct.state == DuctState.DILATED:
                    duct.prolapse(0.1 * pressure)

        total = self.lactiferous_sinuses
        self.lactiferous_sinuses = 0

        for duct in self.nipple_ducts:
            if duct.state == DuctState.NORMAL:
                total += duct.internal_volume
                duct.internal_volume = 0
        return total

    def get_flow_capacity(self) -> float:
        active = [
            d
            for d in self.nipple_ducts
            if d.state not in [DuctState.SEVERED, DuctState.EXTERNAL]
        ]
        return sum(3.14 * (d.diameter / 2) ** 2 * 10 for d in active)

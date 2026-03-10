# === anatomy/reproductive/uterus.py ===
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum, auto
import math

from body_sim.anatomy.base import AnatomicalComponent, BaseComponent
from body_sim.core.fluids import Fluid, FluidType
from body_sim.core.events import EventBus, Event, EventType
from body_sim.anatomy.reproductive.ovary import Ovary
from body_sim.anatomy.reproductive.tubes import FallopianTube


class UterusState(Enum):
    NORMAL = auto()
    EMPTY = auto()
    TENSE = auto()
    LEAKING = auto()
    OVERPRESSURED = auto()
    DESCENDED = auto()
    PROLAPSED = auto()
    EVERTED = auto()
    INVERTED = auto()


class UterusInflationStatus(Enum):
    NORMAL = "normal"
    STRETCHED = "stretched"
    DISTENDED = "distended"
    HYPERDISTENDED = "hyperdistended"
    RUPTURE_RISK = "rupture_risk"
    RUPTURED = "ruptured"


@dataclass
class UterineWall:
    thickness: float = 1.0
    elasticity: float = 1.0
    integrity: float = 1.0
    stretch_ratio: float = 1.0
    fatigue: float = 0.0
    plasticity: float = 0.3
    peak_stretch: float = 1.0
    is_permanently_stretched: bool = False

    def can_stretch(self, target_ratio: float) -> bool:
        max_stretch = 500.0 * self.elasticity * self.integrity
        return target_ratio <= max_stretch

    def stretch(self, ratio: float) -> bool:
        if ratio > 500.0:
            self.integrity = max(0.0, self.integrity - 0.1)
            return False

        if ratio > 100.0:
            integrity_loss = (ratio - 100.0) * 0.001
            self.integrity = max(0.01, self.integrity - integrity_loss)
        elif ratio > 10.0:
            integrity_loss = (ratio - 10.0) * 0.0001
            self.integrity = max(0.1, self.integrity - integrity_loss)

        self.stretch_ratio = ratio
        self.peak_stretch = max(self.peak_stretch, ratio)
        self.fatigue = min(1.0, self.fatigue + (ratio - 1.0) * 0.01)

        if ratio >= 2.0:
            self.is_permanently_stretched = True
        return True

    def recover(self, dt: float):
        self.fatigue = max(0.0, self.fatigue - 0.01 * dt)
        if self.stretch_ratio > 1.0:
            elastic_part = (self.stretch_ratio - 1.0) * (1.0 - self.plasticity)
            plastic_part = (self.stretch_ratio - 1.0) * self.plasticity
            recovery = 0.001 * self.elasticity * dt
            new_elastic = max(0, elastic_part - recovery)
            self.stretch_ratio = 1.0 + plastic_part + new_elastic

    def get_skin_tension(self) -> float:
        if self.stretch_ratio <= 1.0:
            return 0.0
        return min(1.0, (self.stretch_ratio - 1.0) / 3.0)


@dataclass
class Cervix:
    length: float = 3.0
    diameter: float = 2.5
    max_dilation: float = 10.0
    current_dilation: float = 0.0
    gape_diameter: float = 0.0
    inflation_ratio: float = 1.0

    def dilate(self, amount: float) -> bool:
        new_dilation = min(self.current_dilation + amount, self.max_dilation)
        self.current_dilation = new_dilation
        self.gape_diameter = max(0.1, new_dilation)
        return True

    def contract(self):
        self.current_dilation = max(0.0, self.current_dilation - 0.5)
        self.gape_diameter = max(0.1, self.current_dilation)

    def inflate(self, ratio: float):
        self.inflation_ratio = max(1.0, min(ratio, 3.0))
        self.diameter *= self.inflation_ratio

    @property
    def is_open(self) -> bool:
        return self.gape_diameter > 0.15

    @property
    def effective_gape(self) -> float:
        return self.gape_diameter if self.is_open else 0.0


@dataclass
class Uterus(AnatomicalComponent):
    base_length: float = 7.0
    base_width: float = 5.0
    base_depth: float = 3.0
    cavity_volume: float = 50.0

    cervix: Cervix = field(default_factory=Cervix)
    walls: UterineWall = field(default_factory=UterineWall)
    left_tube: Optional[FallopianTube] = None
    right_tube: Optional[FallopianTube] = None
    left_ovary: Optional[Ovary] = None
    right_ovary: Optional[Ovary] = None

    state: UterusState = field(default=UterusState.NORMAL)
    inflation_status: UterusInflationStatus = field(
        default=UterusInflationStatus.NORMAL
    )

    inflation_ratio: float = 1.0
    tube_fill_ratio: float = 0.3
    peristalsis_strength: float = 0.5

    inserted_objects: List[Any] = field(default_factory=list)
    _listeners: Dict[str, List[Callable]] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        super().__init__("uterus", max_volume=5000)
        if self.left_tube is None:
            self.left_tube = FallopianTube(side="left")
        if self.right_tube is None:
            self.right_tube = FallopianTube(side="right")
        if self.left_ovary is None:
            self.left_ovary = Ovary(side="left")
        if self.right_ovary is None:
            self.right_ovary = Ovary(side="right")

    @property
    def current_volume(self) -> float:
        if self.state in (UterusState.EVERTED, UterusState.INVERTED):
            return self.cavity_volume * 0.1
        stretch_factor = self.inflation_ratio**3
        return self.cavity_volume * stretch_factor * (self.walls.stretch_ratio**3)

    def on(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)

    def _emit(self, event: str, **data):
        for cb in self._listeners.get(event, []):
            cb(self, **data)

    def inflate(self, ratio: float) -> bool:
        if ratio > 4.0:
            return False
        old_ratio = self.inflation_ratio
        self.inflation_ratio = ratio
        self.cervix.inflate(ratio)

        if self.left_tube:
            self.left_tube.inflate(ratio)
        if self.right_tube:
            self.right_tube.inflate(ratio)

        self._update_inflation_status()

        if ratio > old_ratio:
            self._emit("inflated", old_ratio=old_ratio, new_ratio=ratio)
        return True

    def _update_inflation_status(self):
        total_stretch = self.inflation_ratio * self.walls.stretch_ratio

        if total_stretch < 1.5:
            self.inflation_status = UterusInflationStatus.NORMAL
        elif total_stretch < 2.0:
            self.inflation_status = UterusInflationStatus.STRETCHED
        elif total_stretch < 2.5:
            self.inflation_status = UterusInflationStatus.DISTENDED
        elif total_stretch < 3.0:
            self.inflation_status = UterusInflationStatus.HYPERDISTENDED
        elif total_stretch < 500.0:
            self.inflation_status = UterusInflationStatus.RUPTURE_RISK
        else:
            self.inflation_status = UterusInflationStatus.RUPTURED

    # === anatomy/reproductive/uterus.py ===

    def add_fluid(self, fluid: Fluid) -> float:
        """Добавить жидкость с распределением по трубам."""
        if fluid.volume <= 0:
            return 0.0

        # Распределение: часть в матку, часть в трубы
        to_uterus = fluid.volume * (1 - self.tube_fill_ratio)
        to_tubes = fluid.volume * self.tube_fill_ratio

        # Создаем копию жидкости для матки с нужным объемом
        uterus_fluid = Fluid(
            fluid_type=fluid.fluid_type,
            volume=to_uterus,
            source_component=fluid.source_component,
            properties=fluid.properties.copy(),
        )

        overflow = super().add_fluid(uterus_fluid)

        # Остаток от переполнения матки идет в трубы
        if overflow > 0:
            to_tubes += overflow

        # Распределяем в трубы
        if to_tubes > 0:
            per_tube = to_tubes / 2

            if self.left_tube:
                self.left_tube.contained_fluid += per_tube
                # Передача в яичник если есть связь
                if hasattr(self.left_tube, "ovary") and self.left_tube.ovary:
                    tube_fluid = Fluid(
                        fluid_type=fluid.fluid_type,
                        volume=per_tube,
                        source_component=fluid.source_component,
                    )
                    self.left_tube.ovary.add_fluid(tube_fluid)

            if self.right_tube:
                self.right_tube.contained_fluid += per_tube
                if hasattr(self.right_tube, "ovary") and self.right_tube.ovary:
                    tube_fluid = Fluid(
                        fluid_type=fluid.fluid_type,
                        volume=per_tube,
                        source_component=fluid.source_component,
                    )
                    self.right_tube.ovary.add_fluid(tube_fluid)

        return overflow

    def stretch(self, ratio: float) -> bool:
        return self.walls.stretch(ratio)

    def evert(self):
        self.state = UterusState.EVERTED
        self._emit("eversion")

    def prolapse(self, degree: float):
        if degree > 0.7:
            self.state = UterusState.EVERTED
            self.evert()
        elif degree > 0.3:
            self.state = UterusState.PROLAPSED
        else:
            self.state = UterusState.DESCENDED

    def insert_object(self, obj: Any) -> bool:
        if self.state == UterusState.EVERTED:
            return False
        obj_volume = getattr(obj, "volume", 0)
        if obj_volume > self.available_volume:
            return False
        self.inserted_objects.append(obj)
        return True

    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)

        self.walls.recover(delta_time)

        if self.left_tube:
            self.left_tube.update(delta_time, event_bus)
        if self.right_tube:
            self.right_tube.update(delta_time, event_bus)
        if self.left_ovary:
            self.left_ovary.update(delta_time, event_bus)
        if self.right_ovary:
            self.right_ovary.update(delta_time, event_bus)

        if self.peristalsis_strength > 0 and self.fluids:
            for tube in [self.left_tube, self.right_tube]:
                if tube and self.fluids:
                    transfer_amount = min(
                        0.1 * delta_time, sum(f.volume for f in self.fluids)
                    )
                    if transfer_amount > 0:
                        tube.receive_backflow(transfer_amount)
                        self.remove_fluid(transfer_amount)

        self._update_inflation_status()

    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update(
            {
                "state": self.state.name,
                "inflation_status": self.inflation_status.value,
                "inflation_ratio": self.inflation_ratio,
                "wall_stretch": self.walls.stretch_ratio,
                "integrity": self.walls.integrity,
                "cervix_dilation": self.cervix.current_dilation,
                "cervix_open": self.cervix.is_open,
                "left_tube": self.left_tube.get_state() if self.left_tube else None,
                "right_tube": self.right_tube.get_state() if self.right_tube else None,
                "left_ovary": self.left_ovary.get_state() if self.left_ovary else None,
                "right_ovary": (
                    self.right_ovary.get_state() if self.right_ovary else None
                ),
                "objects_inside": len(self.inserted_objects),
            }
        )
        return base

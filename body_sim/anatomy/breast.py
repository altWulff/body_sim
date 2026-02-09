# body_sim/anatomy/breast.py
"""
Основной класс груди с физикой.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional, TYPE_CHECKING
import math
import cmath

from body_sim.core.enums import CupSize, BreastState, FluidType
from body_sim.core.fluids import FluidMixture, BreastFluid, FLUID_DEFS
from body_sim.core.constants import PRESSURE_LEAK_MIN, MAX_SAG
from body_sim.anatomy.nipple import Areola
from body_sim.systems.lactation import LactationSystem
from body_sim.systems.inflation import InflationSystem
from body_sim.systems.insertion import InsertionManager
from body_sim.systems.pressure import PressureSystem, get_pressure_tier, apply_pressure_to_nipple
from body_sim.systems.physics import calc_pressure, calc_sag_target

if TYPE_CHECKING:
    pass


@dataclass
class Breast:
    cup: CupSize
    areola: Areola
    base_elasticity: float = 1.0
    leak_factor: float = 20.0
    
    mixture: FluidMixture = field(default_factory=FluidMixture)
    lactation: LactationSystem = field(default_factory=LactationSystem)
    inflation: InflationSystem = field(default_factory=InflationSystem)
    insertion_manager: InsertionManager = field(default_factory=InsertionManager)
    
    _listeners: Dict[str, List[Callable]] = field(default_factory=dict, repr=False)
    _state: BreastState = BreastState.EMPTY
    _elasticity: float = field(init=False)
    _sag: float = field(init=False)
    _base_volume: float = field(init=False)
    _max_volume: float = field(init=False)
    _last_dynamic_cup: CupSize = field(init=False)
    _pressure_system: PressureSystem = field(default_factory=PressureSystem)
    
    auto_inflate: bool = True
    inflate_ratio_per_100ml: float = 0.05

    def __post_init__(self):
        self._base_volume = self.cup.base_volume
        self._max_volume = self._base_volume * 1.5
        self._elasticity = self.base_elasticity
        self._sag = 0.0
        self._last_dynamic_cup = self.cup

    def on(self, event: str, callback: Callable[..., Any]) -> None:
        self._listeners.setdefault(event, []).append(callback)
    
    def _emit(self, event: str, **data: Any) -> None:
        for cb in self._listeners.get(event, []):
            cb(self, **data)

    @property
    def state(self) -> BreastState:
        return self._state
    
    @property
    def filled(self) -> float:
        return self.mixture.total()
    
    @property
    def volume(self) -> float:
        base_volume = self._base_volume
        
        if self.filled <= 0:
            return base_volume + self.insertion_manager.total_volume
        
        fill_ratio = min(self.filled / self._max_volume, 1.0)
        normal_stretch = 1.0 + (self.inflation.stretch_ratio - 1.0) * 0.5
        
        fluid_volume = (self._max_volume - base_volume) * fill_ratio * normal_stretch
        objects_volume = self.insertion_manager.total_volume
        
        return base_volume + fluid_volume + objects_volume
    
    @property
    def dynamic_cup(self) -> CupSize:
        effective_volume = self.volume
        for cup in reversed(list(CupSize)):
            if effective_volume >= cup.base_volume:
                return cup
        return CupSize.AAA
    
    @property
    def sag(self) -> float:
        return self._sag
    
    @property
    def elasticity(self) -> float:
        return self._elasticity

    @property
    def available_volume(self) -> float:
        return self._max_volume - self.filled

    @property
    def can_inflate(self) -> bool:
        return self.inflation.stretch_ratio < self.inflation.max_stretch

    def pressure(self, defs: Dict[FluidType, BreastFluid] = FLUID_DEFS) -> float:
        viscosity = self.mixture.viscosity(defs)
        return calc_pressure(
            filled=self.filled,
            volume=self._base_volume,
            viscosity=viscosity,
            elasticity=self._elasticity,
            sag=self._sag
        )
    
    def has_leak_outlet(self) -> bool:
        return bool(self.areola.nipples)

    def _update_sag(self, defs: Dict[FluidType, BreastFluid], dt: float) -> None:
        if self.filled <= 0:
            self._sag = max(0.0, self._sag - 0.1 * dt)
            return
        
        fill_ratio = min(self.filled / self.volume, 1.0)
        
        total = self.mixture.total()
        avg_density = 1.0
        if total > 0:
            avg_density = self.mixture.density(defs)
        
        target = calc_sag_target(self, fill_ratio, avg_density)
        
        inertia = 0.05 * dt
        if self._sag > 0.5:
            inertia *= 0.5
        
        self._sag += (target - self._sag) * inertia
        self._sag = max(0.0, min(self._sag, MAX_SAG))
    
    def _update_elasticity(self, dt: float) -> None:
        loss_factor = self._sag * 0.4  # ELASTICITY_SAG_LOSS
        target = max(self.base_elasticity * (1.0 - loss_factor), 0.1)
        self._elasticity += (target - self._elasticity) * 0.2 * dt  # ELASTICITY_ADJUST_RATE
        
    def _calc_leak_rate(self, pressure: float, viscosity: float) -> float:
        if not self.has_leak_outlet():
            return 0.0
        
        leakage_reduction = self.insertion_manager.total_leakage_reduction
        if leakage_reduction >= 1.0:
            return 0.0
        
        total_flow = 0.0
        
        for nipple in self.areola.nipples:
            if not nipple.is_open:
                continue
            
            effective_gape = nipple.effective_gape
            if effective_gape <= 0:
                continue
            
            radius = effective_gape / 2
            area = math.pi * radius ** 2
            
            if pressure < PRESSURE_LEAK_MIN:
                continue
            
            pressure_diff = pressure - PRESSURE_LEAK_MIN + 0.1
            flow_efficiency = (nipple.gape_diameter / nipple.width) ** 2
            
            flow_rate = 0.8 * area * pressure_diff * flow_efficiency / max(viscosity, 0.1)
            total_flow += max(0.0, flow_rate)
        
        total_flow *= (1.0 - leakage_reduction)
        return total_flow * (self.leak_factor / 20.0)
    
    def _determine_state(self, pressure: float) -> BreastState:
        if self.filled <= 0:
            return BreastState.EMPTY
        
        if pressure < 0.5:  # PRESSURE_NORMAL
            return BreastState.NORMAL
        if pressure < 1.0:  # PRESSURE_TENSE
            return BreastState.TENSE
        
        has_open_nipple = any(
            nipple.is_open for nipple in self.areola.nipples
        ) if self.has_leak_outlet() else False
        
        if not has_open_nipple:
            return BreastState.OVERPRESSURED if not self.has_leak_outlet() else BreastState.TENSE
        
        if pressure >= PRESSURE_LEAK_MIN:
            return BreastState.LEAKING
        
        return BreastState.TENSE

    def tick(self, defs: Dict[FluidType, BreastFluid] = FLUID_DEFS, dt: float = 1.0) -> Dict[str, Any]:
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")
        
        # 1. Физика формы
        self._update_sag(defs, dt)
        self._update_elasticity(dt)
        
        # 2. Лактация
        self.lactation.tick(self, defs, dt)
        
        # 3. Давление и соски
        pressure = self.pressure(defs)
        pressure += self.insertion_manager.pressure_modifier
        tier = get_pressure_tier(pressure)
        
        for nipple in self.areola.nipples:
            apply_pressure_to_nipple(nipple, tier, dt)
        
        self.areola._update_diameter()
        
        tier_changed = self._pressure_system.check_changed(pressure)
        if tier_changed:
            self._emit("pressure_tier_change", tier=tier)
        
        # 4. Состояние
        new_state = self._determine_state(pressure)
        old_state = self._state
        
        if new_state != old_state:
            self._state = new_state
            self._emit("state_change", old=old_state, new=new_state)
            
            if new_state == BreastState.LEAKING:
                self._emit("leak_start")
            elif old_state == BreastState.LEAKING:
                self._emit("leak_end")
        
        # 5. Утечка
        leaked = 0.0
        if self._state == BreastState.LEAKING:
            viscosity = self.mixture.viscosity(defs)
            leak_rate = self._calc_leak_rate(pressure, viscosity)
            max_leak = self.filled * leak_rate * dt
            leaked = min(max_leak, self.filled)
            
            if leaked > 0:
                self.mixture.remove(leaked)
                self._emit("leak", amount=leaked)
        
        # 6. Стимуляция лактации
        if self.lactation.state in (2, 3):  # ACTIVE, ENGORGED
            self.lactation.stimulate()
        
        # 7. Обновление размера
        current_cup = self.dynamic_cup
        if current_cup != self._last_dynamic_cup:
            self._emit("cup_changed", old=self._last_dynamic_cup, new=current_cup)
            self._last_dynamic_cup = current_cup

        self.inflation.apply_stretch(self, dt)

        return {
            "state": self._state.name,
            "pressure": round(pressure, 2),
            "filled": round(self.filled, 1),
            "sag": round(self._sag, 3),
            "leaked": round(leaked, 2),
            "cup": self.dynamic_cup.name,
            "elasticity": round(self._elasticity, 2),
        }

    def add_fluid(self, fluid: 'FluidType | BreastFluid', amount: float) -> float:
        if amount <= 0:
            return 0.0
        
        fluid_type = fluid.fluid_type if isinstance(fluid, BreastFluid) else fluid
        
        normal_available = self.available_volume
        
        if amount <= normal_available:
            self.mixture.add(fluid_type, amount)
            self._emit("fluid_added", amount=amount, inflated=False)
            return amount
        
        excess = amount - normal_available
        
        if not self.auto_inflate or not self.can_inflate:
            if normal_available > 0:
                self.mixture.add(fluid_type, normal_available)
                self._emit("fluid_added", amount=normal_available, inflated=False, overflow=excess)
                return normal_available
            return 0.0
        
        inflate_amount = self._calculate_inflation_for_volume(excess)
        old_stretch = self.inflation.stretch_ratio
        self._apply_inflation(inflate_amount)
        
        self.mixture.add(fluid_type, amount)
        
        new_stretch = self.inflation.stretch_ratio
        self._emit("fluid_added", amount=amount, inflated=True, excess=excess,
                  stretch_before=old_stretch, stretch_after=new_stretch)
        
        if new_stretch >= self.inflation.max_stretch * 0.95:
            self._emit("max_inflation_warning")
        
        return amount

    def remove_fluid(self, amount: float) -> float:
        if amount <= 0:
            return 0.0
        actual = min(amount, self.filled)
        self.mixture.remove(actual)
        return actual
    
    def _calculate_inflation_for_volume(self, excess_volume: float) -> float:
        base_inflate = excess_volume * self.inflate_ratio_per_100ml / 100.0
        current_stretch = self.inflation.stretch_ratio
        difficulty = 1.0 + (current_stretch - 1.0) * 2.0
        return base_inflate * difficulty
    
    def _apply_inflation(self, inflate_amount: float) -> None:
        self.inflation.stretch_ratio = min(
            self.inflation.max_stretch,
            self.inflation.stretch_ratio + inflate_amount
        )
        
        base_normal_max = self._base_volume * 1.5
        self._max_volume = base_normal_max * self.inflation.stretch_ratio
        
        stretch_penalty = (self.inflation.stretch_ratio - 1.0) * 0.3
        self._elasticity = max(0.1, self.base_elasticity - stretch_penalty)
        
        if self.areola:
            base_diameter = self.areola.base_diameter
            target_diameter = base_diameter * cmath.sqrt(self.inflation.stretch_ratio)
            self.areola._current_diameter = target_diameter
        
        self._emit("inflation", stretch_ratio=self.inflation.stretch_ratio,
                  new_max_volume=self._max_volume)
                  
# === chest/breast_row.py ===
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum, auto
import math

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus, EventType, Event
from body_sim.core.fluids import FluidMixture, FluidType
from body_sim.systems.inflation import InflationSystem, InflationProfile
from body_sim.systems.lactation import LactationSystem, LactationProfile
from body_sim.systems.insertion import InsertionManager
from body_sim.systems.physics import PhysicsEngine
from body_sim.systems.pressure import PressureController

from .cup_size import CupSize
from .nipple import Nipple, NipplePlug
from .areola import Areola
from .milk_ducts import MilkDuctSystem


class BreastState(Enum):
    EMPTY = auto()
    NORMAL = auto()
    TENSE = auto()
    LEAKING = auto()
    OVERPRESSURED = auto()


@dataclass
class BreastRow(AnatomicalComponent):
    index: int = 0
    side: str = "left"
    cup_size: CupSize = field(default=CupSize.C)

    areola: Areola = field(default_factory=Areola)
    duct_system: MilkDuctSystem = field(default_factory=MilkDuctSystem)

    firmness: float = 1.0
    glandular_density: float = 0.6

    inflation: InflationSystem = field(init=False, repr=False)
    lactation: LactationSystem = field(init=False, repr=False)
    insertion: InsertionManager = field(init=False, repr=False)
    pressure_controller: PressureController = field(init=False, repr=False)

    mixture: FluidMixture = field(default_factory=FluidMixture)
    current_milk_volume: float = 0.0

    arousal: float = field(default=0.0, repr=False)
    pleasure: float = field(default=0.0, repr=False)
    sensitivity: float = 1.2

    _state: BreastState = field(default=BreastState.EMPTY, repr=False)
    _auto_inflate: bool = field(default=True, repr=False)
    _sag: float = field(default=0.0, repr=False)
    _max_volume: float = field(init=False, repr=False)
    _base_volume: float = field(init=False, repr=False)
    _elasticity: float = field(init=False, repr=False)
    _last_current_cup: CupSize = field(init=False, repr=False)

    _listeners: Dict[str, List[Callable]] = field(default_factory=dict, repr=False)
    _event_bus: Optional[EventBus] = field(default=None, repr=False)

    PRESSURE_NORMAL = 0.5  # Норма
    PRESSURE_TENSE = 1.2  # Напряжение (было 1.0)
    PRESSURE_LEAK_MIN = 3.0  # Протечка (было 1.5/0.8)
    PRESSURE_OVERFULL = 2.0  # Переполнение (новое промежуточное)
    MAX_SAG = 1.0
    GIGA_LIMIT = 500000
    LEAK_MULTIPLIER = 0.5  # Было 5.0 - уменьшили скорость утечки

    def __post_init__(self):
        base_vol = self.cup_size.base_volume
        super().__init__(
            f"{self.side}_breast_{self.index}",
            base_volume=base_vol,
            max_volume_multiplier=1.5,
            sensitivity=self.sensitivity,
        )
        self._base_volume = base_vol
        self._max_volume = base_vol * 1.5
        self._elasticity = 1.0
        self._last_current_cup = self.cup_size

        self.inflation = InflationSystem(
            InflationProfile(max_stretch=3.0, plasticity=0.3, base_elasticity=1.0)
        )
        self.lactation = LactationSystem(LactationProfile())
        self.insertion = InsertionManager()
        self.pressure_controller = PressureController()

        self.areola.diameter = 3.0 + (self.cup_size.value / 100)
        self.areola.base_diameter = self.areola.diameter
        if not self.areola.nipples:
            self.areola.nipples = [Nipple(diameter=self.areola.diameter * 0.25)]

    def set_event_bus(self, event_bus: EventBus):
        self._event_bus = event_bus

    def _emit_local(self, event: str, **data: Any) -> None:
        for cb in self._listeners.get(event, []):
            cb(self, **data)

    def _emit_global(self, event_type: EventType, **data: Any) -> None:
        if self._event_bus:
            event = Event(type=event_type, source=self.component_id, data=data)
            self._event_bus.emit(event)

    def _emit(
        self, event_name: str, event_type: Optional[EventType] = None, **data: Any
    ) -> None:
        self._emit_local(event_name, **data)
        if event_type and self._event_bus:
            self._emit_global(event_type, **data)

    def on(self, event: str, callback: Callable[..., Any]) -> None:
        self._listeners.setdefault(event, []).append(callback)

    @property
    def filled(self) -> float:
        return max(0.0, self.mixture.total() + self.current_milk_volume)

    @property
    def volume(self) -> float:
        """Текущий физический объем груди."""
        # Объем ткани (растянутой)
        tissue_vol = self._base_volume * self.inflation.profile.stretch_ratio

        # Полость для жидкости = разница между max и тканью
        cavity_vol = self._max_volume - tissue_vol

        # Жидкость (self.mixture.total() + молоко в железах)
        fluid_vol = self.filled

        # Объем вставленных объектов
        objects_vol = getattr(self.insertion, "total_volume", 0)

        if fluid_vol <= cavity_vol:
            # Линейное заполнение до 100%
            return tissue_vol + fluid_vol + objects_vol
        else:
            # Переполнение - небольшое увеличение
            overflow = fluid_vol - cavity_vol
            return self._max_volume + overflow * 0.2 + objects_vol

    @property
    def available_volume(self) -> float:
        return max(0.0, self._max_volume - self.filled)

    @property
    def fill_ratio(self) -> float:
        if self._max_volume <= 0:
            return 0.0
        return min(1.0, self.filled / self._max_volume)

    @property
    def pressure(self) -> float:
        return self.pressure_controller.current_pressure

    @property
    def sag(self) -> float:
        return self._sag

    @property
    def elasticity(self) -> float:
        return self._elasticity

    @property
    def current_cup(self) -> CupSize:
        total_vol = self.volume
        for cup in reversed(list(CupSize)):
            if total_vol >= cup.base_volume:
                return cup
        return CupSize.AAA

    @property
    def state(self) -> BreastState:
        return self._state

    def add_fluid_by_type(
        self, fluid_type: FluidType, amount: float, source: str = None
    ) -> float:
        if amount <= 0:
            return 0.0

        if self.filled >= self.GIGA_LIMIT:
            self._emit(
                "max_capacity_reached",
                EventType.MODIFIER_APPLIED,
                limit=self.GIGA_LIMIT,
            )
            return 0.0

        # Сколько можно добавить до 100% (без растяжения)
        to_full = self._max_volume - self.filled

        # Если помещается в текущий объем - добавляем без растяжения
        if amount <= to_full:
            self.mixture.add(
                fluid_type, amount, source or getattr(self, "component_id", "unknown")
            )
            self._emit(
                "fluid_added",
                EventType.FLUID_ADDED,
                amount=amount,
                fluid_type=fluid_type.name,
                inflated=False,
            )
            return amount

        # Если не помещается и заполнение >= 90% - растягиваемся
        if self.fill_ratio >= 0.90 and self._auto_inflate:
            old_stretch = self.inflation.profile.stretch_ratio

            # Сколько нужно растянуться для избытка
            excess = amount - to_full
            inflate_amount = (excess / 100.0) * 0.05

            # Учитываем сложность растяжения
            difficulty = 1.0 + (old_stretch - 1.0) * 2.0
            inflate_amount *= difficulty

            new_stretch = old_stretch + inflate_amount
            self.inflation.apply_stretch(new_stretch)

            # Обновляем максимальный объем
            new_max = self._base_volume * 1.5 * self.inflation.profile.stretch_ratio
            self._max_volume = min(new_max, self.GIGA_LIMIT)

            self.areola._update_diameter(self.inflation.profile.stretch_ratio)

            # Теперь добавляем всё количество
            self.mixture.add(
                fluid_type, amount, source or getattr(self, "component_id", "unknown")
            )
            self._emit(
                "fluid_added",
                EventType.FLUID_ADDED,
                amount=amount,
                fluid_type=fluid_type.name,
                inflated=True,
                stretch_before=old_stretch,
                stretch_after=self.inflation.profile.stretch_ratio,
            )
            return amount

        # Если не растягиваемся - добавляем только до полного заполнения
        if to_full > 0:
            self.mixture.add(
                fluid_type, to_full, source or getattr(self, "component_id", "unknown")
            )
            self._emit(
                "fluid_added",
                EventType.FLUID_ADDED,
                amount=to_full,
                fluid_type=fluid_type.name,
                inflated=False,
                note="partial_fill",
            )
            return to_full

        return 0.02

    def express(self, amount: float, pressure: float = 1.0) -> float:
        from_ducts = self.duct_system.express(pressure)

        milk_in_mixture = self.mixture.get_amount(FluidType.MILK)
        to_remove = min(amount - from_ducts, milk_in_mixture)
        removed = 0.0
        if to_remove > 0:
            removed_dict = self.mixture.remove(to_remove, [FluidType.MILK])
            removed = sum(removed_dict.values())

        from_glands = min(amount - from_ducts - removed, self.current_milk_volume)
        self.current_milk_volume -= from_glands

        total = from_ducts + removed + from_glands

        if total > 0:
            self.areola.stimulate(0.5)
            self._emit(
                "express", EventType.FLUID_REMOVED, amount=total, fluid_type="MILK"
            )

        return total

    def stimulate(self, intensity: float = 0.1) -> dict:
        self.arousal = min(1.0, self.arousal + intensity * 0.1)
        self.pleasure = min(10.0, self.pleasure + intensity * self.sensitivity)

        self.areola.stimulate(intensity)

        temp_inflate = 1.0 + (intensity * 0.02)
        self.inflation.apply_stretch(temp_inflate)
        self.areola._update_diameter(self.inflation.profile.stretch_ratio)

        if hasattr(self.lactation, "state"):
            if self.lactation.state.value >= 2:
                self.lactation.stimulate()

        self._emit(
            "stimulated",
            EventType.MODIFIER_APPLIED,
            intensity=intensity,
            arousal=self.arousal,
            pleasure=self.pleasure,
            side=self.side,
        )

        return {
            "sensitivity": (
                sum(n.sensitivity for n in self.areola.nipples)
                if self.areola.nipples
                else 0
            ),
            "arousal": self.arousal,
            "pleasure": self.pleasure,
            "state": "stimulated",
        }

    def start_lactation(self, intensity: float = 10.0) -> None:
        try:
            if hasattr(self.lactation, "start"):
                self.lactation.start()
            elif hasattr(self.lactation, "activate"):
                self.lactation.activate()

            if hasattr(self.lactation, "profile") and hasattr(
                self.lactation.profile, "production_rate"
            ):
                self.lactation.profile.production_rate = intensity

            self._emit(
                "lactation_start", EventType.LACTATION_START, intensity=intensity
            )
        except:
            self._emit("lactation_start", None, intensity=intensity)

    def stop_lactation(self) -> None:
        try:
            if hasattr(self.lactation, "stop"):
                self.lactation.stop()
            elif hasattr(self.lactation, "deactivate"):
                self.lactation.deactivate()

            self._emit("lactation_stop", EventType.LACTATION_END)
        except:
            self._emit("lactation_stop", None)

    def _calc_leak_rate(self, pressure: float) -> float:
        """Утечка только при давлении > 3.0."""
        if not self.areola.nipples or self.filled <= 0:
            return 0.0

        # Утечка только выше порога PRESSURE_LEAK_MIN (3.0)
        if pressure < self.PRESSURE_LEAK_MIN:
            return 0.0

        open_nipples = [
            n for n in self.areola.nipples if n.is_open and n.effective_gape > 0
        ]
        if not open_nipples:
            return 0.0

        viscosity = (
            self.mixture.viscosity() if hasattr(self.mixture, "viscosity") else 1.0
        )
        total_flow = 0.0

        for nipple in open_nipples:
            effective_gape = nipple.effective_gape
            if effective_gape <= 0:
                continue

            radius = effective_gape / 2
            area = math.pi * radius**2

            # Давление сверх порога
            pressure_diff = pressure - self.PRESSURE_LEAK_MIN

            # Очень медленная утечка (коэффициент 0.2)
            flow_rate = area * pressure_diff * 0.2 / max(viscosity, 0.5)

            # Максимум 3% объема за тик
            max_flow = self.filled * 0.03
            flow_rate = min(flow_rate, max_flow)

            total_flow += max(0.0, flow_rate)

        leak_reduction = getattr(self.insertion, "total_leakage_reduction", 0)
        total_flow *= 1.0 - max(0.0, min(1.0, leak_reduction))

        return total_flow * 0.3  # Уменьшенный множитель

    def _update_sag(self, dt: float):
        if self.filled <= 0:
            self._sag = max(0.0, self._sag - 0.1 * dt)
            return

        fill_ratio = min(self.filled / self.volume, 1.0)
        fluid_density = self.mixture.density() if self.mixture.total() > 0 else 1.0

        target_sag = fill_ratio * fluid_density * 0.5 * (1.0 - self._elasticity * 0.3)
        target_sag = min(target_sag, self.MAX_SAG)

        inertia = 0.05 * dt
        if self._sag > 0.5:
            inertia *= 0.5

        self._sag += (target_sag - self._sag) * inertia
        self._sag = max(0.0, self._sag)

    def _update_elasticity(self, dt: float):
        loss_factor = self._sag * 0.4
        target = max(0.1, 1.0 * (1.0 - loss_factor))
        self._elasticity += (target - self._elasticity) * 0.2 * dt

    def _determine_state(self, pressure: float) -> BreastState:
        if self.filled <= 0:
            return BreastState.EMPTY

        if pressure < self.PRESSURE_NORMAL:
            return BreastState.NORMAL
        if pressure < self.PRESSURE_TENSE:
            return BreastState.TENSE

        # Новое состояние - переполнена но еще не течет
        if pressure < self.PRESSURE_LEAK_MIN:
            has_open = (
                any(n.is_open for n in self.areola.nipples)
                if self.areola.nipples
                else False
            )
            if not has_open:
                return BreastState.OVERPRESSURED
            return (
                BreastState.TENSE
            )  # Если соски открыты но давление ниже порога утечки
        # Протечка только при очень высоком давлении
        return BreastState.LEAKING

    def _auto_open_nipples(self, pressure: float):
        """Соски открываются только при давлении > 2.5 (близко к порогу утечки)."""
        if not self.areola.nipples:
            return

        # Открытие только при давлении > 2.5 (было 1.2)
        if pressure > 2.5:
            for nipple in self.areola.nipples:
                if not nipple.is_open:
                    target_gape = nipple.diameter * 0.1 * ((pressure - 2.5) / 1.0)
                    nipple.open(target_gape)
                    nipple.is_open = True

                # Расширение при критическом давлении > 3.5
                if pressure > 3.5 and nipple.is_open:
                    current = nipple.gape_diameter
                    max_target = nipple.diameter * 0.5
                    new_target = min(current + 0.01 * (pressure - 3.5), max_target)
                    nipple.gape_diameter = new_target
                    nipple.is_open = nipple.gape_diameter > 0.01

    def tick(self, dt: float = 1.0, event_bus: EventBus = None) -> Dict[str, Any]:
        if event_bus and not self._event_bus:
            self.set_event_bus(event_bus)

        # Обновление инфляции
        target_stretch = self.inflation.calculate_target_stretch(
            self.volume, self._base_volume
        )
        self.inflation.apply_stretch(target_stretch, dt)
        self._max_volume = min(
            self._base_volume * 1.5 * self.inflation.profile.stretch_ratio,
            self.GIGA_LIMIT,
        )
        self.areola._update_diameter(self.inflation.profile.stretch_ratio)

        # Физика
        self._update_sag(dt)
        self._update_elasticity(dt)

        # Давление
        calculated_pressure = PhysicsEngine.calculate_pressure(
            self.filled,
            self._base_volume,
            self.mixture.viscosity() if hasattr(self.mixture, "viscosity") else 1.0,
            self._elasticity,
            self._sag,
        )
        self.pressure_controller.update(calculated_pressure)

        # АВТООТКРЫВАНИЕ сосков при давлении (КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ)
        self._auto_open_nipples(calculated_pressure)

        # Дополнительная стимуляция сосков
        for nipple in self.areola.nipples:
            nipple.open_from_pressure(calculated_pressure, max_pressure=2.0)

        # Лактация
        try:
            lactation_result = self.lactation.tick(dt, self, event_bus)
            if lactation_result and lactation_result.get("milk_produced"):
                self.current_milk_volume += lactation_result["milk_produced"]
                num_ducts = max(1, len(self.duct_system.nipple_ducts))
                per_duct = lactation_result["milk_produced"] / num_ducts
                for duct in self.duct_system.nipple_ducts:
                    overflow = duct.receive_milk(per_duct)
                    if overflow > 0:
                        self.duct_system.lactiferous_sinuses += overflow
                self._emit(
                    "lactation",
                    EventType.LACTATION_ACTIVE,
                    amount=lactation_result["milk_produced"],
                )
        except Exception:
            pass

        # УТЕЧКА (исправленная логика)
        leaked = 0.0
        current_state = self._determine_state(calculated_pressure)
        old_state = self._state

        # Утечка происходит если есть давление и открытые соски
        if self.filled > 0 and calculated_pressure > 0.3:
            leak_rate = self._calc_leak_rate(calculated_pressure)
            if leak_rate > 0:
                desired_leak = self.filled * leak_rate * dt
                max_leak = self.filled * 0.5 * dt  # Не более 50% за тик

                leaked = min(desired_leak, max_leak)
                leaked = max(0.0, leaked)

                if leaked > 0.1:  # Минимальный порог для отображения
                    self.mixture.remove(leaked)
                    self._emit(
                        "leak",
                        EventType.LEAK,
                        amount=leaked,
                        pressure=calculated_pressure,
                        side=self.side,
                    )

                    # Если утечка значительная, сбрасываем давление визуально
                    if leaked > self.filled * 0.05:
                        calculated_pressure *= 0.95

        # Обновление состояния
        if current_state != old_state:
            self._state = current_state
            self._emit(
                "state_change",
                EventType.STATE_CHANGE,
                old_state=old_state.name,
                new_state=current_state.name,
            )
            if current_state == BreastState.LEAKING:
                self._emit("leak_start", EventType.LEAK)
            elif old_state == BreastState.LEAKING:
                self._emit("leak_end", EventType.ENGORGEMENT_RELIEF)

        # Проверка изменения размера
        current_cup = self.current_cup
        if current_cup != self._last_current_cup:
            self._emit(
                "cup_changed",
                EventType.CUP_CHANGE,
                old_cup=self._last_current_cup.name,
                new_cup=current_cup.name,
            )
            self._last_current_cup = current_cup

        # Защита от отрицательных значений
        if self.filled < 0:
            if hasattr(self.mixture, "_contents"):
                self.mixture._contents.clear()
            self._state = BreastState.EMPTY

        return {
            "state": (
                self._state.name if isinstance(self._state, Enum) else str(self._state)
            ),
            "filled": round(self.filled, 1),
            "pressure": round(calculated_pressure, 2),
            "leaked": round(leaked, 2),
            "cup": (
                self.current_cup.name
                if isinstance(self.current_cup, Enum)
                else str(self.current_cup)
            ),
            "sag": round(self._sag, 3),
            "arousal": round(self.arousal, 2),
            "pleasure": round(self.pleasure, 2),
        }

    def update(self, delta_time: float, event_bus: EventBus):
        return self.tick(delta_time, event_bus)

    def get_full_state(self) -> Dict[str, Any]:
        lactation_state = "unknown"
        try:
            if hasattr(self.lactation, "profile") and hasattr(
                self.lactation.profile, "state"
            ):
                state_val = self.lactation.profile.state
                if isinstance(state_val, Enum):
                    lactation_state = state_val.name
                else:
                    lactation_state = str(state_val)
        except:
            pass

        return {
            "cup": (
                self.current_cup.name
                if isinstance(self.current_cup, Enum)
                else str(self.current_cup)
            ),
            "base_cup": (
                self.cup_size.name
                if isinstance(self.cup_size, Enum)
                else str(self.cup_size)
            ),
            "filled": round(self.filled, 1),
            "max_volume": round(self._max_volume, 1),
            "pressure": round(self.pressure, 2),
            "stretch": round(self.inflation.profile.stretch_ratio, 2),
            "sag": round(self._sag, 3),
            "state": (
                self._state.name if isinstance(self._state, Enum) else str(self._state)
            ),
            "arousal": round(self.arousal, 2),
            "pleasure": round(self.pleasure, 2),
            "lactation": lactation_state,
            "areola": (
                self.areola.get_state() if hasattr(self.areola, "get_state") else {}
            ),
            "ducts": {
                "prolapse_total": round(self.duct_system.total_prolapse(), 2),
                "flow_capacity": round(self.duct_system.get_flow_capacity(), 2),
            },
        }

    def get_state(self) -> Dict[str, Any]:
        return {
            "cup": (
                self.current_cup.name
                if isinstance(self.current_cup, Enum)
                else str(self.current_cup)
            ),
            "filled": round(self.filled, 1),
            "pressure": round(self.pressure, 2),
            "state": (
                self._state.name if isinstance(self._state, Enum) else str(self._state)
            ),
            "arousal": round(self.arousal, 2),
            "pleasure": round(self.pleasure, 2),
        }

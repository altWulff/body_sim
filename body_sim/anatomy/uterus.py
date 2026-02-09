# body_sim/anatomy/uterus.py
"""
Матка (uterus/womb) с системой инфляции и распределением жидкости.

Особенности:
- Инфляция как у груди с растяжением стенок
- Распределение жидкости по фаллопиевым трубам к яичникам
- Статусы инфляции (NORMAL, STRETCHED, DISTENDED, HYPERDISTENDED, RUPTURE_RISK)
- Обратное течение жидкости из труб при переполнении
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Tuple
from enum import Enum, auto
import math

from body_sim.core.enums import (
        FluidType, 
        Sex, 
        UterusState, 
        CervixState, 
        OvaryState, 
        FallopianTubeState,
        UterusInflationStatus
    )

from body_sim.core.fluids import FluidMixture, BreastFluid, FLUID_DEFS
from body_sim.core.constants import UTERUS_MAX_STRETCH, PRESSURE_LEAK_MIN


@dataclass
class UterineWall:
    """Стенка матки с физическими свойствами."""
    thickness: float = 1.0           # см (толщина)
    elasticity: float = 1.0          # 0-1 (эластичность)
    integrity: float = 1.0           # 0-1 (целостность тканей)
    stretch_ratio: float = 1.0       # текущее растяжение
    fatigue: float = 0.0             # 0-1 (усталость)

    # Для инфляции
    plasticity: float = 0.3          # Пластичность (0-1)
    peak_stretch: float = 1.0        # Пиковое растяжение
    is_permanently_stretched: bool = False
    
    def can_stretch(self, target_ratio: float) -> bool:
        """Может ли растянуться до целевого соотношения (до 500x)."""
        # Максимальное растяжение зависит от эластичности и целостности
        # Базовый максимум 500x, модифицируется свойствами тканей
        max_stretch = UTERUS_MAX_STRETCH * self.elasticity * self.integrity
        return target_ratio <= max_stretch

    def stretch(self, ratio: float) -> bool:
        """Попытка растяжения."""
        if not self.can_stretch(ratio):
            self.integrity -= 0.1
            return False

        self.stretch_ratio = ratio
        self.peak_stretch = max(self.peak_stretch, ratio)
        self.fatigue += (ratio - 1.0) * 0.1
        self.fatigue = min(1.0, self.fatigue)

        if ratio >= 3.5:
            self.is_permanently_stretched = True

        return True

    def recover(self, dt: float):
        """Восстановление с учётом пластичности."""
        self.fatigue = max(0.0, self.fatigue - 0.01 * dt)

        if self.stretch_ratio > 1.0:
            # Эластичное восстановление
            elastic_part = (self.stretch_ratio - 1.0) * (1.0 - self.plasticity)
            plastic_part = (self.stretch_ratio - 1.0) * self.plasticity

            recovery = 0.001 * self.elasticity * dt
            new_elastic = max(0, elastic_part - recovery)

            self.stretch_ratio = 1.0 + plastic_part + new_elastic

    def get_skin_tension(self) -> float:
        """Натяжение кожи (0-1)."""
        if self.stretch_ratio <= 1.0:
            return 0.0
        return min(1.0, (self.stretch_ratio - 1.0) / 3.0)

    def get_stretch_marks_risk(self) -> float:
        """Риск растяжек."""
        tension = self.get_skin_tension()
        return tension * tension * (1.0 - self.elasticity)


@dataclass
class Cervix:
    """Шейка матки - "сосок" матки через который происходит утечка."""
    length: float = 3.0              # см (длина)
    diameter: float = 2.5            # см (диаметр отверстия)
    max_dilation: float = 10.0       # см (максимальное раскрытие)

    state: CervixState = field(default=CervixState.CLOSED)
    current_dilation: float = 0.0    # текущее раскрытие

    # Параметры как у соска - для механики утечки
    base_dilation: float = 0.1       # базовое раскрытие
    gape_diameter: float = 0.0       # текущее отверстие
    max_gape: float = field(init=False)

    # Инфляция шейки
    inflation_ratio: float = 1.0     # Коэффициент инфляции

    vaginal_connection: Optional[Any] = field(default=None, repr=False)

    def __post_init__(self):
        self.max_gape = self.max_dilation * 0.9
        self.gape_diameter = self.base_dilation

    def dilate(self, amount: float) -> bool:
        """Растворение шейки."""
        new_dilation = min(self.current_dilation + amount, self.max_dilation)

        if new_dilation > self.diameter * 0.5:
            self.state = CervixState.DILATED
        if new_dilation >= self.diameter * 2:
            self.state = CervixState.FULLY_OPEN

        self.current_dilation = new_dilation
        self.gape_diameter = max(self.base_dilation, new_dilation)
        return True

    def contract(self):
        """Сокращение."""
        self.current_dilation = max(0.0, self.current_dilation - 0.5)
        self.gape_diameter = max(self.base_dilation, self.current_dilation)
        if self.current_dilation < 0.5:
            self.state = CervixState.CLOSED

    def inflate(self, ratio: float):
        """Инфляция шейки (растяжение)."""
        self.inflation_ratio = max(1.0, min(ratio, 3.0))
        self.diameter *= self.inflation_ratio
        self.max_dilation *= self.inflation_ratio

    @property
    def is_open(self) -> bool:
        """Открыта ли шейка (для утечки)."""
        return self.gape_diameter > self.base_dilation * 1.5

    @property
    def effective_gape(self) -> float:
        """Эффективное отверстие для расчёта утечки."""
        if not self.is_open:
            return 0.0
        openness = self.gape_diameter / self.diameter
        return self.gape_diameter * openness

    @property
    def effective_diameter(self) -> float:
        """Эффективный диаметр прохода."""
        if self.state == CervixState.EVERTED:
            return self.max_dilation * 2
        return self.current_dilation


@dataclass
class Ovary:
    """
    Яичник с полной системой stretching, inflation и pressure.
    Аналогично матке, но с учётом анатомии яичника.
    """
    name: str = "ovary"
    side: str = "left"

    # Базовые размеры
    base_length: float = 3.0
    base_width: float = 2.0
    base_thickness: float = 1.5

    # Текущие размеры (с учётом stretching/inflation)
    current_length: float = field(init=False)
    current_width: float = field(init=False)
    current_thickness: float = field(init=False)

    # Объёмы
    base_volume: float = field(init=False)
    max_volume: float = field(init=False)
    current_volume: float = field(init=False)

    state: OvaryState = field(default=OvaryState.NORMAL)

    follicle_count: int = 5
    follicle_sizes: List[float] = field(default_factory=lambda: [0.5]*5)

    hormone_production: float = 1.0
    blood_supply: float = 1.0

    # ============ STRETCHING SYSTEM ============
    stretch_ratio: float = 1.0           # Коэффициент растяжения (1.0 = норма)
    max_stretch_ratio: float = 3.0       # Максимальное растяжение
    elasticity: float = 0.6              # Эластичность (0-1)
    plasticity: float = 0.4              # Пластичность (0-1)
    is_permanently_stretched: bool = False

    # ============ INFLATION SYSTEM ============
    inflation_ratio: float = 1.0         # Коэффициент инфляции
    max_inflation_ratio: float = 3.0     # Максимальная инфляция
    wall_integrity: float = 1.0          # Целостность стенок (0-1)
    wall_thickness: float = 0.5          # Толщина стенки (см)

    # Статус инфляции
    inflation_status: 'UterusInflationStatus' = field(default=None)

    # ============ PRESSURE SYSTEM ============
    # Жидкость в яичнике
    fluid_content: float = 0.0
    max_fluid_capacity: float = 20.0     # мл
    fluid_mixture: FluidMixture = field(default_factory=FluidMixture)

    # Давление
    internal_pressure: float = 0.0       # Внутреннее давление
    leak_rate: float = 0.0               # Скорость утечки

    # Соединения
    prolapse_degree: float = 0.0
    attached_tube: Optional['FallopianTube'] = field(default=None, repr=False)
    ruptured_follicles: int = 0

    def __post_init__(self):
        self.base_volume = self.calculate_volume()
        self.max_volume = self.base_volume * 2.0
        self.current_length = self.base_length
        self.current_width = self.base_width
        self.current_thickness = self.base_thickness
        self.current_volume = self.base_volume

        # Инициализируем статус инфляции
        try:
            from body_sim.anatomy.uterus import UterusInflationStatus
            self.inflation_status = UterusInflationStatus.NORMAL
        except ImportError:
            self.inflation_status = None

    # ============ VOLUME CALCULATIONS ============

    def calculate_volume(self) -> float:
        """Рассчитать базовый объём яичника."""
        return self.base_length * self.base_width * self.base_thickness * 0.8

    def calculate_current_volume(self) -> float:
        """Рассчитать текущий объём с учётом stretching и inflation."""
        stretch_factor = self.stretch_ratio ** 3
        inflation_factor = self.inflation_ratio ** 3
        return self.base_volume * stretch_factor * inflation_factor

    @property
    def available_volume(self) -> float:
        """Свободный объём для жидкости."""
        return self.current_volume - self.fluid_content

    @property
    def fill_ratio(self) -> float:
        """Коэффициент заполнения."""
        if self.current_volume <= 0:
            return 0.0
        return self.fluid_content / self.current_volume

    # ============ STRETCHING SYSTEM ============

    def stretch(self, ratio: float) -> bool:
        """
        Растянуть яичник.

        Args:
            ratio: Коэффициент растяжения (1.0 = норма)

        Returns:
            True если успешно
        """
        if ratio > self.max_stretch_ratio:
            return False

        old_ratio = self.stretch_ratio
        self.stretch_ratio = ratio

        # Обновляем размеры
        self.current_length = self.base_length * ratio
        self.current_width = self.base_width * (ratio ** 0.5)  # Меньше растяжение по ширине
        self.current_thickness = self.base_thickness * (ratio ** 0.3)

        # Проверяем на перманентное растяжение
        if ratio >= 2.5:
            self.is_permanently_stretched = True

        # Обновляем объём
        self.current_volume = self.calculate_current_volume()
        self._update_inflation_status()

        return True

    def recover_stretch(self, dt: float):
        """Восстановление от растяжения."""
        if self.stretch_ratio <= 1.0:
            return

        # Эластичное восстановление
        elastic_part = (self.stretch_ratio - 1.0) * (1.0 - self.plasticity)
        plastic_part = (self.stretch_ratio - 1.0) * self.plasticity

        recovery_rate = 0.001 * self.elasticity * dt
        new_elastic = max(0, elastic_part - recovery_rate)

        self.stretch_ratio = 1.0 + plastic_part + new_elastic

        # Обновляем размеры
        self.current_length = self.base_length * self.stretch_ratio
        self.current_width = self.base_width * (self.stretch_ratio ** 0.5)
        self.current_thickness = self.base_thickness * (self.stretch_ratio ** 0.3)
        self.current_volume = self.calculate_current_volume()

        self._update_inflation_status()

    # ============ INFLATION SYSTEM ============

    def inflate(self, ratio: float) -> bool:
        """
        Инфлировать (раздуть) яичник.

        Args:
            ratio: Коэффициент инфляции (1.0 = норма)

        Returns:
            True если успешно
        """
        if ratio > self.max_inflation_ratio:
            return False

        if ratio > 2.5 and self.wall_integrity < 0.5:
            return False  # Риск разрыва

        self.inflation_ratio = ratio

        # Обновляем размеры (инфляция более равномерная)
        self.current_length = self.base_length * self.stretch_ratio * (ratio ** 0.7)
        self.current_width = self.base_width * (self.stretch_ratio ** 0.5) * (ratio ** 0.7)
        self.current_thickness = self.base_thickness * (self.stretch_ratio ** 0.3) * (ratio ** 0.7)

        # Обновляем объём
        self.current_volume = self.calculate_current_volume()

        # Увеличиваем ёмкость
        self.max_fluid_capacity = 20.0 * (ratio ** 2)

        self._update_inflation_status()
        return True

    def _update_inflation_status(self):
        """Обновить статус инфляции."""
        try:
            from body_sim.anatomy.uterus import UterusInflationStatus

            total_ratio = self.stretch_ratio * self.inflation_ratio

            if total_ratio < 1.5:
                self.inflation_status = UterusInflationStatus.NORMAL
            elif total_ratio < 2.0:
                self.inflation_status = UterusInflationStatus.STRETCHED
            elif total_ratio < 2.5:
                self.inflation_status = UterusInflationStatus.DISTENDED
            elif total_ratio < 3.0:
                self.inflation_status = UterusInflationStatus.HYPERDISTENDED
            elif total_ratio < 3.5:
                self.inflation_status = UterusInflationStatus.RUPTURE_RISK
            else:
                self.inflation_status = UterusInflationStatus.RUPTURED
        except ImportError:
            pass

    def get_skin_tension(self) -> float:
        """Натяжение "кожи" яичника (0-1)."""
        total_ratio = self.stretch_ratio * self.inflation_ratio
        if total_ratio <= 1.0:
            return 0.0
        return min(1.0, (total_ratio - 1.0) / 2.5)

    def get_stretch_marks_risk(self) -> float:
        """Риск растяжек."""
        tension = self.get_skin_tension()
        return tension * tension * (1.0 - self.elasticity)

    # ============ PRESSURE SYSTEM ============

    def calculate_pressure(self, defs: Dict[FluidType, 'BreastFluid'] = None) -> float:
        """
        Рассчитать внутреннее давление.

        Args:
            defs: Определения жидкостей (для вязкости)

        Returns:
            Давление (0+)
        """
        if self.fluid_content <= 0:
            return 0.0

        # Базовое давление от заполнения
        fill_ratio = self.fill_ratio
        pressure = fill_ratio * 1.5

        # Модификатор вязкости
        if defs and self.fluid_mixture.components:
            viscosity = self.fluid_mixture.viscosity(defs)
            pressure *= (1.0 + viscosity * 0.3)

        # Модификатор эластичности
        elasticity_factor = 1.0 / max(0.1, self.elasticity)
        pressure *= elasticity_factor

        # Модификатор инфляции (большая инфляция = меньше давления)
        inflation_mod = 1.0 / (self.inflation_ratio ** 0.3)
        pressure *= inflation_mod

        # Модификатор растяжения
        stretch_penalty = (self.stretch_ratio - 1.0) * 0.2
        pressure += stretch_penalty

        self.internal_pressure = pressure
        return pressure

    def calculate_leak_rate(self, pressure: float, tube_pressure: float = 0.0) -> float:
        """
        Рассчитать скорость утечки через соединение с трубой.

        Args:
            pressure: Внутреннее давление яичника
            tube_pressure: Давление в трубе (для обратного потока)

        Returns:
            Скорость утечки (мл/тик)
        """
        pressure_diff = pressure - tube_pressure

        if pressure_diff < 0.5:
            return 0.0

        # Утечка через соединение с трубой
        base_leak = (pressure_diff - 0.5) * 0.1

        # Модификатор целостности
        integrity_mod = self.wall_integrity ** 2

        leak = base_leak * integrity_mod
        self.leak_rate = leak

        return leak

    # ============ FLUID MANAGEMENT ============

    def add_fluid(self, fluid: 'FluidType | BreastFluid', amount: float) -> float:
        """
        Добавить жидкость в яичник.

        Args:
            fluid: Тип жидкости или BreastFluid
            amount: Количество в мл

        Returns:
            Фактически добавленное количество
        """
        available = self.available_volume
        actual = min(amount, available)

        if actual > 0:
            self.fluid_content += actual
            self.fluid_mixture.add(fluid, actual)

            # При переполнении - увеличение размера фолликулов
            if self.fill_ratio > 0.8:
                self.enlarge_follicles(0.05)

            # Авто-растяжение при высоком давлении
            if self.fill_ratio > 0.9 and self.stretch_ratio < self.max_stretch_ratio:
                needed_stretch = 1.0 + (self.fill_ratio - 0.9) * 0.5
                self.stretch(min(self.stretch_ratio + needed_stretch, self.max_stretch_ratio))

        return actual

    def remove_fluid(self, amount: float) -> float:
        """Удалить жидкость из яичника."""
        actual = min(amount, self.fluid_content)
        if actual > 0:
            self.fluid_content -= actual
            self.fluid_mixture.remove(actual)
        return actual

    def drain_fluid(self) -> Dict[FluidType, float]:
        """Полностью опустошить яичник и вернуть состав."""
        removed = dict(self.fluid_mixture.components)
        self.fluid_content = 0.0
        self.fluid_mixture.components.clear()
        return removed

    def leak_to_tube(self, amount: float = None) -> float:
        """
        Утечка жидкости обратно в трубу.

        Args:
            amount: Количество (если None, используется leak_rate)

        Returns:
            Количество утечки
        """
        if not self.attached_tube:
            return 0.0

        if amount is None:
            amount = self.leak_rate

        actual = min(amount, self.fluid_content)
        if actual > 0:
            # Определяем преобладающий тип жидкости
            primary_fluid = self.get_primary_fluid()

            self.fluid_content -= actual
            self.fluid_mixture.remove(actual)

            # Возвращаем в трубу
            self.attached_tube.receive_backflow(actual)

        return actual

    def get_fluid_composition(self) -> Dict[FluidType, float]:
        """Получить состав жидкости в яичнике."""
        return dict(self.fluid_mixture.components)

    def get_primary_fluid(self) -> Optional[FluidType]:
        """Получить преобладающий тип жидкости."""
        if not self.fluid_mixture.components:
            return None
        return max(self.fluid_mixture.components.items(), key=lambda x: x[1])[0]

    # ============ FOLLICLE MANAGEMENT ============

    def enlarge_follicles(self, amount: float):
        """Увеличить фолликулы."""
        for i in range(len(self.follicle_sizes)):
            self.follicle_sizes[i] = min(2.5, self.follicle_sizes[i] + amount)
        if max(self.follicle_sizes) > 1.5:
            self.state = OvaryState.ENLARGED

    def rupture_follicle(self, index: int) -> bool:
        """Разорвать фолликул (овуляция)."""
        if 0 <= index < len(self.follicle_sizes):
            if self.follicle_sizes[index] > 1.0:
                self.follicle_sizes[index] = 0.3
                self.ruptured_follicles += 1
                return True
        return False

    # ============ PROLAPSE ============

    def evert(self, degree: float = 1.0):
        """Вывернуть яичник."""
        self.prolapse_degree = min(1.0, self.prolapse_degree + degree)
        if self.prolapse_degree > 0.7:
            self.state = OvaryState.EVERTED
        elif self.prolapse_degree > 0.3:
            self.state = OvaryState.PROLAPSED

    def reposition(self, amount: float = 0.5) -> bool:
        """Вправить яичник."""
        if self.state == OvaryState.EVERTED and amount < 0.7:
            return False
        self.prolapse_degree = max(0.0, self.prolapse_degree - amount)
        if self.prolapse_degree < 0.2:
            self.state = OvaryState.NORMAL
        elif self.prolapse_degree < 0.5:
            self.state = OvaryState.PROLAPSED
        return True

    @property
    def is_everted(self) -> bool:
        return self.state == OvaryState.EVERTED

    @property
    def visible_externally(self) -> bool:
        return self.prolapse_degree > 0.5

    @property
    def total_volume(self) -> float:
        """Общий объём с учётом жидкости."""
        return self.current_volume + self.fluid_content

    def get_status_dict(self) -> Dict[str, Any]:
        """Получить словарь со статусом яичника."""
        return {
            'side': self.side,
            'state': self.state.name if self.state else None,
            'inflation_status': self.inflation_status.value if self.inflation_status else None,
            'stretch_ratio': round(self.stretch_ratio, 2),
            'inflation_ratio': round(self.inflation_ratio, 2),
            'total_ratio': round(self.stretch_ratio * self.inflation_ratio, 2),
            'fluid_content': round(self.fluid_content, 1),
            'max_capacity': round(self.max_fluid_capacity, 1),
            'fill_ratio': round(self.fill_ratio, 2),
            'pressure': round(self.internal_pressure, 2),
            'skin_tension': round(self.get_skin_tension(), 2),
            'stretch_marks_risk': round(self.get_stretch_marks_risk(), 2),
            'follicles': len(self.follicle_sizes),
            'is_permanently_stretched': self.is_permanently_stretched,
        }

    @property
    def external_description(self) -> str:
        """Описание для внешнего отображения."""
        if not self.visible_externally:
            return ""

        desc = [f"{self.side.upper()} OVARY EXPOSED"]

        if self.inflation_status and self.inflation_status.value != 'normal':
            desc.append(f"[{self.inflation_status.value.upper()}]")

        visible_follicles = [f"{s:.1f}cm" for s in self.follicle_sizes if s > 0.8]
        if visible_follicles:
            desc.append(f"Follicles: {', '.join(visible_follicles)}")

        if self.ruptured_follicles > 0:
            desc.append(f"Ruptured: {self.ruptured_follicles}")

        if self.fluid_content > 0:
            primary = self.get_primary_fluid()
            primary_name = primary.name if primary else "MIX"
            desc.append(f"Fluid: {self.fluid_content:.1f}ml ({primary_name})")

        if self.is_permanently_stretched:
            desc.append("⚠️ PERMANENTLY STRETCHED")

        if self.blood_supply < 0.5:
            desc.append("⚠️ ISCHEMIC")

        return " | ".join(desc)

@dataclass
class FallopianTube:
    """Фаллопиева труба с системой инфляции и транспорта жидкости."""
    name: str = "fallopian_tube"
    side: str = "left"

    # Базовые размеры
    base_length: float = 10.0
    base_diameter: float = 0.3
    uterine_opening: float = 0.1
    ovarian_opening: float = 0.5

    # Текущие размеры (с учётом инфляции)
    current_length: float = field(init=False)
    current_diameter: float = field(init=False)

    state: FallopianTubeState = field(default=FallopianTubeState.NORMAL)
    elasticity: float = 1.0
    max_stretch_ratio: float = 4.0
    current_stretch: float = 1.0

    # Инфляция
    inflation_ratio: float = 1.0
    inflation_status: UterusInflationStatus = field(default=UterusInflationStatus.NORMAL)

    # Жидкость в трубе
    contained_fluid: float = 0.0
    max_fluid_capacity: float = 15.0  # мл
    fluid_mixture: FluidMixture = field(default_factory=FluidMixture)

    # Соединения
    uterus: Optional[Any] = field(default=None, repr=False)
    ovary: Optional[Ovary] = field(default=None, repr=False)

    # Транспорт жидкости
    fluid_flow_rate: float = 0.0  # скорость потока к яичнику
    backflow_resistance: float = 0.5  # сопротивление обратному току

    def __post_init__(self):
        self.current_length = self.base_length
        self.current_diameter = self.base_diameter
        if self.ovary:
            self.ovary.attached_tube = self

    @property
    def stretched_length(self) -> float:
        return self.base_length * self.current_stretch

    @property
    def is_stretched(self) -> bool:
        return self.current_stretch > 1.5

    @property
    def is_inflated(self) -> bool:
        return self.inflation_ratio > 1.5

    @property
    def can_prolapse_ovary(self) -> bool:
        if not self.ovary:
            return False
        return (self.current_stretch > 2.0 and 
                self.ovary.calculate_volume() < self.ovarian_opening * 10)

    @property
    def total_volume(self) -> float:
        """Общий объём трубы (структура + жидкость)."""
        structure_volume = math.pi * (self.current_diameter/2)**2 * self.current_length
        return structure_volume + self.contained_fluid

    def stretch(self, ratio: float) -> bool:
        """Растянуть трубу."""
        if ratio > self.max_stretch_ratio:
            self.state = FallopianTubeState.BLOCKED
            return False

        self.current_stretch = ratio
        self.current_length = self.base_length * ratio

        if ratio > 2.0:
            self.state = FallopianTubeState.DILATED
            self._update_inflation_status()

        return True

    def inflate(self, ratio: float) -> bool:
        """Инфлировать (раздуть) трубу."""
        if ratio > self.max_stretch_ratio:
            return False

        self.inflation_ratio = ratio
        self.current_diameter = self.base_diameter * ratio

        # Увеличиваем ёмкость
        self.max_fluid_capacity = 15.0 * (ratio ** 2)

        self._update_inflation_status()
        return True

    def _update_inflation_status(self):
        """Обновить статус инфляции."""
        total_stretch = self.current_stretch * self.inflation_ratio

        if total_stretch < 1.5:
            self.inflation_status = UterusInflationStatus.NORMAL
        elif total_stretch < 2.0:
            self.inflation_status = UterusInflationStatus.STRETCHED
        elif total_stretch < 2.5:
            self.inflation_status = UterusInflationStatus.DISTENDED
        elif total_stretch < 3.0:
            self.inflation_status = UterusInflationStatus.HYPERDISTENDED
        elif total_stretch < 3.5:
            self.inflation_status = UterusInflationStatus.RUPTURE_RISK
        else:
            self.inflation_status = UterusInflationStatus.RUPTURED

    def add_fluid(self, amount: float, fluid_type: FluidType = None) -> float:
        """Добавить жидкость в трубу."""
        available = self.max_fluid_capacity - self.contained_fluid
        actual = min(amount, available)

        self.contained_fluid += actual
        if fluid_type:
            self.fluid_mixture.add(fluid_type, actual)

        # Автоматическая передача в яичник
        if self.ovary and self.contained_fluid > self.max_fluid_capacity * 0.7:
            overflow = self.contained_fluid - self.max_fluid_capacity * 0.7
            # Определяем тип жидкости для передачи
            transfer_fluid_type = fluid_type
            if transfer_fluid_type is None and self.fluid_mixture.components:
                transfer_fluid_type = max(self.fluid_mixture.components.items(), key=lambda x: x[1])[0]
            transferred = self.ovary.add_fluid(transfer_fluid_type, overflow)
            self.contained_fluid -= transferred
            self.fluid_mixture.remove(transferred)

        return actual

    def transfer_to_ovary(self, amount: float, fluid_type: 'FluidType' = None) -> float:
        """
        Передать жидкость в яичник.

        Args:
            amount: Количество жидкости
            fluid_type: Тип жидкости (если None, берётся из смеси трубы)

        Returns:
            Количество переданной жидкости
        """
        if not self.ovary:
            return 0.0

        actual = min(amount, self.contained_fluid)
        if actual <= 0:
            return 0.0

        # Определяем тип жидкости
        if fluid_type is None:
            # Берём преобладающий тип из смеси трубы
            if self.fluid_mixture.components:
                fluid_type = max(self.fluid_mixture.components.items(), key=lambda x: x[1])[0]
            else:
                fluid_type = None  # Будет использован тип по умолчанию

        transferred = self.ovary.add_fluid(fluid_type, actual)
        self.contained_fluid -= transferred
        self.fluid_mixture.remove(transferred)

        return transferred

    def receive_backflow(self, amount: float) -> float:
        """Принять обратный поток от яичника."""
        # Сопротивление обратному току
        actual = amount * (1.0 - self.backflow_resistance)
        return self.add_fluid(actual)

    def evert_with_ovary(self):
        self.state = FallopianTubeState.EVERTED_WITH_OVARY
        if self.ovary:
            self.ovary.evert(1.0)

    def reposition(self):
        self.state = FallopianTubeState.NORMAL
        self.current_stretch = max(1.0, self.current_stretch - 0.5)
        self.inflation_ratio = max(1.0, self.inflation_ratio - 0.3)
        self.current_length = self.base_length * self.current_stretch
        self.current_diameter = self.base_diameter * self.inflation_ratio
        self._update_inflation_status()
        if self.ovary:
            self.ovary.reposition(0.5)

    @property
    def uterine_opening_visible(self) -> bool:
        if not self.uterus:
            return False
        return (hasattr(self.uterus, 'state') and 
                self.uterus.state in (UterusState.EVERTED, UterusState.INVERTED))

    @property
    def external_description(self) -> str:
        if not self.uterine_opening_visible:
            return ""

        desc = [f"{self.side.upper()} TUBE"]

        if self.inflation_status != UterusInflationStatus.NORMAL:
            desc.append(f"[{self.inflation_status.value.upper()}]")

        desc.append(f"L:{self.current_length:.1f}cm Ø{self.current_diameter:.1f}cm")

        if self.is_stretched:
            desc.append(f"stretch:{self.current_stretch:.1f}x")

        if self.is_inflated:
            desc.append(f"inflate:{self.inflation_ratio:.1f}x")

        if self.ovary and self.ovary.visible_externally:
            desc.append(f"→ OVARY")

        if self.contained_fluid > 0:
            desc.append(f"fluid:{self.contained_fluid:.1f}ml")

        return " | ".join(desc)


@dataclass 
class Uterus:
    """
    Матка с системой инфляции и распределением жидкости.

    Особенности:
    - Инфляция как у груди
    - Распределение жидкости по трубам к яичникам
    - Обратный поток при переполнении
    """

    name: str = "uterus"

    # Базовые размеры
    base_length: float = 7.0
    base_width: float = 5.0
    base_depth: float = 3.0
    cavity_volume: float = 50.0

    # Компоненты
    cervix: Cervix = field(default_factory=Cervix)
    walls: UterineWall = field(default_factory=UterineWall)

    # Трубы и яичники
    left_tube: Optional[FallopianTube] = field(default=None)
    right_tube: Optional[FallopianTube] = field(default=None)
    left_ovary: Optional[Ovary] = field(default=None)
    right_ovary: Optional[Ovary] = field(default=None)

    # Состояние
    state: UterusState = field(default=UterusState.NORMAL)
    inflation_status: UterusInflationStatus = field(default=UterusInflationStatus.NORMAL)

    prolapse_stage: float = 0.0
    descent_position: float = 0.0

    # СИСТЕМА ЖИДКОСТИ
    mixture: FluidMixture = field(default_factory=FluidMixture)
    leak_factor: float = 15.0

    # СИСТЕМА ИНФЛЯЦИИ
    inflation_ratio: float = 1.0           # Коэффициент инфляции матки
    tube_fill_ratio: float = 0.3           # Доля жидкости в трубы (0-1)
    ovary_fill_ratio: float = 0.2          # Доля от труб в яичники
    backflow_enabled: bool = True          # Разрешить обратный поток

    # Вставленные предметы
    inserted_objects: List[Any] = field(default_factory=list)

    # Физиология
    muscle_tone: float = 0.7
    ligament_integrity: float = 1.0
    pelvic_floor_strength: float = 0.7
    peristalsis_strength: float = 0.5      # Сила перистальтики

    # Дополнительный объём при выворачивании
    everted_volume: float = field(init=False)

    # События
    _listeners: Dict[str, List[Callable]] = field(default_factory=dict)

    def __post_init__(self):
        self.everted_volume = self.cavity_volume * 1.5

        if self.left_tube is None:
            self.left_tube = FallopianTube(side="left", uterus=self)
        if self.right_tube is None:
            self.right_tube = FallopianTube(side="right", uterus=self)
        if self.left_ovary is None:
            self.left_ovary = Ovary(side="left")
            self.left_tube.ovary = self.left_ovary
            self.left_ovary.attached_tube = self.left_tube
        if self.right_ovary is None:
            self.right_ovary = Ovary(side="right")
            self.right_tube.ovary = self.right_ovary
            self.right_ovary.attached_tube = self.right_tube

    # ============ EVENTS ============

    def on(self, event: str, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)

    def _emit(self, event: str, **data):
        for cb in self._listeners.get(event, []):
            cb(self, **data)

    # ============ PROPERTIES ============

    @property
    def filled(self) -> float:
        """Общий объём жидкости во всей системе."""
        total = self.mixture.total()
        for tube in self.tubes:
            if tube:
                total += tube.contained_fluid
        for ovary in self.ovaries:
            if ovary:
                total += ovary.fluid_content
        return total

    @property
    def uterus_filled(self) -> float:
        """Жидкость только в матке."""
        return self.mixture.total()

    @property
    def tubes_filled(self) -> float:
        """Жидкость в трубах."""
        return sum(t.contained_fluid for t in self.tubes if t)

    @property
    def ovaries_filled(self) -> float:
        """Жидкость в яичниках."""
        return sum(o.fluid_content for o in self.ovaries if o)

    @property
    def current_volume(self) -> float:
        """Текущий объём матки с учётом инфляции."""
        if self.state in (UterusState.EVERTED, UterusState.INVERTED):
            return self.cavity_volume * 0.1
        stretch_factor = self.inflation_ratio ** 3
        return self.cavity_volume * stretch_factor

    @property
    def available_volume(self) -> float:
        """Свободный объём в матке."""
        objects_volume = sum(
            getattr(obj, 'volume', 0) or getattr(obj, 'effective_volume', 0)
            for obj in self.inserted_objects
        )
        return max(0, self.current_volume - self.uterus_filled - objects_volume)

    @property
    def tubes(self) -> List[FallopianTube]:
        return [t for t in [self.left_tube, self.right_tube] if t]

    @property
    def ovaries(self) -> List[Ovary]:
        return [o for o in [self.left_ovary, self.right_ovary] if o]

    @property
    def is_everted(self) -> bool:
        return self.state == UterusState.EVERTED

    @property
    def is_prolapsed(self) -> bool:
        return self.state in (UterusState.DESCENDED, UterusState.PROLAPSED, UterusState.EVERTED)

    @property
    def total_system_volume(self) -> float:
        """Общий объём всей системы (матка + трубы + яичники)."""
        total = self.current_volume
        for tube in self.tubes:
            if tube:
                total += tube.max_fluid_capacity
        for ovary in self.ovaries:
            if ovary:
                total += ovary.max_fluid_capacity
        return total

    # ============ INFLATION SYSTEM ============

    def inflate(self, ratio: float) -> bool:
        """
        Инфлировать (раздуть) матку и трубы.

        Args:
            ratio: Коэффициент инфляции (1.0 = норма, 2.0 = в 2 раза больше)

        Returns:
            True если успешно
        """
        if ratio > 4.0:
            self._emit("inflation_limit_reached", ratio=ratio)
            return False

        old_ratio = self.inflation_ratio
        self.inflation_ratio = ratio

        # Обновляем размеры
        self.base_length *= ratio
        self.base_width *= ratio
        self.base_depth *= ratio

        # Инфлируем шейку
        self.cervix.inflate(ratio)

        # Инфлируем трубы
        for tube in self.tubes:
            if tube:
                tube.inflate(ratio)

        self._update_inflation_status()

        if ratio > old_ratio:
            self._emit("inflated", old_ratio=old_ratio, new_ratio=ratio)

        return True
        
    def _update_inflation_status(self):
        """Обновить статус инфляции с RUPTURED только на предельном растяжении 500x."""
        wall_stretch = self.walls.stretch_ratio
        total_stretch = self.inflation_ratio * wall_stretch
        
        # Плавные границы с зонами перехода
        if total_stretch < 1.3:
            self.inflation_status = UterusInflationStatus.NORMAL
        elif total_stretch < 1.7:
            # Переход NORMAL -> STRETCHED (1.3 - 1.7)
            self.inflation_status = UterusInflationStatus.STRETCHED if total_stretch >= 1.5 else UterusInflationStatus.NORMAL
        elif total_stretch < 2.3:
            # Переход STRETCHED -> DISTENDED (1.7 - 2.3)
            self.inflation_status = UterusInflationStatus.DISTENDED if total_stretch >= 2.0 else UterusInflationStatus.STRETCHED
        elif total_stretch < 2.8:
            # Переход DISTENDED -> HYPERDISTENDED (2.3 - 2.8)
            self.inflation_status = UterusInflationStatus.HYPERDISTENDED if total_stretch >= 2.5 else UterusInflationStatus.DISTENDED
        elif total_stretch < 3.5:
            # Переход HYPERDISTENDED -> RUPTURE_RISK (2.8 - 3.5)
            self.inflation_status = UterusInflationStatus.RUPTURE_RISK if total_stretch >= 3.0 else UterusInflationStatus.HYPERDISTENDED
            if total_stretch >= 3.0 and self.inflation_status != UterusInflationStatus.RUPTURE_RISK:
                self._emit("rupture_warning", stretch=total_stretch)
        elif total_stretch < 10.0:
            # Ультра-растяжение 3.5x - 10x
            self.inflation_status = UterusInflationStatus.RUPTURE_RISK
            self.walls.is_permanently_stretched = True
            self._emit("ultra_stretch", stretch=total_stretch)
        elif total_stretch < 50.0:
            # Мега-растяжение 10x - 50x
            self.inflation_status = UterusInflationStatus.RUPTURE_RISK
            self.walls.is_permanently_stretched = True
            integrity_loss = (total_stretch - 10.0) * 0.0001
            self.walls.integrity = max(0.5, self.walls.integrity - integrity_loss)
            self._emit("mega_stretch", stretch=total_stretch, integrity=self.walls.integrity)
        elif total_stretch < 100.0:
            # Гига-растяжение 50x - 100x
            self.inflation_status = UterusInflationStatus.RUPTURE_RISK
            self.walls.is_permanently_stretched = True
            integrity_loss = 0.004 + (total_stretch - 50.0) * 0.0001
            self.walls.integrity = max(0.3, self.walls.integrity - integrity_loss)
            self._emit("giga_stretch", stretch=total_stretch, integrity=self.walls.integrity)
        elif total_stretch < 250.0:
            # Тера-растяжение 100x - 250x
            self.inflation_status = UterusInflationStatus.RUPTURE_RISK
            self.walls.is_permanently_stretched = True
            integrity_loss = 0.002 + (total_stretch - 100.0) * 0.00005
            self.walls.integrity = max(0.15, self.walls.integrity - integrity_loss)
            self._emit("tera_stretch", stretch=total_stretch, integrity=self.walls.integrity)
        elif total_stretch < 400.0:
            # Петра-растяжение 250x - 400x
            self.inflation_status = UterusInflationStatus.RUPTURE_RISK
            self.walls.is_permanently_stretched = True
            integrity_loss = 0.001 + (total_stretch - 250.0) * 0.00002
            self.walls.integrity = max(0.08, self.walls.integrity - integrity_loss)
            self._emit("peta_stretch", stretch=total_stretch, integrity=self.walls.integrity)
        elif total_stretch < 500.0:
            # Экза-растяжение 400x - 500x (пред-разрыв)
            self.inflation_status = UterusInflationStatus.RUPTURE_RISK
            self.walls.is_permanently_stretched = True
            integrity_loss = 0.0005 + (total_stretch - 400.0) * 0.00005
            self.walls.integrity = max(0.03, self.walls.integrity - integrity_loss)
            self._emit("exa_stretch", stretch=total_stretch, integrity=self.walls.integrity)
        elif total_stretch >= 500.0:
            # ПРЕДЕЛЬНОЕ РАСТЯЖЕНИЕ 500x - РАЗРЫВ
            self.inflation_status = UterusInflationStatus.RUPTURED
            self.walls.is_permanently_stretched = True
            self.walls.integrity = max(0.0, self.walls.integrity - 0.01)
            self._emit("ruptured", stretch=total_stretch, integrity=self.walls.integrity)

    

    def get_inflation_details(self) -> Dict[str, Any]:
        """Получить детали инфляции."""
        return {
            "uterus_ratio": self.inflation_ratio,
            "wall_stretch": self.walls.stretch_ratio,
            "total_stretch": self.inflation_ratio * self.walls.stretch_ratio,
            "status": self.inflation_status.value,
            "skin_tension": self.walls.get_skin_tension(),
            "stretch_marks_risk": self.walls.get_stretch_marks_risk(),
            "is_permanent": self.walls.is_permanently_stretched,
        }

    # ============ FLUID DISTRIBUTION ============

    def _distribute_fluid_to_tubes(self, amount: float, fluid_type: FluidType) -> float:
        """
        Распределить жидкость по фаллопиевым трубам.

        Returns:
            Количество, которое не удалось распределить
        """
        if not self.tubes:
            return amount

        # Доля в трубы
        to_tubes = amount * self.tube_fill_ratio
        per_tube = to_tubes / len(self.tubes)

        distributed = 0.0
        for tube in self.tubes:
            if tube:
                added = tube.add_fluid(per_tube, fluid_type)
                distributed += added

                # Автоматическая передача в яичник с сохранением типа жидкости
                if tube.ovary:
                    overflow = tube.contained_fluid - tube.max_fluid_capacity * 0.8
                    if overflow > 0:
                        tube.transfer_to_ovary(overflow, fluid_type)

        return amount - distributed

    def _handle_backflow(self) -> float:
        """
        Обработать обратный поток от яичников при переполнении.

        Returns:
            Количество жидкости, вернувшееся в матку
        """
        if not self.backflow_enabled:
            return 0.0

        backflow_total = 0.0

        for ovary in self.ovaries:
            if ovary and ovary.fluid_content > ovary.max_fluid_capacity * 0.9:
                # Избыточная жидкость возвращается
                excess = ovary.fluid_content - ovary.max_fluid_capacity * 0.9
                returned = ovary.remove_fluid(excess * 0.5)

                # Через трубу обратно в матку
                if ovary.attached_tube:
                    ovary.attached_tube.receive_backflow(returned)
                    backflow_total += returned * ovary.attached_tube.backflow_resistance

        return backflow_total

    def _apply_peristalsis(self, dt: float):
        """Применить перистальтику для перемещения жидкости."""
        if self.peristalsis_strength <= 0:
            return

        # Перистальтика толкает жидкость к трубам
        for tube in self.tubes:
            if tube and self.uterus_filled > 0:
                push_amount = self.uterus_filled * self.peristalsis_strength * 0.1 * dt

                # Перемещаем в трубу
                if tube.contained_fluid < tube.max_fluid_capacity:
                    space = tube.max_fluid_capacity - tube.contained_fluid
                    actual = min(push_amount, space)

                    # Определяем преобладающий тип жидкости в матке
                    primary_fluid = None
                    if self.mixture.components:
                        primary_fluid = max(self.mixture.components.items(), key=lambda x: x[1])[0]

                    # Берём из смеси матки
                    self.mixture.remove(actual)
                    tube.add_fluid(actual, primary_fluid)

                    # Автопередача в яичник с сохранением типа
                    if tube.ovary:
                        tube.transfer_to_ovary(actual * 0.3, primary_fluid)

    # ============ PRESSURE SYSTEM ============

    def pressure(self, defs: Dict[FluidType, BreastFluid] = FLUID_DEFS) -> float:
        """Расчёт давления с учётом инфляции."""
        if self.uterus_filled <= 0:
            return 0.0

        viscosity = self.mixture.viscosity(defs)
        fill_ratio = self.uterus_filled / self.current_volume if self.current_volume > 0 else 0

        # Базовое давление
        pressure = fill_ratio * 2.0

        # Модификатор вязкости
        pressure *= (1.0 + viscosity * 0.5)

        # Модификатор эластичности
        elasticity_factor = 1.0 / max(0.1, self.walls.elasticity)
        pressure *= elasticity_factor

        # Модификатор инфляции (большая инфляция = меньше давления)
        inflation_mod = 1.0 / (self.inflation_ratio ** 0.5)
        pressure *= inflation_mod

        # Модификатор растяжения стенок
        stretch_penalty = (self.walls.stretch_ratio - 1.0) * 0.3
        pressure += stretch_penalty

        return pressure

    def _calc_leak_rate(self, pressure: float, viscosity: float) -> float:
        """Расчёт скорости утечки через шейку."""
        if not self.cervix.is_open:
            return 0.0

        effective_gape = self.cervix.effective_gape
        if effective_gape <= 0:
            return 0.0

        radius = effective_gape / 2
        area = math.pi * radius ** 2

        if pressure < PRESSURE_LEAK_MIN:
            return 0.0

        pressure_diff = pressure - PRESSURE_LEAK_MIN + 0.1
        flow_efficiency = (self.cervix.gape_diameter / self.cervix.diameter) ** 2

        flow_rate = 0.8 * area * pressure_diff * flow_efficiency / max(viscosity, 0.1)
        return max(0.0, flow_rate) * (self.leak_factor / 15.0)

    def _determine_state(self, pressure: float) -> UterusState:
        """Определение состояния."""
        if self.uterus_filled <= 0:
            return UterusState.EMPTY

        if self.is_everted:
            return UterusState.EVERTED

        if pressure < 0.5:
            return UterusState.NORMAL
        if pressure < 1.0:
            return UterusState.TENSE

        if self.cervix.is_open and pressure >= PRESSURE_LEAK_MIN:
            return UterusState.LEAKING

        return UterusState.OVERPRESSURED

    # ============ FLUID MANAGEMENT ============

    def add_fluid(self, fluid: 'FluidType | BreastFluid', amount: float) -> float:
        """Добавить жидкость с распределением по системе и автоматическим растяжением."""
        if amount <= 0:
            return 0.0

        fluid_type = fluid.fluid_type if isinstance(fluid, BreastFluid) else fluid
        total_added = 0.0
        remaining = amount

        # Максимальное растяжение 500x
        UTERUS_MAX_STRETCH = 500.0

        while remaining > 0:
            # Проверяем доступный объём с текущим растяжением
            available = self.available_volume

            if remaining <= available:
                # Всё помещается
                self.mixture.add(fluid_type, remaining)
                total_added += remaining
                
                # Распределяем часть в трубы
                self._distribute_fluid_to_tubes(remaining * self.tube_fill_ratio, fluid_type)
                
                self._emit("fluid_added", amount=total_added, fluid_type=fluid_type)
                return total_added

            # Не помещается - заполняем что можем
            if available > 0:
                self.mixture.add(fluid_type, available)
                total_added += available
                remaining -= available
                self._distribute_fluid_to_tubes(available * self.tube_fill_ratio, fluid_type)

            # Пытаемся растянуть стенки
            current_stretch = self.walls.stretch_ratio
            current_inflation = self.inflation_ratio
            current_total = current_stretch * current_inflation

            if current_total >= UTERUS_MAX_STRETCH:
                # Достигли предела
                self._emit("fluid_added", amount=total_added, fluid_type=fluid_type, 
                          overflow=remaining, max_reached=True)
                return total_added

            # Рассчитываем необходимое растяжение
            # Нужный объём = текущий + remaining
            needed_volume = self.uterus_filled + remaining
            # Добавляем запас 10%
            needed_volume *= 1.1
            
            # Целевое общее растяжение
            base_capacity = self.cavity_volume * (self.inflation_ratio ** 3)
            if base_capacity > 0:
                target_total_stretch = (needed_volume / base_capacity) ** (1/3)
            else:
                target_total_stretch = current_total + 1.0

            target_total_stretch = min(target_total_stretch, UTERUS_MAX_STRETCH)

            # Сначала пробуем инфляцию (меньше давления)
            if current_inflation < min(4.0, target_total_stretch):
                new_inflation = min(target_total_stretch / current_stretch, 4.0)
                if self.inflate(new_inflation):
                    continue

            # Затем растяжение стенок
            target_stretch = target_total_stretch / current_inflation
            target_stretch = min(target_stretch, self.walls.elasticity * 4.0)

            if target_stretch > current_stretch:
                if self.walls.stretch(target_stretch):
                    continue

            # Если не удалось растянуться - выходим
            self._emit("fluid_added", amount=total_added, fluid_type=fluid_type,
                      overflow=remaining, stretch_failed=True)
            return total_added

        return total_added
        

    def remove_fluid(self, amount: float) -> float:
        """Удалить жидкость (сначала из матки)."""
        if amount <= 0:
            return 0.0

        # Сначала из матки
        from_uterus = min(amount, self.uterus_filled)
        self.mixture.remove(from_uterus)
        remaining = amount - from_uterus

        # Потом из труб
        if remaining > 0:
            for tube in self.tubes:
                if tube and remaining > 0:
                    from_tube = min(remaining, tube.contained_fluid)
                    tube.contained_fluid -= from_tube
                    tube.fluid_mixture.remove(from_tube)
                    remaining -= from_tube

        # Потом из яичников
        if remaining > 0:
            for ovary in self.ovaries:
                if ovary and remaining > 0:
                    from_ovary = ovary.remove_fluid(remaining)
                    remaining -= from_ovary

        return amount - remaining

    def drain_all(self) -> Dict[FluidType, float]:
        """Полностью опустошить всю систему."""
        removed = {}

        # Из матки
        for fluid_type in list(self.mixture.components.keys()):
            amount = self.mixture.components[fluid_type]
            removed[fluid_type] = removed.get(fluid_type, 0) + amount
            del self.mixture.components[fluid_type]

        # Из труб
        for tube in self.tubes:
            if tube:
                for ft, amount in tube.fluid_mixture.components.items():
                    removed[ft] = removed.get(ft, 0) + amount
                tube.contained_fluid = 0.0
                tube.fluid_mixture.components.clear()

        # Из яичников
        for ovary in self.ovaries:
            if ovary:
                # Яичники содержат безтиповую жидкость
                if ovary.fluid_content > 0:
                    removed[FluidType.WATER] = removed.get(FluidType.WATER, 0) + ovary.fluid_content
                    ovary.fluid_content = 0.0

        self._emit("drained", amount=sum(removed.values()), fluids=removed)
        return removed

    # ============ TICK & UPDATE ============

    def tick(self, defs: Dict[FluidType, BreastFluid] = FLUID_DEFS, dt: float = 1.0) -> Dict[str, Any]:
        """Обновление состояния."""
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")

        # 1. Восстановление стенок
        self.walls.recover(dt)

        # 2. Обратный поток
        backflow = self._handle_backflow()
        if backflow > 0:
            self.mixture.add(FluidType.WATER, backflow)  # Упрощение

        # 3. Перистальтика
        self._apply_peristalsis(dt)

        # 4. Расчёт давления
        pressure = self.pressure(defs)

        # 5. Обновление шейки
        self._update_cervix(pressure, dt)

        # 6. Определение состояния
        old_state = self.state
        new_state = self._determine_state(pressure)

        if new_state != old_state:
            self.state = new_state
            self._emit("state_change", old=old_state, new=new_state)

            if new_state == UterusState.LEAKING:
                self._emit("leak_start")
            elif old_state == UterusState.LEAKING:
                self._emit("leak_end")

        # 7. Утечка
        leaked = 0.0
        if self.state == UterusState.LEAKING:
            viscosity = self.mixture.viscosity(defs)
            leak_rate = self._calc_leak_rate(pressure, viscosity)
            max_leak = self.uterus_filled * leak_rate * dt
            leaked = min(max_leak, self.uterus_filled)

            if leaked > 0:
                self.mixture.remove(leaked)
                self._emit("leak", amount=leaked)

        # 8. Обновление инфляции
        self._update_inflation_status()

        # 9. Обновление яичников
        for ovary in self.ovaries:
            if ovary:
                ovary.hormone_production = max(0.0, ovary.hormone_production - 0.001 * dt)
                if ovary.is_everted:
                    ovary.blood_supply = max(0.3, ovary.blood_supply - 0.01 * dt)
                    if ovary.blood_supply < 0.5:
                        ovary.state = OvaryState.TORSION

        # 10. Сокращение шейки
        if self.cervix.state not in (CervixState.EVERTED, CervixState.FULLY_OPEN):
            self.cervix.contract()

        # 11. Проверка пролапса
        if self.state == UterusState.NORMAL:
            risk = self.calculate_prolapse_risk()
            if risk > 0.8:
                self._progress_prolapse(0.1)

        return {
            "state": self.state.name,
            "inflation_status": self.inflation_status.value,
            "pressure": round(pressure, 2),
            "uterus_filled": round(self.uterus_filled, 1),
            "tubes_filled": round(self.tubes_filled, 1),
            "ovaries_filled": round(self.ovaries_filled, 1),
            "total_filled": round(self.filled, 1),
            "capacity": round(self.current_volume, 1),
            "leaked": round(leaked, 2),
            "cervix_dilation": round(self.cervix.current_dilation, 1),
            "inflation_ratio": round(self.inflation_ratio, 2),
        }


    def _update_cervix(self, pressure: float, dt: float):
        """Обновление шейки под давлением."""
        if pressure > 0.8:
            dilation_pressure = (pressure - 0.8) * 0.5 * dt
            self.cervix.dilate(dilation_pressure)

        if pressure > 1.5:
            force_dilation = (pressure - 1.5) * 0.3 * dt
            self.cervix.dilate(force_dilation)

    # ============ PROLAPSE MECHANICS ============

    def calculate_prolapse_risk(self) -> float:
        """Расчёт риска пролапса с учётом инфляции."""
        risk = 0.0
        risk += (1.0 - self.ligament_integrity) * 0.3
        risk += (1.0 - self.pelvic_floor_strength) * 0.3

        if self.walls.stretch_ratio > 2.0:
            risk += (self.walls.stretch_ratio - 2.0) * 0.2

        # Инфляция увеличивает риск
        if self.inflation_ratio > 2.0:
            risk += (self.inflation_ratio - 2.0) * 0.15

        fill_ratio = self.uterus_filled / max(self.current_volume, 1)
        risk += fill_ratio * 0.2

        risk += self.walls.fatigue * 0.1

        ovary_weight = sum(o.total_volume for o in self.ovaries if o)
        risk += ovary_weight * 0.001

        return min(1.0, risk)

    def apply_strain(self, force: float) -> bool:
        """Приложить силу."""
        risk = self.calculate_prolapse_risk()
        if force * risk > 0.5:
            return self._progress_prolapse(force * risk)
        return False

    def _progress_prolapse(self, amount: float) -> bool:
        """Прогрессирование пролапса."""
        old_state = self.state

        self.descent_position = min(1.0, self.descent_position + amount * 0.1)
        self.prolapse_stage = self.descent_position

        for tube in self.tubes:
            if tube:
                tube.stretch(1.0 + self.descent_position * 2)

        if self.descent_position < 0.3:
            self.state = UterusState.DESCENDED
        elif self.descent_position < 0.7:
            self.state = UterusState.PROLAPSED
        else:
            if self.state != UterusState.EVERTED:
                self._complete_eversion()

        if self.state != old_state:
            self._emit("state_change", old=old_state, new=self.state)
            return True
        return False

    def _complete_eversion(self):
        """Полное выворачивание."""
        self.state = UterusState.EVERTED
        self.cervix.state = CervixState.EVERTED

        self.drain_all()
        for obj in self.inserted_objects:
            if hasattr(obj, 'is_inserted'):
                obj.is_inserted = False
        self.inserted_objects.clear()

        self.walls.stretch_ratio = 2.5
        self.walls.fatigue = 1.0

        for tube in self.tubes:
            if tube:
                tube.state = FallopianTubeState.PROLAPSED

        self._emit("complete_eversion")

    def reduce_prolapse(self, amount: float = 0.5) -> bool:
        """Уменьшить пролапс."""
        if self.state == UterusState.EVERTED and amount < 0.5:
            return False

        self.descent_position = max(0.0, self.descent_position - amount)
        self.prolapse_stage = self.descent_position

        for ovary in self.ovaries:
            if ovary and ovary.state in (OvaryState.PROLAPSED, OvaryState.EVERTED):
                ovary.reposition(amount * 0.5)

        for tube in self.tubes:
            if tube:
                tube.current_stretch = max(1.0, tube.current_stretch - amount)

        if self.descent_position < 0.1:
            self.state = UterusState.NORMAL
            self.cervix.state = CervixState.CLOSED

        return True

    # ============ OBJECT INSERTION ============

    def insert_object(self, obj: Any) -> bool:
        """Вставить предмет."""
        if self.is_everted:
            return False

        obj_volume = getattr(obj, 'volume', 0) or getattr(obj, 'effective_volume', 0)
        if obj_volume > self.available_volume:
            return False

        obj_diameter = getattr(obj, 'diameter', 0) or getattr(obj, 'effective_diameter', 0)
        if obj_diameter > self.cervix.effective_diameter * 1.2:
            if not self.cervix.dilate(obj_diameter - self.cervix.effective_diameter):
                return False

        self.inserted_objects.append(obj)
        if hasattr(obj, 'is_inserted'):
            obj.is_inserted = True

        self._emit("object_inserted", object=obj)
        return True

    def remove_object(self, index: int) -> Optional[Any]:
        """Извлечь предмет."""
        if 0 <= index < len(self.inserted_objects):
            obj = self.inserted_objects.pop(index)
            if hasattr(obj, 'is_inserted'):
                obj.is_inserted = False
            self._emit("object_removed", object=obj)
            return obj
        return None

    # ============ TUBE & OVARY OPERATIONS ============

    def stretch_tube(self, side: str, ratio: float) -> bool:
        """Растянуть трубу."""
        tube = self.left_tube if side == "left" else self.right_tube
        if not tube:
            return False

        success = tube.stretch(ratio)
        if success and ratio > 2.5 and tube.ovary:
            if tube.can_prolapse_ovary:
                tube.ovary.evert(0.3)
        return success

    def inflate_tube(self, side: str, ratio: float) -> bool:
        """Инфлировать трубу."""
        tube = self.left_tube if side == "left" else self.right_tube
        if not tube:
            return False
        return tube.inflate(ratio)

    def evert_ovary(self, side: str, force: float = 1.0) -> bool:
        """Вывернуть яичник."""
        tube = self.left_tube if side == "left" else self.right_tube
        ovary = self.left_ovary if side == "left" else self.right_ovary

        if not tube or not ovary:
            return False

        if not self.cervix.is_open and not self.is_everted:
            return False

        if tube.current_stretch < 2.0:
            return False

        tube.evert_with_ovary()
        if force > 0.5:
            ovary.evert(force)

        return True

    def ovulate(self, side: str, follicle_idx: int = -1) -> bool:
        """Овуляция."""
        ovary = self.left_ovary if side == "left" else self.right_ovary
        tube = self.left_tube if side == "left" else self.right_tube

        if not ovary or not tube:
            return False

        if ovary.is_everted:
            if ovary.rupture_follicle(follicle_idx if follicle_idx >= 0 else 0):
                return True
            return False

        if ovary.rupture_follicle(follicle_idx if follicle_idx >= 0 else 0):
            tube.contained_ovum = {"stage": "fertilizable", "side": side}
            return True

        return False

    def __str__(self) -> str:
        return (
            f"Uterus({self.state.name}, "
            f"inflation={self.inflation_status.value}, "
            f"filled={self.uterus_filled:.1f}ml, "
            f"tubes={self.tubes_filled:.1f}ml, "
            f"ovaries={self.ovaries_filled:.1f}ml)"
        )


@dataclass
class UterusSystem:
    """Система маток для тела."""
    uteri: List[Uterus] = field(default_factory=list)

    def __post_init__(self):
        if not self.uteri:
            self.uteri.append(Uterus())

    @property
    def primary(self) -> Optional[Uterus]:
        return self.uteri[0] if self.uteri else None

    def add_uterus(self, uterus: Uterus) -> int:
        self.uteri.append(uterus)
        return len(self.uteri) - 1

    def tick(self, dt: float = 1.0):
        for uterus in self.uteri:
            uterus.tick(dt=dt)

    def __iter__(self):
        return iter(self.uteri)

    def __len__(self):
        return len(self.uteri)

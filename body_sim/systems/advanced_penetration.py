# body_sim/systems/advanced_penetration.py
"""
Расширенная система проникновений с анатомической глубиной.
Поддерживает: вагина→шейка→матка→трубы→яичники, уретра, соски.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Any, Union
from enum import Enum, auto
import random
import math
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from body_sim.systems.penetration import PenetrableOrgan, InsertableObject, PenetrationData


console = Console()


class PenetrationDepthZone(Enum):
    """Анатомические зоны для глубинного проникновения."""
    # Вагинальные
    VAGINA_INTROITUS = auto()      # Вход
    VAGINA_CANAL = auto()          # Канал
    VAGINA_FORNIX = auto()         # Свода (глубоко)
    CERVIX_EXTERNAL_OS = auto()    # Наружный зев шейки
    CERVIX_CANAL = auto()          # Канал шейки
    CERVIX_INTERNAL_OS = auto()    # Внутренний зев
    UTERUS_CAVITY = auto()         # Полость матки
    UTERUS_FUNDUS = auto()         # Дно матки
    TUBE_ISTHMUS = auto()          # Устье трубы
    TUBE_AMPULLA = auto()          # Ампулла трубы
    TUBE_INFUNDIBULUM = auto()     # Воронка трубы
    OVARY_SURFACE = auto()         # Поверхность яичника
    OVARY_PARENCHYMA = auto()      # Внутрь яичника

    # Уретральные
    URETHRA_MEATUS = auto()        # Наружное отверстие
    URETHRA_CANAL = auto()         # Канал
    URETHRA_TRIGONE = auto()       # Треугольник мочевого пузыря

    # Молочные
    NIPPLE_SURFACE = auto()        # Поверхность соска
    LACTIFEROUS_SINUS = auto()     # Молочный синус
    LACTIFEROUS_DUCT = auto()      # Молочный проток
    BREAST_ALVEOLI = auto()        # Дольки (глубоко)


@dataclass
class DepthLandmark:
    """Анатомическая отметка глубины."""
    zone: PenetrationDepthZone
    depth_cm: float
    min_diameter: float          # Минимальный диаметр для прохождения
    max_diameter: float          # Макс диаметр (растяжение)
    resistance_factor: float     # Сопротивление прохождению (0-1)
    description: str = ""

    # Особые эффекты при достижении
    stimulation_bonus: float = 0.0
    pain_risk: float = 0.0
    damage_risk: float = 0.0


@dataclass
class DeepPenetrationState:
    """Состояние глубокого проникновения."""
    current_depth: float = 0.0
    current_zone: PenetrationDepthZone = PenetrationDepthZone.VAGINA_INTROITUS
    max_achieved_depth: float = 0.0
    passed_landmarks: List[DepthLandmark] = field(default_factory=list)

    # Особые состояния
    is_through_cervix: bool = False
    is_in_uterus: bool = False
    is_in_tube: bool = False
    tube_side: Optional[str] = None  # "left" или "right"
    is_at_ovary: bool = False

    # Риски
    cervix_strain: float = 0.0       # Натяжение шейки
    ligament_strain: float = 0.0     # Натяжение связок
    tube_stretch: float = 0.0        # Растяжение трубы

    def __post_init__(self):
        if not self.passed_landmarks:
            self.passed_landmarks = []


@dataclass  
class ProlapseRiskCalculator:
    """Калькулятор риска пролапса/выворота при извлечении."""

    @staticmethod
    def calculate_uterine_prolapse_risk(
        penetration_state: DeepPenetrationState,
        uterus: Any,
        force_withdrawal: float = 0.5
    ) -> Tuple[float, str]:
        """Расчёт риска пролапса матки при выходе из неё."""
        risk = 0.0
        factors = []

        if penetration_state.is_in_uterus:
            depth_factor = min(1.0, penetration_state.current_depth / 15.0)
            risk += depth_factor * 0.2
            factors.append(f"depth:+{depth_factor:.1%}")

            if penetration_state.current_zone == PenetrationDepthZone.UTERUS_FUNDUS:
                risk += 0.3
                factors.append("fundus:+30%")

        if hasattr(uterus, 'cervix'):
            cervix = uterus.cervix
            if hasattr(cervix, 'state') and hasattr(cervix.state, 'name'):
                if cervix.state.name == "FULLY_OPEN":
                    risk += 0.2
                    factors.append("cervix_open:+20%")
                elif cervix.state.name == "DILATED":
                    risk += 0.1
                    factors.append("cervix_dilated:+10%")

            if hasattr(cervix, 'current_dilation'):
                dilation_risk = min(0.25, cervix.current_dilation / 20.0)
                risk += dilation_risk
                factors.append(f"dilation:+{dilation_risk:.0%}")

        if hasattr(uterus, 'inflation_ratio') and uterus.inflation_ratio > 2.0:
            inf_risk = (uterus.inflation_ratio - 2.0) * 0.15
            risk += inf_risk
            factors.append(f"inflation:+{inf_risk:.0%}")

        if hasattr(uterus, 'ligament_integrity'):
            ligament_risk = (1.0 - uterus.ligament_integrity) * 0.25
            risk += ligament_risk
            factors.append(f"ligaments:+{ligament_risk:.0%}")

        if force_withdrawal > 0.7:
            force_risk = (force_withdrawal - 0.7) * 0.5
            risk += force_risk
            factors.append(f"force:+{force_risk:.0%}")

        final_risk = min(1.0, risk)
        desc = " | ".join(factors) if factors else "low risk"
        return final_risk, desc

    @staticmethod
    def calculate_ovary_eversion_risk(
        penetration_state: DeepPenetrationState,
        tube: Any,
        ovary: Any,
        withdrawal_force: float = 0.5
    ) -> Tuple[float, str]:
        """Расчёт риска выворота яичника."""
        risk = 0.0
        factors = []

        if not penetration_state.is_at_ovary:
            return 0.0, "not at ovary"

        if hasattr(tube, 'current_stretch'):
            if tube.current_stretch < 2.0:
                return 0.0, "tube not stretched enough"

            stretch_risk = (tube.current_stretch - 2.0) * 0.3
            risk += stretch_risk
            factors.append(f"tube_stretch:{tube.current_stretch:.1f}x")

        if hasattr(ovary, 'calculate_volume'):
            volume = ovary.calculate_volume()
            if volume < 8.0:
                risk += 0.25
                factors.append("small_ovary:+25%")
            elif volume > 15.0:
                risk -= 0.2
                factors.append("large_ovary:-20%")

        if hasattr(ovary, 'state') and hasattr(ovary.state, 'name'):
            if ovary.state.name in ["PROLAPSED", "EVERTED"]:
                risk += 0.4
                factors.append("already_prolapsed:+40%")

        if withdrawal_force > 0.6:
            risk += (withdrawal_force - 0.6) * 0.6
            factors.append(f"force:{withdrawal_force:.0%}")

        if hasattr(ovary, 'inflation_ratio') and ovary.inflation_ratio > 1.5:
            inf_bonus = (ovary.inflation_ratio - 1.5) * 0.2
            risk += inf_bonus
            factors.append(f"ovary_inflation:+{inf_bonus:.0%}")

        final_risk = min(1.0, max(0.0, risk))
        return final_risk, " | ".join(factors)


@dataclass
class Urethra:
    """Уретра как проникаемый канал."""
    sex: str = "female"
    canal_length: float = 5.0
    rest_diameter: float = 0.6
    max_stretch_ratio: float = 2.0
    muscle_tone: float = 0.7

    inserted_objects: List[Any] = field(default_factory=list)
    total_inserted_volume: float = 0.0
    current_dilation: float = 0.0
    lubrication: float = 0.0
    sensitivity: float = 2.0
    pain_threshold: float = 0.3
    infection_risk: float = 0.0
    has_been_penetrated: bool = False
    micro_tears: float = 0.0

    def __post_init__(self):
        if self.sex == "male":
            self.canal_length = 20.0
            self.rest_diameter = 0.8
            self.has_prostate = True
        else:
            self.canal_length = 5.0
            self.rest_diameter = 0.6
            self.has_prostate = False
        self.current_dilation = self.rest_diameter

    @property
    def is_penetrated(self) -> bool:
        return len(self.inserted_objects) > 0

    def calculate_resistance(self, obj, depth: float) -> float:
        size_ratio = obj.diameter / self.rest_diameter
        if size_ratio > self.max_stretch_ratio:
            return 100.0
        resistance = (size_ratio ** 2) * 30 * self.muscle_tone
        if depth < 1.0:
            resistance += 40.0
        if size_ratio > 1.2:
            resistance += (size_ratio - 1.2) * 50
        return min(100, resistance)

    def check_insertion(self, obj, force: float) -> Tuple[bool, str]:
        initial_resistance = self.calculate_resistance(obj, 0)
        if force < initial_resistance:
            return False, f"Слишком большое сопротивление ({initial_resistance:.0f}%)"
        size_ratio = obj.diameter / self.rest_diameter
        if size_ratio > self.max_stretch_ratio:
            self.micro_tears += (size_ratio - self.max_stretch_ratio) * 0.1
            return False, f"Слишком большой диаметр! Риск разрыва ({self.micro_tears:.0%})"
        return True, "OK"

    def insert_object(self, obj, force: float) -> Tuple[bool, str]:
        can_insert, msg = self.check_insertion(obj, force)
        if not can_insert:
            return False, msg
        initial_depth = min(1.0, obj.length * 0.1)
        resistance = self.calculate_resistance(obj, initial_depth)
        if force > resistance:
            obj.inserted_depth = initial_depth
            self.current_dilation = max(self.current_dilation, obj.diameter)
            from body_sim.systems.penetration import PenetrationData
            data = PenetrationData(object=obj)
            self.inserted_objects.append(data)
            self._update_occupied_volume()
            self.has_been_penetrated = True
            return True, f"{obj.name} вставлен на {initial_depth:.1f} см"
        else:
            return False, "Не удалось преодолеть входное сопротивление"

    def _update_occupied_volume(self):
        total = 0.0
        for data in self.inserted_objects:
            obj = data.object
            volume = (math.pi * (obj.diameter/2) ** 2) * obj.inserted_depth
            total += volume
        self.total_inserted_volume = total

    def get_landmarks(self) -> List[DepthLandmark]:
        landmarks = [
            DepthLandmark(
                zone=PenetrationDepthZone.URETHRA_MEATUS,
                depth_cm=0.0, min_diameter=0.3, max_diameter=1.0,
                resistance_factor=0.8, description="Наружное отверстие уретры",
                stimulation_bonus=0.5
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.URETHRA_CANAL,
                depth_cm=self.canal_length * 0.5,
                min_diameter=0.5,
                max_diameter=1.2 if self.sex == "female" else 1.5,
                resistance_factor=0.4, description="Канал уретры",
                pain_risk=0.1
            )
        ]
        if self.sex == "male":
            landmarks.append(
                DepthLandmark(
                    zone=PenetrationDepthZone.URETHRA_TRIGONE,
                    depth_cm=18.0, min_diameter=1.0, max_diameter=2.0,
                    resistance_factor=0.3,
                    description="Предстательная железа/треугольник",
                    stimulation_bonus=1.0, pain_risk=0.2
                )
            )
        return landmarks


@dataclass
class NippleCanal:
    """Канал через сосок в грудь."""
    nipple: Any = None
    canal_length: float = 2.0
    duct_length: float = 5.0
    rest_diameter: float = 0.2
    max_stretch_ratio: float = 4.0
    is_dilated: bool = False
    current_dilation: float = 0.0
    lactation_active: bool = False
    inserted_objects: List[Any] = field(default_factory=list)

    def can_accommodate(self, obj_diameter: float) -> Tuple[bool, str]:
        if not self.nipple:
            return False, "No nipple attached"
        required_gape = obj_diameter * 1.1
        if self.nipple.gape_diameter < required_gape:
            return False, (
                f"Слишком широко! Требуется gape={required_gape:.2f}cm, "
                f"текущий={self.nipple.gape_diameter:.2f}cm"
            )
        return True, "OK"

    def calculate_resistance(self, obj, depth: float) -> float:
        size_ratio = obj.diameter / self.rest_diameter
        base = (size_ratio ** 2) * 20
        if self.nipple and self.nipple.is_open:
            base *= 0.5
        if depth > self.canal_length:
            base += (depth - self.canal_length) * 10
        return base

    def insert_object(self, obj, force: float) -> Tuple[bool, str]:
        can_fit, msg = self.can_accommodate(obj.diameter)
        if not can_fit:
            return False, msg
        resistance = self.calculate_resistance(obj, 0)
        if force < resistance:
            return False, f"Недостаточно силы для входа ({resistance:.0f}%)"
        obj.inserted_depth = min(1.0, obj.length * 0.1)
        from body_sim.systems.penetration import PenetrationData
        data = PenetrationData(object=obj)
        self.inserted_objects.append(data)
        return True, f"{obj.name} введён через сосок"

    def get_landmarks(self) -> List[DepthLandmark]:
        return [
            DepthLandmark(
                zone=PenetrationDepthZone.NIPPLE_SURFACE,
                depth_cm=0.0, min_diameter=0.1, max_diameter=0.5,
                resistance_factor=0.6, description="Поверхность соска",
                stimulation_bonus=0.8
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.LACTIFEROUS_SINUS,
                depth_cm=1.5, min_diameter=0.3, max_diameter=1.0,
                resistance_factor=0.3, description="Молочный синус",
                stimulation_bonus=0.5
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.LACTIFEROUS_DUCT,
                depth_cm=3.0, min_diameter=0.1, max_diameter=0.4,
                resistance_factor=0.4, description="Молочные протоки"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.BREAST_ALVEOLI,
                depth_cm=6.0, min_diameter=0.05, max_diameter=0.2,
                resistance_factor=0.7, description="Альвеолы",
                stimulation_bonus=0.3, pain_risk=0.2
            )
        ]


@dataclass
class AdvancedPenetrationEncounter:
    """Расширенная сессия проникновения с поддержкой глубины и переходов."""
    source_body: Any
    target_body: Any
    penetrating_object: Any
    entry_organ: str = "vagina"
    entry_organ_idx: int = 0
    state: DeepPenetrationState = field(default_factory=DeepPenetrationState)
    is_active: bool = False
    current_organ: Any = None
    uterus_ref: Any = None
    tube_ref: Any = None
    ovary_ref: Any = None
    ejaculation_by_zone: Dict[PenetrationDepthZone, float] = field(default_factory=dict)
    landmarks: List[DepthLandmark] = field(default_factory=list)
    debug_info: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.ejaculation_by_zone = {}
        self.landmarks = []
        self.debug_info = {}
        self._diagnostic_check()
        self._init_entry_organ()
        if not self.landmarks:
            console.print(f"[yellow]Warning: No landmarks for {self.entry_organ}[/yellow]")

    def _diagnostic_check(self):
        """Диагностика структуры target_body."""
        self.debug_info['target_body_type'] = type(self.target_body).__name__
        self.debug_info['has_uterus_system'] = hasattr(self.target_body, 'uterus_system')
        self.debug_info['has_uterus'] = hasattr(self.target_body, 'uterus')
        self.debug_info['has_womb'] = hasattr(self.target_body, 'womb')

    def _find_uterus(self) -> Any:
        """Поиск матки разными способами."""
        if hasattr(self.target_body, 'uterus_system'):
            us = self.target_body.uterus_system
            if hasattr(us, 'primary'):
                return us.primary
            if hasattr(us, 'uterus'):
                return us.uterus
            return us
        if hasattr(self.target_body, 'uterus'):
            return self.target_body.uterus
        if hasattr(self.target_body, 'womb'):
            return self.target_body.womb
        if hasattr(self.target_body, 'matka'):
            return self.target_body.matka
        if hasattr(self.target_body, 'reproductive_system'):
            rs = self.target_body.reproductive_system
            if hasattr(rs, 'uterus'):
                return rs.uterus
            if hasattr(rs, 'womb'):
                return rs.womb
        return None

    def _init_entry_organ(self):
        """Инициализация начального органа."""
        organ = self._get_organ(self.entry_organ, self.entry_organ_idx)
        if organ:
            self.current_organ = organ
            self._setup_landmarks_for_organ(organ)

    def _get_organ(self, organ_type: str, index: int):
        """Получить орган из целевого тела."""
        plural_map = {
            "vagina": "vaginas", "anus": "anuses", 
            "penis": "penises", "nipple": "nipples"
        }
        plural = plural_map.get(organ_type, organ_type + "s")
        if hasattr(self.target_body, plural):
            organs = getattr(self.target_body, plural)
            if isinstance(organs, list) and index < len(organs):
                return organs[index]
            elif not isinstance(organs, list) and index == 0:
                return organs
        if hasattr(self.target_body, organ_type) and index == 0:
            return getattr(self.target_body, organ_type)
        return None

    def _get_vaginal_landmarks(self, vagina) -> List[DepthLandmark]:
        """Создать отметки для вагинального пути."""
        landmarks = [
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_INTROITUS,
                depth_cm=0.0, min_diameter=1.0, max_diameter=6.0,
                resistance_factor=0.5, description="Вход во влагалище"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_CANAL,
                depth_cm=getattr(vagina, 'canal_length', 10.0) * 0.5,
                min_diameter=2.0,
                max_diameter=getattr(vagina, 'rest_diameter', 3.0) * getattr(vagina, 'max_stretch_ratio', 3.0),
                resistance_factor=0.3, description="Влагалищный канал"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_FORNIX,
                depth_cm=getattr(vagina, 'canal_length', 10.0) * 0.95,
                min_diameter=2.5, max_diameter=8.0,
                resistance_factor=0.4, description="Заднее/переднее своды",
                stimulation_bonus=0.8
            ),
        ]

        uterus = self._find_uterus()
        if uterus:
            cervix_pos = getattr(vagina, 'canal_length', 10.0)
            cervix_resistance = 0.9
            if hasattr(uterus, 'cervix'):
                cervix = uterus.cervix
                cervix_state = getattr(cervix, 'state', None)
                if cervix_state and hasattr(cervix_state, 'name'):
                    if cervix_state.name in ["DILATED", "FULLY_OPEN"]:
                        cervix_resistance = 0.4
                    elif cervix_state.name == "EVERTED":
                        cervix_resistance = 0.2

            landmarks.extend([
                DepthLandmark(
                    zone=PenetrationDepthZone.CERVIX_EXTERNAL_OS,
                    depth_cm=cervix_pos, min_diameter=0.1, max_diameter=12.0,
                    resistance_factor=cervix_resistance,
                    description="Наружный зев шейки матки", stimulation_bonus=0.5
                ),
                DepthLandmark(
                    zone=PenetrationDepthZone.CERVIX_CANAL,
                    depth_cm=cervix_pos + 2.0, min_diameter=0.2, max_diameter=8.0,
                    resistance_factor=0.7, description="Канал шейки матки", pain_risk=0.1
                ),
                DepthLandmark(
                    zone=PenetrationDepthZone.CERVIX_INTERNAL_OS,
                    depth_cm=cervix_pos + 3.5, min_diameter=0.3, max_diameter=6.0,
                    resistance_factor=0.6, description="Внутренний зев", stimulation_bonus=0.3
                ),
                DepthLandmark(
                    zone=PenetrationDepthZone.UTERUS_CAVITY,
                    depth_cm=cervix_pos + 5.0, min_diameter=2.0, max_diameter=25.0,
                    resistance_factor=0.2, description="Полость матки"
                ),
                DepthLandmark(
                    zone=PenetrationDepthZone.UTERUS_FUNDUS,
                    depth_cm=cervix_pos + 8.0, min_diameter=3.0, max_diameter=30.0,
                    resistance_factor=0.3, description="Дно матки"
                ),
            ])

            for side, offset in [("left", -1.5), ("right", 1.5)]:
                if hasattr(uterus, f'{side}_tube'):
                    tube_start = cervix_pos + 8.0 + offset
                    landmarks.extend([
                        DepthLandmark(
                            zone=PenetrationDepthZone.TUBE_ISTHMUS,
                            depth_cm=tube_start, min_diameter=0.1, max_diameter=4.0,
                            resistance_factor=0.8, description=f"Устье {side} трубы"
                        ),
                        DepthLandmark(
                            zone=PenetrationDepthZone.TUBE_AMPULLA,
                            depth_cm=tube_start + 5.0, min_diameter=0.3, max_diameter=5.0,
                            resistance_factor=0.5, description=f"Ампулла {side} трубы"
                        ),
                        DepthLandmark(
                            zone=PenetrationDepthZone.TUBE_INFUNDIBULUM,
                            depth_cm=tube_start + 10.0, min_diameter=1.0, max_diameter=8.0,
                            resistance_factor=0.4, description=f"Воронка {side} трубы"
                        ),
                        DepthLandmark(
                            zone=PenetrationDepthZone.OVARY_SURFACE,
                            depth_cm=tube_start + 12.0, min_diameter=2.0, max_diameter=6.0,
                            resistance_factor=0.6, description=f"Поверхность {side} яичника",
                            stimulation_bonus=0.2
                        ),
                    ])
        return landmarks

    def _setup_landmarks_for_organ(self, organ):
        """Настройка анатомических отметок."""
        try:
            if self.entry_organ == "vagina":
                self.landmarks = self._get_vaginal_landmarks(organ)
            elif self.entry_organ == "anus":
                self.landmarks = [
                    DepthLandmark(PenetrationDepthZone.VAGINA_INTROITUS, 0.0, 1.0, 8.0, 0.4, "Вход в анус"),
                    DepthLandmark(PenetrationDepthZone.VAGINA_CANAL, 10.0, 2.0, 10.0, 0.3, "Прямая кишка"),
                ]
            elif self.entry_organ == "urethra":
                if hasattr(organ, 'get_landmarks'):
                    self.landmarks = organ.get_landmarks()
                else:
                    sex = getattr(organ, 'sex', 'female')
                    self.landmarks = [
                        DepthLandmark(PenetrationDepthZone.URETHRA_MEATUS, 0.0, 0.3, 1.0, 0.8, "Наружное отверстие"),
                        DepthLandmark(PenetrationDepthZone.URETHRA_CANAL, 20.0 if sex == 'male' else 5.0, 0.5, 1.5, 0.4, "Канал"),
                    ]
            elif self.entry_organ == "nipple":
                self.landmarks = [
                    DepthLandmark(PenetrationDepthZone.NIPPLE_SURFACE, 0.0, 0.1, 0.5, 0.6, "Поверхность соска", stimulation_bonus=0.8),
                    DepthLandmark(PenetrationDepthZone.LACTIFEROUS_SINUS, 1.5, 0.3, 1.0, 0.3, "Молочный синус"),
                    DepthLandmark(PenetrationDepthZone.LACTIFEROUS_DUCT, 3.0, 0.1, 0.4, 0.4, "Молочные протоки"),
                    DepthLandmark(PenetrationDepthZone.BREAST_ALVEOLI, 6.0, 0.05, 0.2, 0.7, "Альвеолы", pain_risk=0.2),
                ]
            else:
                self.landmarks = []
            self.landmarks.sort(key=lambda x: x.depth_cm)
        except Exception as e:
            console.print(f"[red]Error setting up landmarks: {e}[/red]")
            self.landmarks = []

    def get_status_display(self) -> Panel:
        """Визуализация статуса."""
        depth = self.state.current_depth
        zone = self.state.current_zone.name
        bar_width = 40
        max_display_depth = 35.0
        pos = int((depth / max_display_depth) * bar_width)
        bar = "[" + "=" * pos + ">" + " " * (bar_width - pos - 1) + "]"
        source_name = getattr(self.source_body, 'name', 'Unknown')
        target_name = getattr(self.target_body, 'name', 'Unknown')

        uterus_warning = ""
        if not self._find_uterus():
            uterus_warning = "\n[yellow]⚠ Матка не найдена[/yellow]"

        content = f"""
[bold]{source_name}[/bold] → [bold]{target_name}[/bold]
Глубина: {depth:.1f} см | Зона: [cyan]{zone}[/cyan]
{bar} {depth:.1f}/~35см
Особые состояния:
• В матке: {'[red]ДА[/red]' if self.state.is_in_uterus else 'Нет'}
• В трубе: {f'[red]{self.state.tube_side}[/red]' if self.state.is_in_tube else 'Нет'}
• У яичника: {'[magenta]ДА[/magenta]' if self.state.is_at_ovary else 'Нет'}{uterus_warning}
Натяжение: Шейки {self.state.cervix_strain:.0%} | Связок {self.state.ligament_strain:.0%} | Трубы {self.state.tube_stretch:.0%}
        """
        return Panel(content, title="Deep Penetration Status", border_style="red")

    def advance(self, amount: float, force: float = 50.0) -> Tuple[bool, str]:
        """Продвинуться глубже."""
        if not self.is_active:
            return False, "Проникновение не активно"
        if not self.landmarks:
            return False, "Нет анатомических отметок"

        target_depth = self.state.current_depth + amount

        # Находим следующую отметку
        next_landmark = None
        for lm in self.landmarks:
            if lm.depth_cm > self.state.current_depth + 0.05:
                next_landmark = lm
                break

        if next_landmark and target_depth >= next_landmark.depth_cm:
            obj_diam = getattr(self.penetrating_object, 'diameter', 3.0)
            if obj_diam > next_landmark.max_diameter:
                return False, f"Слишком толсто! Макс: {next_landmark.max_diameter:.1f}см"

            required_force = next_landmark.resistance_factor * 100
            if force < required_force:
                return False, f"Недостаточно силы! Нужно {required_force:.0f}%, есть {force:.0f}%"

            # Проходим отметку
            self.state.current_depth = next_landmark.depth_cm
            self.state.current_zone = next_landmark.zone
            self.state.max_achieved_depth = max(self.state.max_achieved_depth, next_landmark.depth_cm)
            if next_landmark not in self.state.passed_landmarks:
                self.state.passed_landmarks.append(next_landmark)

            msg = f"Достигнуто: {next_landmark.description}"

            if next_landmark.zone == PenetrationDepthZone.CERVIX_EXTERNAL_OS:
                msg += "\n[yellow]⚠ Удар по шейке![/yellow]"
                self.state.cervix_strain += 0.2
            elif next_landmark.zone == PenetrationDepthZone.UTERUS_CAVITY:
                msg += "\n[red]⚠ Вход в матку![/red]"
                self.state.is_in_uterus = True
                self._enter_uterus()
            elif "TUBE" in next_landmark.zone.name:
                side = "left" if "left" in next_landmark.description else "right"
                msg += f"\n[red]⚠ Вход в {side} трубу![/red]"
                self.state.is_in_tube = True
                self.state.tube_side = side
                self._enter_tube(side)
            elif next_landmark.zone == PenetrationDepthZone.OVARY_SURFACE:
                msg += "\n[magenta]⚠ Контакт с яичником![/magenta]"
                self.state.is_at_ovary = True
                self._contact_ovary()

            return True, msg

        # Обычное продвижение
        self.state.current_depth = target_depth
        self.state.max_achieved_depth = max(self.state.max_achieved_depth, target_depth)
        return True, f"Продвинуто на {amount}см (всего {target_depth:.1f}см)"

    def _enter_uterus(self):
        """Вход в матку."""
        self.uterus_ref = self._find_uterus()
        if self.uterus_ref:
            self.current_organ = self.uterus_ref

    def _enter_tube(self, side: str):
        """Вход в трубу."""
        if self.uterus_ref:
            self.tube_ref = getattr(self.uterus_ref, f'{side}_tube', None)

    def _contact_ovary(self):
        """Контакт с яичником."""
        if self.tube_ref:
            self.ovary_ref = getattr(self.tube_ref, 'ovary', None)

    # ==================== МЕТОДЫ ИЗВЛЕЧЕНИЯ (WITHDRAW) ====================

    def withdraw(self, amount: float = None, force: float = 50.0) -> Tuple[bool, str]:
        """
        Извлечься на определенное расстояние или полностью.

        Args:
            amount: На сколько см извлечь (None = полностью)
            force: Сила извлечения (0-100)

        Returns:
            (success, message)
        """
        if not self.is_active:
            return False, "Проникновение не активно"

        if amount is None or amount >= self.state.current_depth:
            return self._full_withdrawal(force)

        # Частичное извлечение
        target_depth = self.state.current_depth - amount
        warnings = []

        # Проверяем риски при прохождении через опасные зоны
        if self.state.is_in_uterus and target_depth < self._get_zone_depth(PenetrationDepthZone.UTERUS_CAVITY):
            if self.uterus_ref:
                risk, desc = ProlapseRiskCalculator.calculate_uterine_prolapse_risk(
                    self.state, self.uterus_ref, force / 100.0
                )
                if risk > 0.3:
                    warnings.append(f"[red]Риск пролапса матки: {risk:.0%}[/red]")
                elif risk > 0.1:
                    warnings.append(f"[yellow]Натяжение связок: {risk:.0%}[/yellow]")

        if self.state.is_at_ovary and target_depth < self._get_zone_depth(PenetrationDepthZone.OVARY_SURFACE):
            if self.tube_ref and self.ovary_ref:
                risk, desc = ProlapseRiskCalculator.calculate_ovary_eversion_risk(
                    self.state, self.tube_ref, self.ovary_ref, force / 100.0
                )
                if risk > 0.3:
                    warnings.append(f"[red]РИСК ВЫВОРОТА ЯИЧНИКА: {risk:.0%}[/red]")
                    if random.random() < risk:
                        self._trigger_ovary_eversion()
                        warnings.append("[red]⚠ ЯИЧНИК ВЫВОРОТИЛСЯ![/red]")

        # Обновляем состояние
        old_zone = self.state.current_zone
        self.state.current_depth = max(0.0, target_depth)

        # Обновляем зону
        new_zone = self._get_zone_at_depth(self.state.current_depth)
        if new_zone != old_zone:
            self.state.current_zone = new_zone
            # Сбрасываем флаги если вышли из зоны
            if new_zone.value < PenetrationDepthZone.UTERUS_CAVITY.value:
                self.state.is_in_uterus = False
            if new_zone.value < PenetrationDepthZone.TUBE_ISTHMUS.value:
                self.state.is_in_tube = False
                self.state.tube_side = None
            if new_zone.value < PenetrationDepthZone.OVARY_SURFACE.value:
                self.state.is_at_ovary = False

        msg = f"Извлечение на {amount}см (глубина: {self.state.current_depth:.1f}см)"
        if warnings:
            msg += "\n" + "\n".join(warnings)

        return True, msg

    def _full_withdrawal(self, force: float) -> Tuple[bool, str]:
        """Полное извлечение с проверкой рисков."""
        warnings = []

        # Проверяем риски при полном выходе
        if self.state.is_in_uterus and self.uterus_ref:
            risk, desc = ProlapseRiskCalculator.calculate_uterine_prolapse_risk(
                self.state, self.uterus_ref, force / 100.0
            )
            if risk > 0.5:
                warnings.append(f"[red]ВЫСОКИЙ РИСК ПРОЛАПСА: {risk:.0%}![/red]")
                if random.random() < risk * 0.5:
                    self._trigger_uterine_prolapse()
                    warnings.append("[red]⚠ ПРОИЗОШЕЛ ПРОЛАПС МАТКИ![/red]")
            elif risk > 0.2:
                warnings.append(f"[yellow]Сильное натяжение связок ({risk:.0%})[/yellow]")

        if self.state.is_at_ovary and self.tube_ref and self.ovary_ref:
            risk, desc = ProlapseRiskCalculator.calculate_ovary_eversion_risk(
                self.state, self.tube_ref, self.ovary_ref, force / 100.0
            )
            if risk > 0.4:
                warnings.append(f"[red]КРИТИЧЕСКИЙ РИСК ВЫВОРОТА: {risk:.0%}![/red]")
                if random.random() < risk:
                    self._trigger_ovary_eversion()
                    warnings.append("[red]⚠ ЯИЧНИК ВЫВЕРНУЛСЯ![/red]")

        # Сбрасываем состояние
        depth_before = self.state.current_depth
        self.state.current_depth = 0.0
        self.state.current_zone = PenetrationDepthZone.VAGINA_INTROITUS
        self.state.is_in_uterus = False
        self.state.is_in_tube = False
        self.state.is_at_ovary = False
        self.state.tube_side = None
        self.is_active = False

        msg = f"[green]Полное извлечение ({depth_before:.1f}см)[/green]"
        if warnings:
            msg += "\n" + "\n".join(warnings)

        return True, msg

    def _get_zone_depth(self, zone: PenetrationDepthZone) -> float:
        """Получить глубину начала зоны."""
        for lm in self.landmarks:
            if lm.zone == zone:
                return lm.depth_cm
        return 0.0

    def _get_zone_at_depth(self, depth: float) -> PenetrationDepthZone:
        """Определить зону по глубине."""
        current_zone = PenetrationDepthZone.VAGINA_INTROITUS
        for lm in sorted(self.landmarks, key=lambda x: x.depth_cm):
            if depth >= lm.depth_cm:
                current_zone = lm.zone
            else:
                break
        return current_zone

    def _trigger_uterine_prolapse(self):
        """Вызвать пролапс матки."""
        if self.uterus_ref:
            if hasattr(self.uterus_ref, 'cervix') and hasattr(self.uterus_ref.cervix, 'state'):
                try:
                    from body_sim.systems.uterus import CervixState
                    self.uterus_ref.cervix.state = CervixState.EVERTED
                except:
                    pass
            if hasattr(self.uterus_ref, 'prolapse_degree'):
                self.uterus_ref.prolapse_degree = min(1.0, getattr(self.uterus_ref, 'prolapse_degree', 0) + 0.3)

    def _trigger_ovary_eversion(self):
        """Вызвать выворот яичника."""
        if self.ovary_ref and hasattr(self.ovary_ref, 'state'):
            try:
                from body_sim.systems.ovaries import OvaryState
                self.ovary_ref.state = OvaryState.EVERTED
            except:
                pass
        if self.tube_ref and hasattr(self.tube_ref, 'is_prolapsed'):
            self.tube_ref.is_prolapsed = True

    def ejaculate(self, volume: float = None) -> str:
        """Эякуляция в текущей зоне."""
        if not self.is_active:
            return "Проникновение не активно"

        if volume is None:
            volume = getattr(self.penetrating_object, 'ejaculate_volume', 5.0)

        zone = self.state.current_zone
        if zone not in self.ejaculation_by_zone:
            self.ejaculation_by_zone[zone] = 0.0
        self.ejaculation_by_zone[zone] += volume

        # Добавляем жидкость в матку если там
        if self.state.is_in_uterus and self.uterus_ref:
            if hasattr(self.uterus_ref, 'add_fluid'):
                try:
                    self.uterus_ref.add_fluid(volume, fluid_type="cum")
                except:
                    pass

        zone_names = {
            PenetrationDepthZone.VAGINA_INTROITUS: "во влагалище (вход)",
            PenetrationDepthZone.VAGINA_CANAL: "во влагалищном канале",
            PenetrationDepthZone.VAGINA_FORNIX: "во влагалищных сводах",
            PenetrationDepthZone.CERVIX_EXTERNAL_OS: "на наружном зеве шейки",
            PenetrationDepthZone.CERVIX_CANAL: "в канале шейки матки",
            PenetrationDepthZone.CERVIX_INTERNAL_OS: "на внутреннем зеве",
            PenetrationDepthZone.UTERUS_CAVITY: "В ПОЛОСТИ МАТКИ",
            PenetrationDepthZone.UTERUS_FUNDUS: "в дне матки",
            PenetrationDepthZone.TUBE_ISTHMUS: "в устье фаллопиевой трубы",
            PenetrationDepthZone.TUBE_AMPULLA: "в ампулле трубы",
            PenetrationDepthZone.TUBE_INFUNDIBULUM: "в воронке трубы",
            PenetrationDepthZone.OVARY_SURFACE: "НА ЯИЧНИКЕ",
        }

        location = zone_names.get(zone, f"в зоне {zone.name}")
        msg = f"[red]Эякуляция ({volume:.1f}мл) {location}![/red]"

        if self.state.is_in_uterus:
            msg += "\n[yellow]⚠ Высокий риск оплодотворения[/yellow]"
        elif self.state.is_in_tube:
            msg += "\n[yellow]⚠ Риск внематочной беременности[/yellow]"

        return msg

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
        """
        Расчёт риска пролапса матки при выходе из неё.

        Returns:
            (risk_0_to_1, description)
        """
        risk = 0.0
        factors = []

        # Базовый риск от глубины проникновения
        if penetration_state.is_in_uterus:
            depth_factor = min(1.0, penetration_state.current_depth / 15.0)
            risk += depth_factor * 0.2
            factors.append(f"depth:+{depth_factor:.1%}")

            # Если достигли дна матки - сильное натяжение связок
            if penetration_state.current_zone == PenetrationDepthZone.UTERUS_FUNDUS:
                risk += 0.3
                factors.append("fundus:+30%")

        # Состояние шейки
        if hasattr(uterus, 'cervix'):
            cervix = uterus.cervix
            if cervix.state.name == "FULLY_OPEN":
                risk += 0.2
                factors.append("cervix_open:+20%")
            elif cervix.state.name == "DILATED":
                risk += 0.1
                factors.append("cervix_dilated:+10%")

            # Растяжение шейки
            if hasattr(cervix, 'current_dilation'):
                dilation_risk = min(0.25, cervix.current_dilation / 20.0)
                risk += dilation_risk
                factors.append(f"dilation:+{dilation_risk:.0%}")

        # Инфляция матки (раздутие увеличивает риск)
        if hasattr(uterus, 'inflation_ratio'):
            if uterus.inflation_ratio > 2.0:
                inf_risk = (uterus.inflation_ratio - 2.0) * 0.15
                risk += inf_risk
                factors.append(f"inflation:+{inf_risk:.0%}")

        # Натяжение связок
        if hasattr(uterus, 'ligament_integrity'):
            ligament_risk = (1.0 - uterus.ligament_integrity) * 0.25
            risk += ligament_risk
            factors.append(f"ligaments:+{ligament_risk:.0%}")

        # Сила извлечения
        if force_withdrawal > 0.7:
            force_risk = (force_withdrawal - 0.7) * 0.5
            risk += force_risk
            factors.append(f"force:+{force_risk:.0%}")

        # Итоговый риск
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
        """
        Расчёт риска выворота яичника при выходе из фаллопиевой трубы.

        Requires:
            - Труба сильно растянута (>2.5x)
            - Проникновение достигло яичника
            - Яичник не слишком большой
        """
        risk = 0.0
        factors = []

        if not penetration_state.is_at_ovary:
            return 0.0, "not at ovary"

        # Растяжение трубы - ключевой фактор
        if hasattr(tube, 'current_stretch'):
            if tube.current_stretch < 2.0:
                return 0.0, "tube not stretched enough"

            stretch_risk = (tube.current_stretch - 2.0) * 0.3
            risk += stretch_risk
            factors.append(f"tube_stretch:{tube.current_stretch:.1f}x")

        # Размер яичника (чем меньше, тем легче вытянуть)
        if hasattr(ovary, 'calculate_volume'):
            volume = ovary.calculate_volume()
            if volume < 8.0:  # Маленький яичник
                risk += 0.25
                factors.append("small_ovary:+25%")
            elif volume > 15.0:  # Крупный
                risk -= 0.2
                factors.append("large_ovary:-20%")

        # Состояние яичника
        if hasattr(ovary, 'state'):
            if ovary.state.name in ["PROLAPSED", "EVERTED"]:
                risk += 0.4  # Уже частично вышел
                factors.append("already_prolapsed:+40%")

        # Сила извлечения
        if withdrawal_force > 0.6:
            risk += (withdrawal_force - 0.6) * 0.6
            factors.append(f"force:{withdrawal_force:.0%}")

        # Инфляция яичника (раздутый легче вытянуть)
        if hasattr(ovary, 'inflation_ratio'):
            if ovary.inflation_ratio > 1.5:
                inf_bonus = (ovary.inflation_ratio - 1.5) * 0.2
                risk += inf_bonus
                factors.append(f"ovary_inflation:+{inf_bonus:.0%}")

        final_risk = min(1.0, max(0.0, risk))
        return final_risk, " | ".join(factors)


@dataclass
class Urethra:
    """
    Уретра как проникаемый канал.
    У женщин: ~4-6см длина, 0.5-0.8см диаметр
    У мужчин: ~20см, извилистая
    """
    sex: str = "female"  # или "male"
    canal_length: float = 5.0
    rest_diameter: float = 0.6
    max_stretch_ratio: float = 2.0  # Ограниченное растяжение
    muscle_tone: float = 0.7

    inserted_objects: List[Any] = field(default_factory=list)
    total_inserted_volume: float = 0.0
    current_dilation: float = 0.0
    lubrication: float = 0.0

    # Чувствительность и риски
    sensitivity: float = 2.0        # Выше чем вагина
    pain_threshold: float = 0.3     # Низкий порог боли
    infection_risk: float = 0.0     # Риск инфекции от проникновения

    # Особенности
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
        """Уретра оказывает больше сопротивления и болезненнее."""
        size_ratio = obj.diameter / self.rest_diameter
        if size_ratio > self.max_stretch_ratio:
            return 100.0

        resistance = (size_ratio ** 2) * 30 * self.muscle_tone

        # Дополнительное сопротивление от сфинктера
        if depth < 1.0:
            resistance += 40.0  # Внешний сфинктер

        # Более болезненное при растяжении
        if size_ratio > 1.2:
            resistance += (size_ratio - 1.2) * 50

        return min(100, resistance)

    def check_insertion(self, obj, force: float) -> Tuple[bool, str]:
        """Проверка с риском травмы."""
        initial_resistance = self.calculate_resistance(obj, 0)

        if force < initial_resistance:
            return False, f"Слишком большое сопротивление ({initial_resistance:.0f}%)"

        # Проверка размера
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
        """Анатомические отметки уретры."""
        landmarks = [
            DepthLandmark(
                zone=PenetrationDepthZone.URETHRA_MEATUS,
                depth_cm=0.0,
                min_diameter=0.3,
                max_diameter=1.0,
                resistance_factor=0.8,
                description="Наружное отверстие уретры",
                stimulation_bonus=0.5
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.URETHRA_CANAL,
                depth_cm=self.canal_length * 0.5,
                min_diameter=0.5,
                max_diameter=1.2 if self.sex == "female" else 1.5,
                resistance_factor=0.4,
                description="Канал уретры",
                pain_risk=0.1
            )
        ]

        if self.sex == "male":
            landmarks.append(
                DepthLandmark(
                    zone=PenetrationDepthZone.URETHRA_TRIGONE,
                    depth_cm=18.0,
                    min_diameter=1.0,
                    max_diameter=2.0,
                    resistance_factor=0.3,
                    description="Предстательная железа/треугольник",
                    stimulation_bonus=1.0,
                    pain_risk=0.2
                )
            )

        return landmarks

    def advance_object(self, obj_name: str, amount: float, force: float) -> Tuple[bool, str]:
        """Продвинуть объект вглубь."""
        for data in self.inserted_objects:
            if data.object.name == obj_name:
                obj = data.object
                target = min(obj.inserted_depth + amount, self.canal_length)
                avg_resistance = (self.calculate_resistance(obj, obj.inserted_depth) + 
                                 self.calculate_resistance(obj, target)) / 2

                if force < avg_resistance:
                    actual_move = amount * (force / avg_resistance) * 0.5
                    obj.inserted_depth += actual_move
                    return False, f"Застопорено. Продвинуто на {actual_move:.1f} см"

                obj.inserted_depth = target
                if obj.inserted_depth >= self.canal_length:
                    return True, f"{obj.name} достиг конца уретры"
                return True, f"{obj.name} продвинут до {obj.inserted_depth:.1f} см"
        return False, "Объект не найден"


@dataclass
class NippleCanal:
    """
    Канал через сосок в грудь.
    Соединяется с системой молочных протоков.
    """
    nipple: Any = None  # Ссылка на Nipple объект

    # Параметры канала
    canal_length: float = 2.0        # До молочных синусов
    duct_length: float = 5.0         # Общая длина протоков
    rest_diameter: float = 0.2       # Закрыт по умолчанию
    max_stretch_ratio: float = 4.0   # Можно сильно растянуть

    # Состояние
    is_dilated: bool = False
    current_dilation: float = 0.0
    lactation_active: bool = False

    inserted_objects: List[Any] = field(default_factory=list)

    def __post_init__(self):
        pass

    def can_accommodate(self, obj_diameter: float) -> Tuple[bool, str]:
        """Проверка помещается ли объект через сосок."""
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
        """Сопротивление зависит от dilation соска."""
        size_ratio = obj.diameter / self.rest_diameter
        base = (size_ratio ** 2) * 20

        # Если сосок раскрыт - меньше сопротивления
        if self.nipple and self.nipple.is_open:
            base *= 0.5

        # Глубже - больше сопротивления (протоки сужаются)
        if depth > self.canal_length:
            base += (depth - self.canal_length) * 10

        return base

    def insert_object(self, obj, force: float) -> Tuple[bool, str]:
        """Вставка через сосок."""
        can_fit, msg = self.can_accommodate(obj.diameter)
        if not can_fit:
            return False, msg

        # Проверяем сопротивление
        resistance = self.calculate_resistance(obj, 0)
        if force < resistance:
            return False, f"Недостаточно силы для входа ({resistance:.0f}%)"

        obj.inserted_depth = min(1.0, obj.length * 0.1)
        from body_sim.systems.penetration import PenetrationData
        data = PenetrationData(object=obj)
        self.inserted_objects.append(data)

        return True, f"{obj.name} введён через сосок"

    def get_landmarks(self) -> List[DepthLandmark]:
        """Отметки в молочной системе."""
        return [
            DepthLandmark(
                zone=PenetrationDepthZone.NIPPLE_SURFACE,
                depth_cm=0.0,
                min_diameter=0.1,
                max_diameter=0.5,
                resistance_factor=0.6,
                description="Поверхность соска",
                stimulation_bonus=0.8
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.LACTIFEROUS_SINUS,
                depth_cm=1.5,
                min_diameter=0.3,
                max_diameter=1.0,
                resistance_factor=0.3,
                description="Молочный синус (накопитель)",
                stimulation_bonus=0.5
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.LACTIFEROUS_DUCT,
                depth_cm=3.0,
                min_diameter=0.1,
                max_diameter=0.4,
                resistance_factor=0.4,
                description="Молочные протоки"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.BREAST_ALVEOLI,
                depth_cm=6.0,
                min_diameter=0.05,
                max_diameter=0.2,
                resistance_factor=0.7,
                description="Альвеолы (дольки)",
                stimulation_bonus=0.3,
                pain_risk=0.2
            )
        ]


@dataclass
class AdvancedPenetrationEncounter:
    """
    Расширенная сессия проникновения с поддержкой глубины и переходов.
    """
    source_body: Any
    target_body: Any
    penetrating_object: Any  # Penis или InsertableObject

    # Начальный целевой орган (вход)
    entry_organ: str = "vagina"  # vagina, anus, urethra, nipple
    entry_organ_idx: int = 0

    # Состояние
    state: DeepPenetrationState = field(default_factory=DeepPenetrationState)
    is_active: bool = False

    # Отслеживание органов
    current_organ: Any = None      # Текущий орган (может меняться)
    uterus_ref: Any = None         # Ссылка на матку (если достигли)
    tube_ref: Any = None           # Ссылка на трубу
    ovary_ref: Any = None          # Ссылка на яичник

    # Накопленная сперма по зонам
    ejaculation_by_zone: Dict[PenetrationDepthZone, float] = field(default_factory=dict)
    landmarks: List[DepthLandmark] = field(default_factory=list)

    # Диагностика
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

        # Проверяем vaginas
        if hasattr(self.target_body, 'vaginas'):
            vaginas = self.target_body.vaginas
            self.debug_info['vaginas_count'] = len(vaginas) if isinstance(vaginas, list) else 1
            if isinstance(vaginas, list) and vaginas:
                self.debug_info['vagina0_type'] = type(vaginas[0]).__name__
                self.debug_info['vagina0_has_canal_length'] = hasattr(vaginas[0], 'canal_length')
        elif hasattr(self.target_body, 'vagina'):
            self.debug_info['vaginas_count'] = 1
            self.debug_info['vagina_type'] = type(self.target_body.vagina).__name__

        # Ищем матку всеми способами
        uterus = self._find_uterus()
        if uterus:
            self.debug_info['uterus_found'] = True
            self.debug_info['uterus_type'] = type(uterus).__name__
            self.debug_info['uterus_has_cervix'] = hasattr(uterus, 'cervix')
            self.debug_info['uterus_has_left_tube'] = hasattr(uterus, 'left_tube')
        else:
            self.debug_info['uterus_found'] = False

    def _find_uterus(self) -> Any:
        """Поиск матки разными способами."""
        # Вариант 1: uterus_system.primary
        if hasattr(self.target_body, 'uterus_system'):
            us = self.target_body.uterus_system
            if hasattr(us, 'primary'):
                return us.primary
            if hasattr(us, 'uterus'):
                return us.uterus
            return us  # Может само является маткой

        # Вариант 2: прямой доступ
        if hasattr(self.target_body, 'uterus'):
            return self.target_body.uterus
        if hasattr(self.target_body, 'womb'):
            return self.target_body.womb
        if hasattr(self.target_body, 'matka'):
            return self.target_body.matka

        # Вариант 3: через reproductive_system
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
        # Правильное множественное число
        plural_map = {
            "vagina": "vaginas",
            "anus": "anuses", 
            "penis": "penises",
            "nipple": "nipples"
        }

        plural = plural_map.get(organ_type, organ_type + "s")

        # Проверяем список
        if hasattr(self.target_body, plural):
            organs = getattr(self.target_body, plural)
            if isinstance(organs, list) and index < len(organs):
                return organs[index]
            elif not isinstance(organs, list) and index == 0:
                return organs

        # Одиночный орган
        if hasattr(self.target_body, organ_type) and index == 0:
            return getattr(self.target_body, organ_type)

        return None

    def _get_vaginal_landmarks(self, vagina) -> List[DepthLandmark]:
        """Создать отметки для вагинального пути до яичников."""
        landmarks = [
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_INTROITUS,
                depth_cm=0.0,
                min_diameter=1.0,
                max_diameter=6.0,
                resistance_factor=0.5,
                description="Вход во влагалище"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_CANAL,
                depth_cm=getattr(vagina, 'canal_length', 10.0) * 0.5,
                min_diameter=2.0,
                max_diameter=getattr(vagina, 'rest_diameter', 3.0) * getattr(vagina, 'max_stretch_ratio', 3.0),
                resistance_factor=0.3,
                description="Влагалищный канал"
            ),
            DepthLandmark(
                zone=PenetrationDepthZone.VAGINA_FORNIX,
                depth_cm=getattr(vagina, 'canal_length', 10.0) * 0.95,
                min_diameter=2.5,
                max_diameter=8.0,
                resistance_factor=0.4,
                description="Заднее/переднее своды (глубоко)",
                stimulation_bonus=0.8
            ),
        ]

        # Ищем матку
        uterus = self._find_uterus()

        if uterus:
            console.print(f"[green]Матка найдена: {type(uterus).__name__}[/green]")
            cervix_pos = getattr(vagina, 'canal_length', 10.0)

            # Определяем сопротивление шейки
            cervix_resistance = 0.9
            if hasattr(uterus, 'cervix'):
                cervix = uterus.cervix
                cervix_state = getattr(cervix, 'state', None)
                if cervix_state:
                    state_name = getattr(cervix_state, 'name', str(cervix_state))
                    console.print(f"[dim]Состояние шейки: {state_name}[/dim]")
                    if state_name in ["DILATED", "FULLY_OPEN"]:
                        cervix_resistance = 0.4
                    elif state_name == "EVERTED":
                        cervix_resistance = 0.2

            # Добавляем landmarks для матки
            landmarks.append(DepthLandmark(
                zone=PenetrationDepthZone.CERVIX_EXTERNAL_OS,
                depth_cm=cervix_pos,
                min_diameter=0.1,
                max_diameter=12.0,
                resistance_factor=cervix_resistance,
                description="Наружный зев шейки матки",
                stimulation_bonus=0.5
            ))

            landmarks.append(DepthLandmark(
                zone=PenetrationDepthZone.CERVIX_CANAL,
                depth_cm=cervix_pos + 2.0,
                min_diameter=0.2,
                max_diameter=8.0,
                resistance_factor=0.7,
                description="Канал шейки матки",
                pain_risk=0.1
            ))

            landmarks.append(DepthLandmark(
                zone=PenetrationDepthZone.CERVIX_INTERNAL_OS,
                depth_cm=cervix_pos + 3.5,
                min_diameter=0.3,
                max_diameter=6.0,
                resistance_factor=0.6,
                description="Внутренний зев (вход в матку)",
                stimulation_bonus=0.3
            ))

            landmarks.append(DepthLandmark(
                zone=PenetrationDepthZone.UTERUS_CAVITY,
                depth_cm=cervix_pos + 5.0,
                min_diameter=2.0,
                max_diameter=25.0,
                resistance_factor=0.2,
                description="Полость матки"
            ))

            landmarks.append(DepthLandmark(
                zone=PenetrationDepthZone.UTERUS_FUNDUS,
                depth_cm=cervix_pos + 8.0,
                min_diameter=3.0,
                max_diameter=30.0,
                resistance_factor=0.3,
                description="Дно матки (конец полости)"
            ))

            # Проверяем трубы
            has_left = hasattr(uterus, 'left_tube')
            has_right = hasattr(uterus, 'right_tube')
            console.print(f"[dim]Трубы: left={has_left}, right={has_right}[/dim]")

            if has_left or has_right:
                for side, offset in [("left", -1.5), ("right", 1.5)]:
                    tube = getattr(uterus, f'{side}_tube', None)
                    if tube:
                        tube_start = cervix_pos + 8.0 + offset

                        landmarks.append(DepthLandmark(
                            zone=PenetrationDepthZone.TUBE_ISTHMUS,
                            depth_cm=tube_start,
                            min_diameter=0.1,
                            max_diameter=4.0,
                            resistance_factor=0.8,
                            description=f"Устье {side} фаллопиевой трубы"
                        ))

                        landmarks.append(DepthLandmark(
                            zone=PenetrationDepthZone.TUBE_AMPULLA,
                            depth_cm=tube_start + 5.0,
                            min_diameter=0.3,
                            max_diameter=5.0,
                            resistance_factor=0.5,
                            description=f"Ампулла {side} трубы"
                        ))

                        landmarks.append(DepthLandmark(
                            zone=PenetrationDepthZone.TUBE_INFUNDIBULUM,
                            depth_cm=tube_start + 10.0,
                            min_diameter=1.0,
                            max_diameter=8.0,
                            resistance_factor=0.4,
                            description=f"Воронка {side} трубы (возле яичника)"
                        ))

                        landmarks.append(DepthLandmark(
                            zone=PenetrationDepthZone.OVARY_SURFACE,
                            depth_cm=tube_start + 12.0,
                            min_diameter=2.0,
                            max_diameter=6.0,
                            resistance_factor=0.6,
                            description=f"Поверхность {side} яичника",
                            stimulation_bonus=0.2
                        ))
        else:
            console.print("[yellow]Матка не найдена! Глубокое проникновение ограничено влагалищем.[/yellow]")
            console.print(f"[dim]Debug info: {self.debug_info}[/dim]")

        return landmarks


    def _setup_landmarks_for_organ(self, organ):
        """Настройка анатомических отметок для органа."""
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
                    self.landmarks = [
                        DepthLandmark(PenetrationDepthZone.URETHRA_MEATUS, 0.0, 0.3, 1.0, 0.8, "Наружное отверстие"),
                        DepthLandmark(PenetrationDepthZone.URETHRA_CANAL, 5.0 if getattr(organ, 'sex', 'female') == 'female' else 20.0, 0.5, 1.5, 0.4, "Канал уретры"),
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

            # Сортируем landmarks по глубине
            self.landmarks.sort(key=lambda x: x.depth_cm)

            console.print(f"[dim]Создано {len(self.landmarks)} landmarks для {self.entry_organ}[/dim]")

        except Exception as e:
            console.print(f"[red]Error setting up landmarks: {e}[/red]")
            import traceback
            console.print(f"[red]{traceback.format_exc()}[/red]")
            self.landmarks = []

    def get_status_display(self) -> Panel:
        """Визуализация статуса проникновения."""
        from rich.panel import Panel
        from rich.text import Text

        depth = self.state.current_depth
        zone = self.state.current_zone.name

        # Создаём визуальную шкалу
        bar_width = 40
        max_display_depth = 35.0
        pos = int((depth / max_display_depth) * bar_width)
        bar = "[" + "=" * pos + ">" + " " * (bar_width - pos - 1) + "]"

        source_name = getattr(self.source_body, 'name', 'Unknown')
        target_name = getattr(self.target_body, 'name', 'Unknown')

        # Показываем debug_info если матка не найдена
        uterus_warning = ""
        if not self.debug_info.get('uterus_found', False):
            uterus_warning = "\n[yellow]⚠ Матка не найдена в target_body[/yellow]"

        content = f"""
[bold]{source_name}[/bold] → [bold]{target_name}[/bold]

Глубина: {depth:.1f} см
Зона: [cyan]{zone}[/cyan]

{bar} {depth:.1f}/~35см

Особые состояния:
• В матке: {'[red]ДА[/red]' if self.state.is_in_uterus else 'Нет'}
• В трубе: {f'[red]{self.state.tube_side}[/red]' if self.state.is_in_tube else 'Нет'}
• У яичника: {'[magenta]ДА[/magenta]' if self.state.is_at_ovary else 'Нет'}{uterus_warning}

Натяжение:
• Шейки: {self.state.cervix_strain:.0%}
• Связок: {self.state.ligament_strain:.0%}
• Трубы: {self.state.tube_stretch:.0%}
        """

        return Panel(content, title="Deep Penetration Status", border_style="red")

    def advance(self, amount: float, force: float = 50.0) -> Tuple[bool, str]:
        """
        Продвинуться глубже.

        Returns:
            (success, message)
        """
        if not self.is_active:
            return False, "Проникновение не активно"

        if not self.landmarks:
            return False, "Нет анатомических отметок для продвижения"

        target_depth = self.state.current_depth + amount

        # Находим следующую отметку
        next_landmark = None
        for lm in self.landmarks:
            if lm.depth_cm > self.state.current_depth + 0.05:
                next_landmark = lm
                break

        if next_landmark:
            # Проверяем достижение отметки
            if target_depth >= next_landmark.depth_cm:
                # Проверяем можем ли пройти
                obj_diam = getattr(self.penetrating_object, 'diameter', 3.0)

                if obj_diam > next_landmark.max_diameter:
                    return False, f"Слишком толсто для {next_landmark.description}! Макс: {next_landmark.max_diameter:.1f}см"

                required_force = next_landmark.resistance_factor * 100
                if force < required_force:
                    return False, (
                        f"Не хватает силы для {next_landmark.description}! "
                        f"Нужно {required_force:.0f}%, есть {force:.0f}%"
                    )

                # Проходим отметку
                self.state.current_depth = next_landmark.depth_cm
                self.state.current_zone = next_landmark.zone
                self.state.max_achieved_depth = max(self.state.max_achieved_depth, next_landmark.depth_cm)

                if next_landmark not in self.state.passed_landmarks:
                    self.state.passed_landmarks.append(next_landmark)

                # Особые эффекты
                msg = f"Достигнуто: {next_landmark.description}"

                if next_landmark.zone == PenetrationDepthZone.CERVIX_EXTERNAL_OS:
                    msg += "\n[yellow]⚠ Удар по шейке матки![/yellow]"
                    self.state.cervix_strain += 0.2

                elif next_landmark.zone == PenetrationDepthZone.UTERUS_CAVITY:
                    msg += "\n[red]⚠ Вход в матку![/red]"
                    self.state.is_in_uterus = True
                    self.state.is_through_cervix = True
                    self._enter_uterus()

                elif "TUBE" in next_landmark.zone.name:
                    side = "left" if "left" in next_landmark.description else "right"
                    msg += f"\n[red]⚠ Вход в {side} фаллопиеву трубу![/red]"
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
        """Вход в матку - сохраняем ссылку."""
        self.uterus_ref = self._find_uterus()
        if self.uterus_ref:
            self.current_organ = self.uterus_ref
            console.print("[green]Вошли в матку[/green]")

    def _enter_tube(self, side: str):
        """Вход в фаллопиеву трубу."""
        if self.uterus_ref:
            self.tube_ref = (
                getattr(self.uterus_ref, 'left_tube', None) if side == "left" 
                else getattr(self.uterus_ref, 'right_tube', None)
            )
            if self.tube_ref:
                console.print(f"[green]Вошли в {side} трубу[/green]")

    def _contact_ovary(self):
        """Контакт с яичником."""
        if self.tube_ref:
            self.ovary_ref = getattr(self.tube_ref, 'ovary', None)
            if self.ovary_ref:
                console.print("[magenta]Контакт с яичником[/magenta]")

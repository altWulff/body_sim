# body_sim/core/enums.py
"""
Все перечисления системы в одном месте.
"""

from enum import Enum, auto


# ========== Размеры груди ==========
class CupSize(Enum):
    FLAT = 50
    MICRO = 100
    AAA = 150
    AA = 200
    A = 250
    B = 350
    C = 450
    D = 550
    E = 650
    F = 800
    G = 1000
    H = 1250
    I = 1550
    J = 1950
    K = 2450
    L = 3100
    M = 3900
    N = 4900
    O = 6200
    P = 7800
    Q = 9800
    R = 12300
    S = 15500
    T = 19500
    U = 24500
    V = 31000
    W = 39000
    X = 49000
    Y = 62000
    Z = 78000
    ULTRA = 100000
    MEGA = 250000
    GIGA = 500000

    @property
    def base_volume(self) -> float:
        return float(self.value)

    @property
    def display_name(self) -> str:
        if self in (CupSize.FLAT, CupSize.MICRO):
            return f"{self.name} (Flat)"
        elif self.value >= 10000:
            return f"{self.name}-CUP ({self.value/1000:.0f}L)"
        return f"{self.name}-CUP"


# ========== Жидкости ==========
class FluidType(Enum):
    MILK = auto()
    CUM = auto()
    WATER = auto()
    HONEY = auto()
    OIL = auto()
    CUSTOM = auto()


# ========== Состояния груди ==========
class BreastState(Enum):
    EMPTY = auto()
    NORMAL = auto()
    TENSE = auto()
    OVERPRESSURED = auto()
    LEAKING = auto()


# ========== Соски ==========
class NippleType(Enum):
    TINY_FLAT = "tiny flat"
    CUTE_SMALL = "cute small"
    PERKY_MEDIUM = "perky medium"
    PUFFY = "puffy"
    LARGE_THICK = "large thick"
    HYPER_LONG = "hyper long"
    GAPING_STRETCHED = "gaping stretched"
    INVERTED = "inverted"


class NippleShape(Enum):
    FLAT = "flat"
    CONICAL = "conical"
    CYLINDRICAL = "cylindrical"
    PUFFY = "puffy"
    INVERTED = "inverted"


# ========== Цвета и текстуры ==========
class Color(Enum):
    PALE_PINK = "pale_pink"
    LIGHT_PINK = "light_pink"
    PINK = "pink"
    DARK_PINK = "dark_pink"
    PEACH = "peach"
    TAN = "tan"
    BROWN = "brown"
    DARK_BROWN = "dark_brown"
    BLACKISH = "blackish"
    LIGHT_BEIGE = "light_beige"
    PALE_IVORY = "pale_ivory"
    GREEN = "green"
    DARK_RED = "dark_red"
    RED = "red"
    BEIGE = "beige"
    BLUE = "blue"
    GRAY = "gray"
    GOLD = "gold"
    SILVER = "silver"
    YELLOW = "yellow"
    BLACK = "black"
    PURPLE = "purple"
    WHITE = "white"
    TRANSLUCENT = "translucent"
    CRIMSON = "crimson"


class AreolaTexture(Enum):
    SMOOTH = "smooth"
    SLIGHTLY_BUMPY = "slightly_bumpy"
    BUMPY = "bumpy"
    WRINKLED = "wrinkled"
    VELVETY = "velvety"
    ROUGH = "rough"


# ========== Лактация ==========
class LactationState(Enum):
    OFF = auto()
    PREPARE = auto()
    ACTIVE = auto()
    ENGORGED = auto()
    DRYING = auto()


# ========== Давление ==========
class PressureTier(Enum):
    LOW = auto()
    HIGH = auto()
    CRITICAL = auto()


# ========== Вставляемые предметы ==========
class InsertableType(Enum):
    PLUG = auto()
    TUBE = auto()
    BALLOON = auto()
    BEADS = auto()
    EGG = auto()
    VIBRATOR = auto()
    NEEDLE = auto()
    CUSTOM = auto()


class InsertableMaterial(Enum):
    SILICONE = "silicone"
    LATEX = "latex"
    METAL = "metal"
    GLASS = "glass"
    PLASTIC = "plastic"
    RUBBER = "rubber"


# ========== Тело и гениталии ==========
class GenitalVisibility(Enum):
    """Уровень видимости гениталий."""
    COVERED = 0        # Полностью скрыты
    PARTIAL = 0.3      # Контуры видны
    EXPOSED = 0.7      # Открыты, но не детально
    FULL = 1.0         # Полностью видны все детали


class Sex(Enum):
    MALE = auto()
    FEMALE = auto()
    FUTANARI = auto()
    NONE = auto()


class BodyType(Enum):
    PETITE = "petite"
    SLENDER = "slender"
    AVERAGE = "average"
    CURVY = "curvy"
    MUSCULAR = "muscular"
    HEAVY = "heavy"
    AMAZON = "amazon"


class PenisType(Enum):
    HUMAN = ("human", "Обычный", {"length_factor": 1.0, "girth_factor": 1.0, "color": "pink"})
    
    # Фантастические типы
    KNOTTED = ("knotted", "Узловатый", {"length_factor": 0.9, "girth_factor": 1.3, "has_knot": True, "color": "red"})
    TAPERED = ("tapered", "Заострённый", {"length_factor": 1.2, "girth_factor": 0.8, "taper_ratio": 0.5, "color": "purple"})
    FLARED = ("flared", "Расширенный", {"length_factor": 1.0, "girth_factor": 1.1, "flare_factor": 1.5, "color": "magenta"})
    BARBED = ("barbed", "Шипастый", {"length_factor": 0.8, "girth_factor": 1.0, "has_barbs": True, "color": "dark_red"})
    DOUBLE = ("double", "Двойной", {"length_factor": 0.7, "girth_factor": 0.9, "count": 2, "color": "cyan"})
    PREHENSILE = ("prehensile", "Хватательный", {"length_factor": 1.5, "girth_factor": 0.7, "is_prehensile": True, "color": "green"})
    EQUINE = ("equine", "Конский", {"length_factor": 1.4, "girth_factor": 1.2, "flare_factor": 1.8, "color": "black"})
    CANINE = ("canine", "Собачий", {"length_factor": 1.1, "girth_factor": 1.15, "has_knot": True, "knot_factor": 1.5, "color": "red"})
    FELINE = ("feline", "Кошачий", {"length_factor": 0.85, "girth_factor": 1.0, "has_barbs": True, "barb_count": 100, "color": "pink"})
    DRAGON = ("dragon", "Драконий", {"length_factor": 1.6, "girth_factor": 1.4, "has_ridges": True, "ridge_count": 5, "color": "purple"})
    DEMON = ("demon", "Демонический", {"length_factor": 1.3, "girth_factor": 1.3, "has_spines": True, "glows": True, "color": "red"})
    TENTACLE = ("tentacle", "Щупальцевый", {"length_factor": 2.0, "girth_factor": 0.6, "is_prehensile": True, "can_split": True, "color": "green"})
    
    # Специальные
    HORSESHOE = ("horseshoe", "Подковообразный", {"length_factor": 0.6, "girth_factor": 1.5, "is_horseshoe": True, "color": "pink"})
    SPIRAL = ("spiral", "Спиральный", {"length_factor": 1.2, "girth_factor": 1.0, "has_spiral": True, "spiral_turns": 3, "color": "blue"})
    RIBBED = ("ribbed", "Ребристый", {"length_factor": 1.0, "girth_factor": 1.1, "has_ribs": True, "rib_count": 8, "color": "orange"})
    BIFURCATED = ("bifurcated", "Раздвоенный", {"length_factor": 0.9, "girth_factor": 0.95, "is_split": True, "split_depth": 0.5, "color": "pink"})
    
    def __init__(self, id: str, name: str, stats: dict):
        self.id = id
        self.type_name = name
        self.length_factor = stats.get("length_factor", 1.0)
        self.girth_factor = stats.get("girth_factor", 1.0)
        self.color = stats.get("color", "pink")
        
        # Особые характеристики
        self.has_knot = stats.get("has_knot", False)
        self.knot_factor = stats.get("knot_factor", 1.0)
        self.has_barbs = stats.get("has_barbs", False)
        self.barb_count = stats.get("barb_count", 0)
        self.has_ridges = stats.get("has_ridges", False)
        self.ridge_count = stats.get("ridge_count", 0)
        self.has_spines = stats.get("has_spines", False)
        self.is_prehensile = stats.get("is_prehensile", False)
        self.can_split = stats.get("can_split", False)
        self.flare_factor = stats.get("flare_factor", 1.0)
        self.taper_ratio = stats.get("taper_ratio", 1.0)
        self.count = stats.get("count", 1)
        self.is_horseshoe = stats.get("is_horseshoe", False)
        self.has_spiral = stats.get("has_spiral", False)
        self.spiral_turns = stats.get("spiral_turns", 0)
        self.has_ribs = stats.get("has_ribs", False)
        self.rib_count = stats.get("rib_count", 0)
        self.is_split = stats.get("is_split", False)
        self.split_depth = stats.get("split_depth", 0.0)
        self.glows = stats.get("glows", False)


class PenisState(Enum):
    """Состояние пениса."""
    FLACCID = auto()
    SEMI_ERECT = auto()
    ERECT = auto()
    ENGORGED = auto()  # Переполненный кровью
    KNOT_ENGORGED = auto()  # Узел раздут


class TesticleSize(Enum):
    MICRO = (5, 3)
    SMALL = (8, 8)
    AVERAGE = (12, 25)
    LARGE = (16, 50)
    HUGE = (20, 100)
    MASSIVE = (25, 200)
    HYPER = (35, 500)

    def __init__(self, length_mm: float, volume_ml: float):
        self.length = length_mm / 10
        self.volume = volume_ml


class ScrotumType(Enum):
    """Типы мошонок."""
    STANDARD = ("standard", "Обычная", {"capacity": 1.0, "hang": 1.0})
    TIGHT = ("tight", "Плотная", {"capacity": 0.8, "hang": 0.5, "retracts": True})
    LOOSE = ("loose", "Свисающая", {"capacity": 1.3, "hang": 1.5, "swings": True})
    SHEATHED = ("sheathed", "В ножне", {"capacity": 1.0, "hang": 0.3, "has_sheath": True})
    INTERNAL = ("internal", "Внутренняя", {"capacity": 0.9, "hang": 0.0, "is_internal": True})
    SEGMENTED = ("segmented", "Сегментированная", {"capacity": 1.2, "hang": 1.0, "has_segments": True, "segment_count": 3})
    
    def __init__(self, id: str, name: str, stats: dict):
        self.id = id
        self.type_name = name
        self.capacity = stats.get("capacity", 1.0)
        self.hang = stats.get("hang", 1.0)
        self.retracts = stats.get("retracts", False)
        self.swings = stats.get("swings", False)
        self.has_sheath = stats.get("has_sheath", False)
        self.is_internal = stats.get("is_internal", False)
        self.has_segments = stats.get("has_segments", False)
        self.segment_count = stats.get("segment_count", 1)


class VaginaType(Enum):
    """Типы влагалищ."""
    HUMAN = ("human", "Обычное", {"depth_factor": 1.0, "tightness": 1.0, "elasticity": 1.0})
    SINUOUS = ("sinuous", "Извилистое", {"depth_factor": 1.2, "tightness": 0.9, "elasticity": 1.1, "has_cervical_pouch": True})
    DEEPCAVE = ("deepcave", "Глубокое", {"depth_factor": 1.5, "tightness": 0.8, "elasticity": 0.9, "extra_depth": True})
    RIBBED = ("ribbed", "Ребристое", {"depth_factor": 1.0, "tightness": 1.1, "elasticity": 1.0, "has_ridges": True, "ridge_count": 12})
    TENTACLED = ("tentacled", "Щупальцевое", {"depth_factor": 1.3, "tightness": 0.7, "elasticity": 1.2, "has_tentacles": True})
    DEMONIC = ("demonic", "Демоническое", {"depth_factor": 1.4, "tightness": 0.85, "elasticity": 1.3, "self_lubricating": True, "glows": True})
    PLANT = ("plant", "Растительное", {"depth_factor": 1.1, "tightness": 0.9, "elasticity": 1.4, "can_expand": True, "photosensitive": True})
    SLIME = ("slime", "Слизистое", {"depth_factor": 1.2, "tightness": 0.6, "elasticity": 2.0, "is_slime": True, "can_reform": True})
    FELINE = ("feline", "Кошачее", {})
    
    def __init__(self, id: str, name: str, stats: dict):
        self.id = id
        self.type_name = name
        self.depth_factor = stats.get("depth_factor", 1.0)
        self.tightness = stats.get("tightness", 1.0)
        self.elasticity = stats.get("elasticity", 1.0)
        self.has_cervical_pouch = stats.get("has_cervical_pouch", False)
        self.extra_depth = stats.get("extra_depth", False)
        self.has_ridges = stats.get("has_ridges", False)
        self.ridge_count = stats.get("ridge_count", 0)
        self.has_tentacles = stats.get("has_tentacles", False)
        self.self_lubricating = stats.get("self_lubricating", False)
        self.glows = stats.get("glows", False)
        self.can_expand = stats.get("can_expand", False)
        self.photosensitive = stats.get("photosensitive", False)
        self.is_slime = stats.get("is_slime", False)
        self.can_reform = stats.get("can_reform", False)

class VaginaState(Enum):
    """Состояние влагалища."""
    NORMAL = auto()
    AROUSED = auto()
    ENGORGED = auto()
    STRETCHED = auto()
    CERVIX_DILATED = auto()

class UterusState(Enum):
    EMPTY = auto()
    NORMAL = auto()
    TENSE = auto()
    OVERPRESSURED = auto()
    LEAKING = auto()
    DESCENDED = auto()
    PROLAPSED = auto()
    EVERTED = auto()
    INVERTED = auto()

class UterusInflationStatus(Enum):
    """Статусы инфляции матки."""
    NORMAL = "normal"              # Нормальное состояние
    STRETCHED = "stretched"        # Растянута
    DISTENDED = "distended"        # Выпучена
    HYPERDISTENDED = "hyper"       # Сильно выпучена
    RUPTURE_RISK = "rupture_risk"  # Риск разрыва
    RUPTURED = "ruptured"          # Разорвана
    

class CervixState(Enum):
    """Состояния шейки матки."""
    CLOSED = auto()           # Закрыта
    DILATED = auto()          # Растворена
    FULLY_OPEN = auto()       # Полностью открыта
    EVERTED = auto()          # Вывернута вместе с маткой


class OvaryState(Enum):
    """Состояния яичника."""
    NORMAL = auto()           # Нормальное положение
    ENLARGED = auto()         # Увеличен (фолликулы/кисты)
    PROLAPSED = auto()        # Частично выпал через трубу
    EVERTED = auto()          # Полностью вывернут наружу
    TORSION = auto()          # Перекрут (опасное состояние)


class FallopianTubeState(Enum):
    """Состояния фаллопиевой трубы."""
    NORMAL = auto()           # Нормальное состояние
    DILATED = auto()          # Растянута
    BLOCKED = auto()          # Заблокирована
    PROLAPSED = auto()        # Выпала вместе с маткой
    EVERTED_WITH_OVARY = auto()  # Вывернута с яичником наружу


class OvaryType(Enum):
    """Типы яичников."""
    STANDARD = ("standard", "Обычные", {"egg_size": 1.0, "fertility": 1.0})
    HYPER = ("hyper", "Гиперактивные", {"egg_size": 0.8, "fertility": 1.5, "rapid_cycle": True})
    SWOLLEN = ("swollen", "Расширенные", {"egg_size": 1.5, "fertility": 0.9, "sensitive": True})
    PRODUCING = ("producing", "Продуктивные", {"egg_size": 1.0, "fertility": 2.0, "high_output": True})
    
    def __init__(self, id: str, name: str, stats: dict):
        self.id = id
        self.type_name = name
        self.egg_size = stats.get("egg_size", 1.0)
        self.fertility = stats.get("fertility", 1.0)
        self.rapid_cycle = stats.get("rapid_cycle", False)
        self.sensitive = stats.get("sensitive", False)
        self.high_output = stats.get("high_output", False)

class UterusType(Enum):
    """Типы маток."""
    STANDARD = ("standard", "Обычная", {"capacity": 1.0, "strength": 1.0})
    DUAL = ("dual", "Двойная", {"capacity": 0.8, "strength": 1.0, "chambers": 2})
    HEARTSHAPED = ("heartshaped", "Сердцевидная", {"capacity": 1.2, "strength": 1.1, "romantic_bonus": True})
    TILTED = ("tilted", "Наклонённая", {"capacity": 1.0, "strength": 0.9, "angle": 45})
    ELONGATED = ("elongated", "Вытянутая", {"capacity": 1.5, "strength": 0.8, "extra_depth": True})
    COMPACT = ("compact", "Компактная", {"capacity": 0.6, "strength": 1.3, "efficient": True})
    
    def __init__(self, id: str, name: str, stats: dict):
        self.id = id
        self.type_name = name
        self.capacity = stats.get("capacity", 1.0)
        self.strength = stats.get("strength", 1.0)
        self.chambers = stats.get("chambers", 1)
        self.romantic_bonus = stats.get("romantic_bonus", False)
        self.angle = stats.get("angle", 0)
        self.extra_depth = stats.get("extra_depth", False)
        self.efficient = stats.get("efficient", False)


class CervixType(Enum):
    """Типы шейки матки."""
    STANDARD = ("standard", "Обычная", {"tightness": 1.0, "dilation": 1.0})
    TIGHT = ("tight", "Тугая", {"tightness": 1.5, "dilation": 0.7})
    OPEN = ("open", "Открытая", {"tightness": 0.6, "dilation": 1.3})
    SENSITIVE = ("sensitive", "Чувствительная", {"tightness": 1.0, "dilation": 1.0, "sensitivity": 2.0})
    BARRED = ("barred", "Забаррикадированная", {"tightness": 2.0, "dilation": 0.5, "protective": True})
    
    def __init__(self, id: str, name: str, stats: dict):
        self.id = id
        self.type_name = name
        self.tightness = stats.get("tightness", 1.0)
        self.dilation = stats.get("dilation", 1.0)
        self.sensitivity = stats.get("sensitivity", 1.0)
        self.protective = stats.get("protective", False)


class AnusType(Enum):
    TIGHT = "tight"
    AVERAGE = "average"
    LOOSE = "loose"
    GAPING = "gaping"
    PROLAPSE = "prolapse"


# ========== События ==========
class EventType(Enum):
    STIMULATION = auto()
    AROUSAL_CHANGE = auto()
    ORGASM = auto()
    EJACULATION = auto()
    LACTATION_LET_DOWN = auto()
    PENETRATION_START = auto()
    PENETRATION_DEEP = auto()
    PENETRATION_RHYTHM = auto()
    WITHDRAWAL = auto()
    INSERTION_START = auto()
    INSERTION_DEEP = auto()
    INSERTION_MOVE = auto()
    EXTRACTION = auto()
    PAIN_THRESHOLD = auto()
    DAMAGE_TISSUE = auto()
    TEAR_WARNING = auto()
    PLEASURE_PEAK = auto()
    DISCOMFORT = auto()
    SATISFACTION = auto()
    FRUSTRATION = auto()
    PARTNER_STIMULATE = auto()
    PARTNER_PENETRATE = auto()
    PARTNER_EJACULATE = auto()
    FLUID_TRANSFER = auto()
    OVERSTIMULATION = auto()
    NUMBNESS = auto()
    SQUIRT = auto()
    PROLAPSE_RISK = auto()


class BreastEventType(Enum):
    """Типы событий груди для реакций."""
    START_LEAKING = auto()          # Начало утечки
    STOP_LEAKING = auto()           # Остановка утечки
    OVERPRESSURED = auto()          # Критическое давление
    ENGORGED = auto()               # Переполнение молоком
    CUP_INCREASE = auto()           # Увеличение размера
    CUP_DECREASE = auto()           # Уменьшение размера
    HIGH_SAG = auto()               # Сильное провисание
    INSERTION_START = auto()        # Начало вставки предмета
    INSERTION_DEEP = auto()         # Глубокая вставка
    LACTATION_START = auto()        # Начало лактации
    LACTATION_PEAK = auto()         # Пик лактации
    NIPPLE_STRETCH = auto()         # Растяжение соска
    NIPPLE_GAPING = auto()          # Раскрытие соска
    INFLATION_MAX = auto()          # Максимальное растяжение
    
class InsertionStatus(Enum):
    OUTSIDE = auto()
    INSERTING = auto()
    FULLY_INSERTED = auto()
    STUCK = auto()

# body_sim/appearance/enums.py
"""
Перечисления для системы внешности.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable
from body_sim.core.enums import Color, CupSize, PenisType, VaginaType, ScrotumType


class EyeType(Enum):
    """Типы глаз."""
    HUMAN = "human"                    # Человеческие
    ROUND = "round"                    # Круглые (аниме/фурри)
    SLIT = "slit"                      # Щелевидные зрачки (змеи/кошки)
    VERTICAL = "vertical"              # Вертикальные (кошачьи)
    HORIZONTAL = "horizontal"          # Горизонтальные (козы/овцы)
    MULTI_PUPIL = "multi_pupil"        # Множественные зрачки
    COMPOUND = "compound"              # Фасеточные (насекомые)
    GLOWING = "glowing"                # Светящиеся
    BLIND = "blind"                    # Слепые (без зрачков)
    EYELESS = "eyeless"                # Без глаз (слизь)
    EXTRA_EYES = "extra_eyes"          # Дополнительные глаза (3+)
    ALMOND = "almond"
    ELVEN = "elven"
    SLITTED = "slitted"
    ORCISH = "orcish"
    DEMONIC = "demonic"
    FELINE = "feline"
    CANINE = "canine"


class EyeColor(Enum):
    """Цвета глаз с RGB для рендеринга."""
    BLUE = ("blue", (100, 149, 237))
    GREEN = ("green", (34, 139, 34))
    BROWN = ("brown", (139, 69, 19))
    HAZEL = ("hazel", (165, 123, 60))
    GRAY = ("gray", (128, 128, 128))
    AMBER = ("amber", (255, 191, 0))
    RED = ("red", (220, 20, 60))
    VIOLET = ("violet", (138, 43, 226))
    CRIMSON = ("crimson", (153, 0, 0))
    GOLD = ("gold", (255, 215, 0))
    SILVER = ("silver", (192, 192, 192))
    BLACK = ("black", (0, 0, 0))
    WHITE = ("white", (255, 255, 255))
    HETEROCHROMIA = ("heterochromia", None)  # Разные цвета
    GLOWING_RED = ("glow_red", (255, 0, 0, 200))  # С свечением
    GLOWING_BLUE = ("glow_blue", (0, 100, 255, 200))
    GLOWING_GREEN = ("glow_green", (0, 255, 100, 200))
    
    def __init__(self, id: str, rgb):
        self.id = id
        self.rgb = rgb


class EarType(Enum):
    """Типы ушей."""
    HUMAN = "human"                    # Обычные человеческие
    ROUND = "round"                    # Круглые (короткие)
    POINTED = "pointed"                # Заостренные (эльфы)
    LONG_POINTED = "long_pointed"      # Длинные заостренные (высшие эльфы)
    ELVEN_LONG = "elven_long"
    CAT = "cat"                        # Кошачьи
    DOG = "dog"                        # Собачьи
    FOX = "fox"                        # Лисьи
    WOLF = "wolf"                      # Волчьи
    RABBIT = "rabbit"                  # Кроличьи (длинные)
    BEAR = "bear"                      # Медвежьи (круглые)
    MOUSE = "mouse"                    # Мышиные (круглые)
    BAT = "bat"                        # Летучие мыши
    GOAT = "goat"                      # Козлиные
    COW = "cow"                        # Коровьи
    DRAGON = "dragon"                  # Драконьи
    FISH = "fish"                      # Рыбьи (жабры)
    FIN = "fin"                        # Плавники
    ANTENNAE = "antennae"              # Антенны (насекомые)
    ORCISH = "orcish"
    NONE = "none"                      # Отсутствуют
    FELINE = "feline"
    CANINE = "canine"
    DEMON = "demon"

class HairType(Enum):
    """Типы волос/покрова."""
    HAIR = "hair"                      # Обычные волосы
    FUR = "fur"                        # Мех (фурри)
    FEATHERS = "feathers"              # Перья
    SCALES = "scales"                  # Чешуя
    SPIKES = "spikes"                  # Шипы
    TENTACLES = "tentacles"            # Щупальца (вместо волос)
    SLIME = "slime"                    # Слизистый покров
    CRYSTAL = "crystal"                # Кристаллы
    FIRE = "fire"                      # Пламя (магическое)
    ENERGY = "energy"                  # Энергетический покров
    NONE = "none"                      # Лысый/без покрова


class HairStyle(Enum):
    """Прически."""
    BALD = "bald"
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    VERY_LONG = "very_long"
    PONYTAIL = "ponytail"
    BRAID = "braid"
    TWIN_TAILS = "twin_tails"
    BUZZ_CUT = "buzz_cut"
    MOHAWK = "mohawk"
    AFRO = "afro"
    DREADLOCKS = "dreadlocks"
    CURLY = "curly"
    WAVY = "wavy"
    SPIKY = "spiky"
    Slicked_BACK = "slicked_back"
    BUNS = "buns"
    PIXIE_CUT = "pixie_cut"
    UNDERCUT = "undercut"


class HairColor(Enum):
    """Цвета волос."""
    BLACK = "black"
    DARK_BROWN = "dark_brown"
    BROWN = "brown"
    LIGHT_BROWN = "light_brown"
    AUBURN = "auburn"
    RED = "red"
    ORANGE = "orange"
    BLONDE = "blonde"
    PLATINUM_BLONDE = "platinum_blonde"
    WHITE = "white"
    GRAY = "gray"
    SILVER = "silver"
    BLUE = "blue"
    GREEN = "green"
    PINK = "pink"
    PURPLE = "purple"
    TEAL = "teal"
    MULTI_COLOR = "multi_color"
    RAINBOW = "rainbow"
    GRADIENT = "gradient"


class SkinTexture(Enum):
    """Текстура кожи."""
    SMOOTH = "smooth"                  # Гладкая
    ROUGH = "rough"                    # Грубая
    SCALY = "scaly"                    # Чешуйчатая
    FURRY = "furry"                    # Покрыта мехом
    FEATHERED = "feathered"            # Покрыта перьями
    SLIMY = "slimy"                    # Скользкая/слизистая
    CHITINOUS = "chitinous"            # Хитиновая (насекомые)
    STONE = "stone"                    # Каменная (големы)
    METALLIC = "metallic"              # Металлическая
    CRYSTALLINE = "crystalline"        # Кристаллическая
    PLANT = "plant"                    # Растительная (кора/листья)
    TRANSPARENT = "transparent"        # Прозрачная


class Race(Enum):
    """Расы с уникальными чертами."""
    HUMAN = "human"
    ELF = "elf"
    DARK_ELF = "dark_elf"
    ORC = "orc"
    DWARF = "dwarf"
    HALFLING = "halfling"
    DEMON = "demon"
    ANGEL = "angel"
    VAMPIRE = "vampire"
    WEREWOLF = "werewolf"
    # Фурри/зверолюди
    CATGIRL = "catgirl"
    FOXGIRL = "foxgirl"
    WOLFGIRL = "wolfgirl"
    BUNNYGIRL = "bunnygirl"
    DOGGIRL = "doggirl"
    BEARGIRL = "beargirl"
    COWGIRL = "cowgirl"
    MOUSEGIRL = "mousegirl"
    # Фантастические
    DRAGON = "dragon"
    LAMIA = "lamia"                    # Змея
    CENTAUR = "centaur"
    HARPY = "harpy"
    MERMAID = "mermaid"
    ARACHNE = "arachne"                # Паук
    SLIME = "slime"
    GOLEM = "golem"
    CYBORG = "cyborg"
    ALIEN = "alien"
    FELINE = "feline"
    CANINE = "canine"
    EQUINE = "equine"
    SHAPESHIFTER = "shapeshifter"
    MIGURDIAN = "migurdian"


class HornType(Enum):
    """Типы рогов."""
    NONE = "none"
    DEMON_CURVED = "demon_curved"      # Загнутые назад
    DEMON_STRAIGHT = "demon_straight"  # Прямые вверх
    DEMON_RAM = "demon_ram"            # Бараньи (круглые)
    DRAGON = "dragon"                  # Драконьи (задираются назад)
    UNICORN = "unicorn"                # Единорог (один)
    GOAT = "goat"                      # Козлиные
    ANTLER = "antler"                  # Рога оленя
    RHINO = "rhino"                    # Носовой рог
    STUBS = "stubs"                    # Короткие
    BROKEN = "broken"                  # Сломанные


class TailType(Enum):
    """Типы хвостов."""
    NONE = "none"
    HUMAN = "human"                    # Короткий хвостик (копчик)
    CAT = "cat"                        # Кошачий
    DOG = "dog"                        # Собачий
    FOX = "fox"                        # Лисий (пушистый)
    WOLF = "wolf"                      # Волчий
    BUNNY = "bunny"                    # Кроличий (помпон)
    COW = "cow"                        # Коровий (кисточка)
    HORSE = "horse"                    # Конский (длинный)
    LIZARD = "lizard"                  # Ящеричный
    DRAGON = "dragon"                  # Драконий
    DEMON = "demon"                    # Демонический (треугольный)
    DEVIL = "devil"                    # Дьявольский (стрелой)
    FISH = "fish"                      # Рыбий
    SCORPION = "scorpion"              # Скорпион (с жвалом)
    FEATHERED = "feathered"            # Перьевой
    ENERGY = "energy"                  # Энергетический
    SLIME = "slime"                    # Слизистый


class WingType(Enum):
    """Типы крыльев."""
    NONE = "none"
    FEATHERED = "feathered"            # Перьевые (ангел)
    BAT = "bat"                        # Кожаные (демон/летучая мышь)
    DRAGON = "dragon"                  # Драконьи (кожа + костяшки)
    BUTTERFLY = "butterfly"            # Бабочка
    DRAGONFLY = "dragonfly"            # Стрекоза
    BIRD = "bird"                      # Птичьи
    ENERGY = "energy"                  # Энергетические
    METALLIC = "metallic"              # Механические/кибернетические
    CRYSTAL = "crystal"                # Кристальные
    SLIME = "slime"                    # Слизистые


class FacialFeature(Enum):
    """Особенности лица."""
    SCARS = "scars"
    TATTOOS = "tattoos"
    PIERCINGS = "piercings"
    FRECKLES = "freckles"
    BEAUTY_MARK = "beauty_mark"
    VITILIGO = "vitiligo"
    ALBINO = "albino"
    MELANISTIC = "melanistic"
    GILLS = "gills"                    # Жабры
    EXTRA_MOUTH = "extra_mouth"        # Дополнительный рот
    THIRD_EYE = "third_eye"            # Третий глаз
    FANGED = "fanged"                  # Клыки
    BEAK = "beak"                      # Клюв
    SNOUT = "snout"                    # Морда
    WHISKERS = "whiskers"              # Усы (животные)


class BodyMarking(Enum):
    """Метки на теле."""
    NONE = "none"
    STRIPES = "stripes"                # Полосы (тигр)
    SPOTS = "spots"                    # Пятна (леопард)
    ROSETTES = "rosettes"              # Розетки (леопард)
    BRINDLE = "brindle"                # Тигриные полосы
    SOLID = "solid"                    # Однотонный
    POINTS = "points"                  # Сиамские отметины
    TABBY = "tabby"                    # Табби
    CALICO = "calico"                  # Калико
    PATCHED = "patched"                # Пегий
    MASK = "mask"                      # Маска на лице
    SOCKS = "socks"                    # Носки на лапах
    MAGIC_CIRCUIT = "magic_circuit"    # Магические цепи
    GLOWING_LINES = "glowing_lines"    # Светящиеся линии
    TRIBAL = "tribal"                  # Трайбл

@dataclass
class EyeAppearance:
    type: EyeType = EyeType.HUMAN
    color: Color = Color.BROWN
    glow: bool = False
    pupil_shape: str = "round"
    current_glow_intensity: float = 0.0  # Для анимации свечения
    
    def tick(self, dt: float):
        """Обновление глаз (мигание, пульсация свечения)."""
        if self.glow:
            # Пульсация свечения
            import math
            self.current_glow_intensity = 0.7 + 0.3 * math.sin(math.pi * 2 * dt)

@dataclass  
class EarAppearance:
    type: EarType = EarType.HUMAN
    length: float = 2.0
    mobility: float = 0.0  # 0-1 для подвижных ушей
    current_position: str = "neutral"  # neutral, perked, flattened, rotated
    
    def perk(self):
        """Навострить уши (для звероликих рас)."""
        if self.mobility > 0:
            self.current_position = "perked"
    
    def flatten(self):
        """Прижать уши (испуг/агрессия)."""
        if self.mobility > 0:
            self.current_position = "flattened"
    
    def tick(self, dt: float):
        """Возврат к нейтральному положению."""
        if self.mobility > 0 and random.random() < 0.1 * dt:
            self.current_position = "neutral"

RACE_ANATOMY_PRESETS: Dict[Race, Dict[str, Any]] = {
    Race.HUMAN: {
        "penis_length": (12.0, 18.0),
        "penis_girth": (10.0, 14.0),
        "vagina_depth": (9.0, 12.0),
        "breast_cup": [CupSize.A, CupSize.B, CupSize.C, CupSize.D],
        "nipple_color": Color.LIGHT_PINK,
        "areola_size": 3.0,
        "ear_type": EarType.HUMAN,
        "eye_types": [EyeType.HUMAN, EyeType.ALMOND],
        "elasticity": 0.8,
        "skin_color": Color.LIGHT_BEIGE,
        "skin_texture": "smooth",
    },
    Race.ELF: {
        "penis_length": (14.0, 20.0),      # Длиннее
        "penis_girth": (9.0, 12.0),        # Но уже
        "vagina_depth": (11.0, 14.0),      # Глубже
        "breast_cup": [CupSize.A, CupSize.B, CupSize.C],  # Стройнее
        "nipple_color": Color.PALE_PINK,
        "areola_size": 2.5,
        "ear_type": EarType.ELVEN_LONG,
        "eye_types": [EyeType.ELVEN, EyeType.ALMOND, EyeType.SLITTED],
        "elasticity": 0.9,                 # Более эластичные
        "skin_color": Color.PALE_IVORY,
        "skin_texture": "smooth",
    },
    Race.ORC: {
        "penis_length": (18.0, 28.0),      # Крупнее
        "penis_girth": (14.0, 18.0),
        "vagina_depth": (10.0, 13.0),
        "breast_cup": [CupSize.D, CupSize.E, CupSize.F],  # Массивнее
        "nipple_color": Color.DARK_BROWN,
        "areola_size": 4.5,
        "ear_type": EarType.ORCISH,
        "eye_types": [EyeType.ORCISH, EyeType.SLITTED],
        "elasticity": 0.6,                 # Менее эластичные, но прочные
        "skin_color": Color.GREEN,
        "skin_texture": "rough",
    },
    Race.DEMON: {
        "penis_type": PenisType.DEMON,
        "vagina_type": VaginaType.DEMONIC,
        "penis_length": (16.0, 25.0),
        "penis_girth": (12.0, 16.0),
        "vagina_depth": (11.0, 15.0),
        "breast_cup": [CupSize.C, CupSize.D, CupSize.E],
        "nipple_color": Color.DARK_RED,
        "areola_size": 4.0,
        "ear_type": EarType.POINTED,
        "eye_types": [EyeType.DEMONIC, EyeType.SLITTED, EyeType.GLOWING],
        "elasticity": 0.85,
        "skin_color": Color.RED,
        "skin_texture": "smooth",
    },
    Race.FELINE: {
        "penis_type": PenisType.FELINE,    # Шипастый/заостренный
        "vagina_type": VaginaType.FELINE,
        "penis_length": (10.0, 15.0),
        "penis_girth": (8.0, 11.0),
        "vagina_depth": (8.0, 11.0),
        "breast_cup": [CupSize.B, CupSize.C, CupSize.D],
        "nipple_color": Color.PINK,
        "areola_size": 3.0,
        "ear_type": EarType.FELINE,
        "eye_types": [EyeType.FELINE, EyeType.SLITTED],
        "elasticity": 0.9,
        "skin_color": Color.BEIGE,
        "skin_texture": "smooth_with_fur",
    },
    Race.CANINE: {
        "penis_type": PenisType.CANINE,    # Узел
        "scrotum_type": ScrotumType.SHEATHED,
        "penis_length": (15.0, 22.0),
        "penis_girth": (11.0, 15.0),
        "vagina_depth": (9.0, 12.0),
        "breast_cup": [CupSize.C, CupSize.D, CupSize.E],
        "nipple_color": Color.DARK_PINK,
        "areola_size": 3.5,
        "ear_type": EarType.CANINE,
        "eye_types": [EyeType.CANINE],
        "elasticity": 0.75,
        "skin_color": Color.TAN,
        "skin_texture": "fur",
    },
    Race.MIGURDIAN: {
        "penis_length": (12.0, 16.0),
        "penis_girth": (9.0, 12.0),
        "vagina_depth": (7.0, 9.0),      # Меньше среднего (компактное телосложение)
        "breast_cup": [CupSize.AA, CupSize.A, CupSize.B],  # Миниатюрные
        "nipple_color": Color.PALE_PINK,
        "areola_size": 2.5,              # Маленькие ареолы
        "ear_type": EarType.DEMON,       # Острые как у демонов, но короткие
        "eye_types": [EyeType.DEMONIC],  # Ахроматические
        "elasticity": 0.95,              # Очень эластичная кожа
        "skin_color": Color.PALE_IVORY,
        "skin_texture": "smooth_sensitive",
        "height_range": (140.0, 155.0),  # Низкий рост
    },
}

# body_sim/appearance/features.py
"""
Базовые классы для черт внешности.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from body_sim.appearance.enums import (
    EyeType, EyeColor, EarType, HairType, HairStyle, HairColor,
    HornType, TailType, WingType, SkinTexture
)


@dataclass
class Eye:
    """Глаз с детальной конфигурацией."""
    eye_type: EyeType = EyeType.HUMAN
    color: EyeColor = EyeColor.BROWN
    secondary_color: Optional[EyeColor] = None  # Для гетерохромии/градиентов
    size: float = 1.0  # Множитель размера
    glow_intensity: float = 0.0  # 0-1 для свечения
    has_eyelashes: bool = True
    pupil_dilation: float = 0.5  # 0-1 (суженый-расширенный)
    
    # Особые эффекты
    is_magical: bool = False
    magic_effect: Optional[str] = None  # "fire", "ice", "stars" и т.д.
    
    def __post_init__(self):
        if self.eye_type == EyeType.GLOWING and self.glow_intensity == 0:
            self.glow_intensity = 0.7
    
    @property
    def display_color(self) -> Tuple:
        """Возвращает RGB цвет для рендеринга."""
        if self.color.rgb:
            return self.color.rgb
        return (100, 100, 100)  # Default gray
    
    def dilate(self, amount: float) -> None:
        """Изменить размер зрачка."""
        self.pupil_dilation = max(0.0, min(1.0, self.pupil_dilation + amount))


@dataclass
class Ear:
    """Ухо с поддержкой разных типов."""
    ear_type: EarType = EarType.HUMAN
    size: float = 1.0  # Множитель размера (0.5 - маленькие, 2.0 - огромные)
    position: float = 0.0  # Угол наклона (-0.5 назад, 0.5 вперед)
    mobility: float = 0.0  # Подвижность (0-1, для животных ушей)
    
    # Покрытие
    has_fur: bool = False
    fur_color: Optional[HairColor] = None
    fur_length: str = "short"  # short, medium, long
    
    # Пирсинг
    piercings: List[str] = field(default_factory=list)  # ["lobe", "helix", "industrial"]
    
    def twitch(self) -> None:
        """Дёрнуть ухом (если подвижное)."""
        if self.mobility > 0.3:
            self.position = (self.position + 0.2) % 1.0 - 0.5
    
    def flatten(self) -> None:
        """Прижать уши (страх/агрессия у животных)."""
        self.position = -0.4
    
    def perk_up(self) -> None:
        """Навострить уши (интерес)."""
        self.position = 0.3


@dataclass 
class Hair:
    """Волосы или альтернативный покров головы."""
    hair_type: HairType = HairType.HAIR
    style: HairStyle = HairStyle.MEDIUM
    color: HairColor = HairColor.BROWN
    secondary_color: Optional[HairColor] = None  # Для омбре/выделения
    
    # Физические параметры
    length: float = 30.0  # Длина в см
    volume: float = 1.0   # Объем/густота
    texture: str = "straight"  # straight, wavy, curly, coily
    
    # Специальные эффекты
    is_animating: bool = False  # Движется ли (огонь/энергия)
    glow_intensity: float = 0.0
    transparency: float = 0.0   # 0-1 для призраков/слизней
    
    # Для фурри
    pattern: Optional[str] = None  # "stripes", "spots", "gradient"
    
    def cut(self, new_length: float) -> None:
        """Подстричь волосы."""
        self.length = max(0, new_length)
        if self.length < 5:
            self.style = HairStyle.SHORT
        elif self.length < 20:
            self.style = HairStyle.MEDIUM
    
    def dye(self, new_color: HairColor, secondary: Optional[HairColor] = None) -> None:
        """Покрасить волосы."""
        self.color = new_color
        if secondary:
            self.secondary_color = secondary


@dataclass
class Horn:
    """Рога/рожки."""
    horn_type: HornType = HornType.NONE
    count: int = 2  # Количество (единорог = 1, демон = 2, олень = много)
    length: float = 10.0  # см
    thickness: float = 1.0  # множитель
    curvature: float = 0.5  # 0 - прямые, 1 - сильно загнутые
    color: str = "#D2B48C"  # Цвет (обычно бежевый/костяной)
    
    # Материал
    is_bone: bool = True
    is_metallic: bool = False
    glows: bool = False
    glow_color: Optional[str] = None
    
    def grow(self, amount: float) -> None:
        """Вырастить рога (или отрастить сломанные)."""
        self.length += amount
        if self.length > 5 and self.horn_type == HornType.STUBS:
            self.horn_type = HornType.DEMON_STRAIGHT
    
    def break_horns(self) -> None:
        """Сломать рога (бой)."""
        self.length *= 0.3
        self.horn_type = HornType.BROKEN


@dataclass
class Tail:
    """Хвост."""
    tail_type: TailType = TailType.NONE
    length: float = 0.0  # см
    thickness: float = 1.0
    fluffiness: float = 0.5  # 0-1 (гладкий-пушистый)
    
    # Покрытие
    color: str = "brown"
    has_pattern: bool = False
    pattern_type: Optional[str] = None  # "striped", "spotted"
    
    # Управление
    prehensile: bool = False  # Может ли хватать
    expression: str = "neutral"  # happy, angry, fearful (для хвоста)
    
    def wag(self, intensity: float = 0.5) -> str:
        """Вилять хвостом."""
        if self.tail_type in [TailType.DOG, TailType.CAT, TailType.FOX]:
            self.expression = "happy" if intensity > 0.5 else "neutral"
            return f"Хвост виляет с интенсивностью {intensity}"
        return "Хвост не подходит для виляния"
    
    def lash(self) -> str:
        """Хлестать хвостом (злость)."""
        self.expression = "angry"
        return "Хвост бьет по земле"


@dataclass
class Wings:
    """Крылья."""
    wing_type: WingType = WingType.NONE
    span: float = 0.0  # Размах в см
    condition: float = 1.0  # 0-1 (поврежденные-целые)
    
    # Особенности
    can_fly: bool = False
    is_hidden: bool = True  # Спрятаны (ангелы часто прячут)
    color_primary: str = "white"
    color_secondary: Optional[str] = None
    
    def unfold(self) -> None:
        """Развернуть крылья."""
        self.is_hidden = False
    
    def fold(self) -> None:
        """Сложить крылья."""
        self.is_hidden = True
    
    def damage(self, amount: float) -> None:
        """Повредить крылья (падение, бой)."""
        self.condition = max(0.0, self.condition - amount)
        self.can_fly = self.condition > 0.5 and self.wing_type not in [WingType.ENERGY]


@dataclass
class FacialStructure:
    """Структура лица/черепа."""
    jaw_width: float = 1.0
    cheekbone_height: float = 1.0
    nose_bridge: float = 1.0
    brow_ridge: float = 1.0
    
    # Расовые модификаторы
    snout_length: float = 0.0  # 0 - плоское лицо, 1 - морда
    muzzle_width: float = 1.0
    
    # Особенности
    has_fangs: bool = False
    fang_size: float = 0.0  # см
    has_whiskers: bool = False
    whisker_length: float = 0.0


@dataclass
class Skin:
    """Кожа/покров тела."""
    texture: SkinTexture = SkinTexture.SMOOTH
    base_color: str = "#F5DEB3"  # Пшеница по умолчанию
    secondary_color: Optional[str] = None  # Для пятнистых/полосатых
    
    # Параметры
    transparency: float = 0.0
    glossiness: float = 0.0  # Блеск (0-1)
    wetness: float = 0.0     # Влажность (для слизней/амфибий)
    
    # Особенности
    markings: List[str] = field(default_factory=list)  # Типы меток из BodyMarking
    scars: List[Tuple[str, float]] = field(default_factory=list)  # (location, severity)
    tattoos: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_scar(self, location: str, severity: float = 0.5) -> None:
        """Добавить шрам."""
        self.scars.append((location, severity))
    
    def add_tattoo(self, design: str, location: str, color: str = "black") -> None:
        """Добавить татуировку."""
        self.tattoos.append({"design": design, "location": location, "color": color})
    
    def change_texture(self, new_texture: SkinTexture) -> None:
        """Изменить текстуру (трансформация/заклинание)."""
        old = self.texture
        self.texture = new_texture
        # Авто-настройка параметров
        if new_texture == SkinTexture.SLIMY:
            self.wetness = 0.8
            self.glossiness = 0.9
        elif new_texture == SkinTexture.METALLIC:
            self.glossiness = 1.0
            self.wetness = 0.0


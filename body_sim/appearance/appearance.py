# body_sim/appearance/appearance.py
"""
Основной класс внешности, объединяющий все черты.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from body_sim.appearance.enums import (
    Race, EyeType, EyeColor, EarType, HairType, HairStyle, HairColor,
    HornType, TailType, WingType, SkinTexture, FacialFeature, BodyMarking
)
from body_sim.appearance.features import (
    Eye, Ear, Hair, Horn, Tail, Wings, FacialStructure, Skin
)
from body_sim.core.enums import Color as BodyColor


@dataclass
class Appearance:
    """Полная внешность существа."""
    race: Race = Race.HUMAN
    
    # Глаза (список для многоглазых существ)
    eyes: List[Eye] = field(default_factory=lambda: [Eye()])
    
    # Уши (обычно 2, но может быть больше)
    ears: List[Ear] = field(default_factory=lambda: [Ear(), Ear()])
    
    # Волосы/покров
    hair: Hair = field(default_factory=Hair)
    
    # Роговые структуры
    horns: List[Horn] = field(default_factory=list)
    
    # Хвост
    tail: Tail = field(default_factory=lambda: Tail(TailType.NONE))
    
    # Крылья
    wings: Wings = field(default_factory=lambda: Wings(WingType.NONE))
    
    # Лицо и кожа
    face: FacialStructure = field(default_factory=FacialStructure)
    skin: Skin = field(default_factory=Skin)
    
    # Особенности
    facial_features: List[FacialFeature] = field(default_factory=list)
    height: float = 170.0  # см
    build: str = "average"  # petite, slender, average, athletic, muscular, heavy
    
    # События
    _listeners: Dict[str, List[Callable]] = field(default_factory=dict, repr=False)
    
    def __post_init__(self):
        """Применить расовые шаблоны если не заданы явно."""
        if not self._is_customized():
            self.apply_race_template()
    
    def _is_customized(self) -> bool:
        """Проверяет, были ли параметры изменены от дефолтных."""
        return len(self.eyes) > 1 or len(self.horns) > 0 or self.tail.tail_type != TailType.NONE
    
    def on(self, event: str, callback: Callable[..., Any]) -> None:
        """Подписаться на событие изменения внешности."""
        self._listeners.setdefault(event, []).append(callback)
    
    def _emit(self, event: str, **data: Any) -> None:
        """Вызвать событие."""
        for cb in self._listeners.get(event, []):
            cb(self, **data)
    
    def apply_race_template(self) -> None:
        """Применить шаблон внешности для текущей расы."""
        templates = {
            Race.HUMAN: self._template_human,
            Race.ELF: self._template_elf,
            Race.DARK_ELF: self._template_dark_elf,
            Race.ORC: self._template_orc,
            Race.DEMON: self._template_demon,
            Race.ANGEL: self._template_angel,
            Race.VAMPIRE: self._template_vampire,
            Race.CATGIRL: self._template_cat,
            Race.FOXGIRL: self._template_fox,
            Race.WOLFGIRL: self._template_wolf,
            Race.BUNNYGIRL: self._template_bunny,
            Race.DRAGON: self._template_dragon,
            Race.SLIME: self._template_slime,
            Race.CYBORG: self._template_cyborg,
        }
        
        template_func = templates.get(self.race, self._template_human)
        template_func()
        self._emit("race_template_applied", race=self.race)
    
    # === Шаблоны рас ===
    
    def _template_human(self):
        self.eyes = [Eye(EyeType.HUMAN, EyeColor.BROWN)]
        self.ears = [Ear(EarType.HUMAN), Ear(EarType.HUMAN)]
        self.hair = Hair(HairType.HAIR, HairStyle.MEDIUM, HairColor.BROWN, length=40)
        self.horns = []
        self.tail = Tail(TailType.NONE)
        self.wings = Wings(WingType.NONE)
        self.skin = Skin(SkinTexture.SMOOTH, "#F5DEB3")
        self.height = 170.0
    
    def _template_elf(self):
        self.eyes = [Eye(EyeType.HUMAN, EyeColor.BLUE)]
        self.ears = [Ear(EarType.LONG_POINTED, size=1.5, mobility=0.2)]
        self.hair = Hair(HairType.HAIR, HairStyle.LONG, HairColor.BLONDE, length=80)
        self.skin = Skin(SkinTexture.SMOOTH, "#FFE4C4")  # Бисквитный
        self.height = 175.0
        self.build = "slender"
    
    def _template_dark_elf(self):
        self.eyes = [Eye(EyeType.HUMAN, EyeColor.RED)]
        self.ears = [Ear(EarType.LONG_POINTED, size=1.6)]
        self.hair = Hair(HairType.HAIR, HairStyle.LONG, HairColor.WHITE, length=90)
        self.skin = Skin(SkinTexture.SMOOTH, "#2F4F4F")  # Темно-серый
        self.height = 170.0
    
    def _template_orc(self):
        self.eyes = [Eye(EyeType.SLIT, EyeColor.AMBER)]
        self.ears = [Ear(EarType.POINTED, size=0.8)]
        self.hair = Hair(HairType.HAIR, HairStyle.MOHAWK, HairColor.BLACK, length=15)
        self.skin = Skin(SkinTexture.ROUGH, "#556B2F")  # Темно-оливковый
        self.face = FacialStructure(jaw_width=1.3, brow_ridge=1.5, has_fangs=True, fang_size=1.5)
        self.height = 190.0
        self.build = "muscular"
    
    def _template_demon(self):
        self.eyes = [Eye(EyeType.SLIT, EyeColor.CRIMSON, glow_intensity=0.5)]
        self.ears = [Ear(EarType.POINTED, size=1.2)]
        self.hair = Hair(HairType.HAIR, HairStyle.LONG, HairColor.BLACK, length=60)
        self.horns = [Horn(HornType.DEMON_CURVED, count=2, length=25, curvature=0.7, color="#8B0000")]
        self.tail = Tail(TailType.DEMON, length=60, color="red", prehensile=True)
        self.wings = Wings(WingType.BAT, span=300, can_fly=True, color_primary="black")
        self.skin = Skin(SkinTexture.SMOOTH, "#CD5C5C")  # Индийский красный
        self.height = 180.0
        self.facial_features = [FacialFeature.FANGED]
    
    def _template_angel(self):
        self.eyes = [Eye(EyeType.HUMAN, EyeColor.GOLD, glow_intensity=0.3)]
        self.ears = [Ear(EarType.HUMAN)]
        self.hair = Hair(HairType.HAIR, HairStyle.LONG, HairColor.PLATINUM_BLONDE, length=100)
        self.wings = Wings(WingType.FEATHERED, span=350, can_fly=True, color_primary="white")
        self.skin = Skin(SkinTexture.SMOOTH, "#FFFAF0")  # Цветочный белый
        self.height = 180.0
    
    def _template_vampire(self):
        self.eyes = [Eye(EyeType.HUMAN, EyeColor.RED, glow_intensity=0.2)]
        self.ears = [Ear(EarType.SLIGHTLY_POINTED)]
        self.hair = Hair(HairType.HAIR, HairStyle.SLICKED_BACK, HairColor.BLACK)
        self.face = FacialStructure(has_fangs=True, fang_size=1.2)
        self.skin = Skin(SkinTexture.SMOOTH, "#F0F8FF", transparency=0.1)  # Призрачно-белый
        self.facial_features = [FacialFeature.FANGED]
    
    def _template_cat(self):
        self.eyes = [Eye(EyeType.VERTICAL, EyeColor.GREEN)]
        self.ears = [Ear(EarType.CAT, size=1.3, mobility=0.9, has_fur=True, fur_color=HairColor.BROWN)]
        self.hair = Hair(HairType.FUR, HairStyle.MEDIUM, HairColor.BROWN)
        self.tail = Tail(TailType.CAT, length=50, fluffiness=0.6, color="brown")
        self.skin = Skin(SkinTexture.FURRY)
        self.skin.markings = [BodyMarking.STRIPES.value]
        self.face = FacialStructure(has_whiskers=True, whisker_length=5.0, snout_length=0.1)
        self.height = 165.0
    
    def _template_fox(self):
        self.eyes = [Eye(EyeType.VERTICAL, EyeColor.AMBER)]
        self.ears = [Ear(EarType.FOX, size=1.4, mobility=0.8, has_fur=True)]
        self.hair = Hair(HairType.FUR, HairStyle.LONG, HairColor.RED)
        self.tail = Tail(TailType.FOX, length=70, fluffiness=0.9, color="orange", has_pattern=True, pattern_type="white_tip")
        self.skin = Skin(SkinTexture.FURRY)
        self.height = 168.0
    
    def _template_wolf(self):
        self.eyes = [Eye(EyeType.ROUND, EyeColor.GOLD)]
        self.ears = [Ear(EarType.WOLF, size=1.2, mobility=0.7, has_fur=True)]
        self.hair = Hair(HairType.FUR, HairStyle.MEDIUM, HairColor.GRAY)
        self.tail = Tail(TailType.WOLF, length=45, fluffiness=0.7, color="gray")
        self.skin = Skin(SkinTexture.FURRY)
        self.face = FacialStructure(has_fangs=True, fang_size=0.8, snout_length=0.15)
        self.height = 175.0
        self.build = "athletic"
    
    def _template_bunny(self):
        self.eyes = [Eye(EyeType.ROUND, EyeColor.RED)]
        self.ears = [Ear(EarType.RABBIT, size=2.0, mobility=0.6)]
        self.hair = Hair(HairType.FUR, HairStyle.SHORT, HairColor.WHITE)
        self.tail = Tail(TailType.BUNNY, length=5, fluffiness=1.0, color="white")
        self.skin = Skin(SkinTexture.FURRY, "#FFE4E1")
        self.height = 160.0
        self.build = "petite"
    
    def _template_dragon(self):
        self.eyes = [Eye(EyeType.SLIT, EyeColor.GOLD, glow_intensity=0.4)]
        self.ears = [Ear(EarType.DRAGON, size=0.8)]
        self.hair = Hair(HairType.SPIKES, HairStyle.SPIKY, HairColor.BLACK)
        self.horns = [
            Horn(HornType.DRAGON, count=2, length=40, curvature=0.3),
            Horn(HornType.DRAGON, count=2, length=20, curvature=0.8)  # Маленькие боковые
        ]
        self.tail = Tail(TailType.DRAGON, length=100, thickness=2.0, prehensile=True, color="red")
        self.wings = Wings(WingType.DRAGON, span=400, can_fly=True)
        self.skin = Skin(SkinTexture.SCALY, "#8B4513")
        self.height = 200.0
        self.build = "muscular"
    
    def _template_slime(self):
        self.eyes = [Eye(EyeType.GLOWING, EyeColor.BLUE, glow_intensity=0.8)]
        self.ears = [Ear(EarType.NONE)]
        self.hair = Hair(HairType.SLIME, HairStyle.LONG, HairColor.BLUE, transparency=0.7)
        self.skin = Skin(SkinTexture.TRANSPARENT, "#00CED1", transparency=0.6, glossiness=1.0, wetness=1.0)
        self.height = 165.0
        self.build = "slender"
    
    def _template_cyborg(self):
        self.eyes = [Eye(EyeType.GLOWING, EyeColor.GLOWING_BLUE, glow_intensity=0.9)]
        self.ears = [Ear(EarType.HUMAN)]
        self.hair = Hair(HairType.HAIR, HairStyle.SHORT, HairColor.BLACK)
        self.skin = Skin(SkinTexture.METALLIC, "#C0C0C0", glossiness=0.8)
        self.facial_features = [FacialFeature.PIERCINGS]
        self.height = 175.0
    
    # === Методы изменения ===
    
    def transform_race(self, new_race: Race, gradual: bool = False) -> None:
        """Трансформировать в другую расу."""
        old_race = self.race
        self.race = new_race
        
        if gradual:
            # Частичное применение (для анимации трансформации)
            pass
        else:
            self.apply_race_template()
        
        self._emit("race_changed", old_race=old_race, new_race=new_race)
    
    def add_eye(self, eye_type: EyeType = EyeType.HUMAN, color: EyeColor = EyeColor.BLUE) -> None:
        """Добавить дополнительный глаз (мутант/мистик)."""
        new_eye = Eye(eye_type, color)
        self.eyes.append(new_eye)
        self._emit("eye_added", eye=new_eye, total_count=len(self.eyes))
    
    def remove_eye(self, index: int) -> bool:
        """Удалить глаз (травма?)."""
        if len(self.eyes) > 1 and 0 <= index < len(self.eyes):
            removed = self.eyes.pop(index)
            self._emit("eye_removed", eye=removed, remaining=len(self.eyes))
            return True
        return False
    
    def set_heterochromia(self, color1: EyeColor, color2: EyeColor) -> None:
        """Установить разный цвет глаз."""
        if len(self.eyes) >= 2:
            self.eyes[0].color = color1
            self.eyes[1].color = color2
            self.eyes[0].secondary_color = color2
            self.eyes[1].secondary_color = color1
    
    def get_description(self) -> str:
        """Получить текстовое описание внешности."""
        parts = []
        
        # Основное
        parts.append(f"{self.race.value}, {self.height}см, телосложение {self.build}")
        
        # Глаза
        if self.eyes:
            eye_desc = f"{len(self.eyes)} глаз(а): " + ", ".join([
                f"{e.color.value} ({e.eye_type.value})" for e in self.eyes
            ])
            parts.append(eye_desc)
        
        # Уши
        if self.ears:
            ear_types = set(e.ear_type.value for e in self.ears)
            parts.append(f"Уши: {', '.join(ear_types)}")
        
        # Особенности
        features = []
        if self.horns:
            features.append(f"рога ({len(self.horns)} шт)")
        if self.tail.tail_type != TailType.NONE:
            features.append(f"хвост ({self.tail.tail_type.value})")
        if self.wings.wing_type != WingType.NONE:
            features.append(f"крылья ({self.wings.wing_type.value})")
        if self.face.has_fangs:
            features.append("клыки")
        
        if features:
            parts.append("Особенности: " + ", ".join(features))
        
        return "; ".join(parts)
    
    def tick(self, dt: float) -> None:
        """Обновление состояния (анимация, эффекты)."""
        # Обновление глаз (зрачки могут реагировать на свет)
        for eye in self.eyes:
            # Случайное мигание
            import random
            if random.random() < 0.01 * dt:
                pass  # Мигание
        
        # Обновление волос (физика)
        if self.hair.is_animating:
            pass  # Анимация огня/энергии
        
        # Хвост (физика)
        if self.tail.tail_type != TailType.NONE:
            pass  # Физика движения


# body_sim/appearance/body_integration.py
"""
Пример интеграции Appearance с классом Body.
Добавьте это в body.py или используйте как миксин.
"""

import random
from dataclasses import dataclass, field
from typing import Optional

from .appearance import Appearance, Race
from .enums import *



@dataclass
class AppearanceMixin:
    """
    Миксин внешности. Управляет расой, глазами, ушами, кожей.
    """
    race: Race = Race.HUMAN
    eyes: EyeAppearance = field(default_factory=EyeAppearance)
    ears: EarAppearance = field(default_factory=EarAppearance)
    skin_color: Color = Color.LIGHT_BEIGE
    skin_texture: str = "smooth"
    
    # Внутренние
    _preset: Dict[str, Any] = field(default_factory=dict, repr=False)
    _appearance_listeners: Dict[str, List[Callable]] = field(default_factory=dict, repr=False)
    
    def __post_init__(self):
        """Инициализация пресета расы."""
        self._preset = self._get_preset()
        self._setup_race_appearance()
    
    def _get_preset(self) -> Dict[str, Any]:
        """Получить текущий пресет расы."""
        return RACE_ANATOMY_PRESETS.get(self.race, RACE_ANATOMY_PRESETS[Race.HUMAN])
    
    def _setup_race_appearance(self):
        """Настроить внешность по расовому пресету."""
        preset = self._preset
        
        # Уши
        if "ear_type" in preset:
            mobility = 0.0
            if preset["ear_type"] in (EarType.FELINE, EarType.CANINE, EarType.ELVEN_LONG):
                mobility = 0.8
            elif preset["ear_type"] == EarType.ORCISH:
                mobility = 0.3
                
            self.ears = EarAppearance(
                type=preset["ear_type"],
                length=6.0 if preset["ear_type"] == EarType.ELVEN_LONG else 2.0,
                mobility=mobility
            )
        
        # Глаза
        if "eye_types" in preset:
            eye_type = random.choice(preset["eye_types"])
            glow = eye_type in (EyeType.DEMONIC, EyeType.GLOWING)
            self.eyes = EyeAppearance(
                type=eye_type,
                color=self._get_eye_color_for_race(),
                glow=glow
            )
        
        # Кожа
        if "skin_color" in preset:
            self.skin_color = preset["skin_color"]
        if "skin_texture" in preset:
            self.skin_texture = preset["skin_texture"]
        
        # Рост (если не задан)
        if hasattr(self, 'height') and self.height == 0:
            if "height_range" in preset:
                self.height = random.uniform(*preset["height_range"])
    
    def _get_eye_color_for_race(self) -> Color:
        """Определить цвет глаз по расе."""
        color_map = {
            Race.HUMAN: [Color.BROWN, Color.BLUE, Color.GREEN, Color.GRAY],
            Race.ELF: [Color.GOLD, Color.SILVER, Color.GREEN, Color.BLUE],
            Race.ORC: [Color.RED, Color.YELLOW, Color.BLACK],
            Race.DEMON: [Color.RED, Color.PURPLE, Color.YELLOW],
            Race.FELINE: [Color.GOLD, Color.GREEN],
            Race.CANINE: [Color.BROWN, Color.BLUE, Color.GOLD],
            Race.DRAGON: [Color.RED, Color.GOLD, Color.PURPLE],
            Race.ANGEL: [Color.GOLD, Color.BLUE, Color.WHITE],
            Race.SLIME: [Color.TRANSLUCENT],
            Race.CYBORG: [Color.RED, Color.BLUE, Color.GREEN],  # LED colors
        }
        colors = color_map.get(self.race, [Color.BROWN])
        return random.choice(colors)
    
    def change_race(self, new_race: Race, regenerate: bool = True) -> Dict[str, Any]:
        """
        Сменить расу с перегенерацией внешности.
        Возвращает изменения для логирования.
        """
        old_race = self.race
        old_preset = self._preset
        
        self.race = new_race
        self._preset = self._get_preset()
        
        changes = {
            "old_race": old_race,
            "new_race": new_race,
            "changes": []
        }
        
        # Обновляем внешность
        if old_preset.get("ear_type") != self._preset.get("ear_type"):
            old_ears = self.ears.type
            self._setup_race_appearance()
            changes["changes"].append(f"ears: {old_ears} -> {self.ears.type}")
        
        if old_preset.get("skin_color") != self._preset.get("skin_color"):
            old_skin = self.skin_color
            self.skin_color = self._preset["skin_color"]
            changes["changes"].append(f"skin: {old_skin} -> {self.skin_color}")
        
        # Эмитим событие
        self._emit_appearance_event("race_changed", **changes)
        
        return changes
    
    def randomize_appearance(self):
        """Случайная внешность в рамках текущей расы."""
        preset = self._preset
        
        # Случайные глаза из доступных
        if "eye_types" in preset:
            self.eyes.type = random.choice(preset["eye_types"])
            self.eyes.color = self._get_eye_color_for_race()
            self.eyes.glow = self.eyes.type in (EyeType.DEMONIC, EyeType.GLOWING, EyeType.SLIME)
        
        # Случайный рост
        if "height_range" in preset and hasattr(self, 'height'):
            self.height = random.uniform(*preset["height_range"])
        
        self._emit_appearance_event("appearance_randomized")
    
    def get_race_size(self, param: str, randomize: bool = True) -> float:
        """
        Получить размер из пресета расы.
        
        Args:
            param: Название параметра (например "penis_length")
            randomize: Если True - случайное значение из диапазона, 
                      если False - среднее
        """
        if param in self._preset:
            min_v, max_v = self._preset[param]
            if randomize:
                return random.uniform(min_v, max_v)
            return (min_v + max_v) / 2
        return 15.0  # default
    
    def get_race_option(self, param: str) -> Any:
        """Получить опцию из списка (например, breast_cup)."""
        if param in self._preset:
            options = self._preset[param]
            if isinstance(options, list):
                return random.choice(options)
            return options
        return None
    
    def perk_ears(self):
        """Навострить уши (если подвижные)."""
        self.ears.perk()
        self._emit_appearance_event("ears_perked")
    
    def flatten_ears(self):
        """Прижать уши."""
        self.ears.flatten()
        self._emit_appearance_event("ears_flattened")
    
    def on_appearance(self, event: str, callback: Callable):
        """Подписаться на события внешности."""
        self._appearance_listeners.setdefault(event, []).append(callback)
    
    def _emit_appearance_event(self, event: str, **data):
        """Вызвать обработчики событий внешности."""
        for cb in self._appearance_listeners.get(event, []):
            cb(self, **data)
    
    def tick(self, dt: float):
        """Обновление внешности (мигание, движение ушей)."""
        self.eyes.tick(dt)
        self.ears.tick(dt)
        
        # Случайные эмоции для подвижных ушей
        if self.ears.mobility > 0 and random.random() < 0.05 * dt:
            if random.random() < 0.3:
                self.perk_ears()
            elif random.random() < 0.6:
                self.flatten_ears()
    
    def get_appearance_description(self) -> str:
        """Текстовое описание внешности."""
        parts = [
            f"{self.race.name}",
            f"{self.eyes.color.name} {self.eyes.type.name} eyes" + 
                (" (glowing)" if self.eyes.glow else ""),
            f"{self.ears.type.name} ears ({self.ears.length:.1f}cm)",
            f"{self.skin_color.name} {self.skin_texture} skin"
        ]
        return ", ".join(parts)


# ============ ХЕЛПЕРЫ ============

def get_race_preset(race: Race) -> Dict[str, Any]:
    """Получить анатомический пресет для расы."""
    return RACE_ANATOMY_PRESETS.get(race, RACE_ANATOMY_PRESETS[Race.HUMAN])


def get_random_race_size(race: Race, param: str) -> float:
    """Получить случайный размер из диапазона пресета расы."""
    preset = get_race_preset(race)
    if param in preset:
        min_v, max_v = preset[param]
        return random.uniform(min_v, max_v)
    return 15.0

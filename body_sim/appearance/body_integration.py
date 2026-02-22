# body_sim/appearance/body_integration.py
"""
Пример интеграции Appearance с классом Body.
Добавьте это в body.py или используйте как миксин.
"""

import random
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable

from .appearance import Appearance
from .body_parts import (
    MouthAppearance, BellyAppearance, AnusAppearance,
    LipFullness, BellyShape, AnusAppearanceType
)
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


@dataclass
class ExtendedAppearanceMixin:
    """
    Расширенный миксин внешности.
    Включает: раса, глаза, уши, КОЖУ, РОТ, ЖИВОТ, АНУС.
    """
    race: Race = Race.HUMAN
    eyes: 'EyeAppearance' = field(default_factory=lambda: EyeAppearance())
    ears: 'EarAppearance' = field(default_factory=lambda: EarAppearance())
    skin_color: Color = Color.LIGHT_BEIGE
    skin_texture: str = "smooth"
    
    # НОВЫЕ АНАТОМИЧЕСКИЕ ЧАСТИ
    mouth_appearance: MouthAppearance = field(default_factory=MouthAppearance)
    belly_appearance: BellyAppearance = field(default_factory=BellyAppearance)
    anus_appearance: AnusAppearance = field(default_factory=AnusAppearance)
    
    # Внутренние
    _preset: Dict[str, Any] = field(default_factory=dict, repr=False)
    _appearance_listeners: Dict[str, List[Callable]] = field(default_factory=dict, repr=False)
    
    def __post_init__(self):
        """Инициализация пресета расы и настройка частей."""
        self._preset = self._get_preset()
        self._setup_race_appearance()
        self._setup_anatomical_parts()
    
    def _get_preset(self) -> Dict[str, Any]:
        """Получить текущий пресет расы."""
        return RACE_ANATOMY_PRESETS.get(self.race, RACE_ANATOMY_PRESETS[Race.HUMAN])
    
    def _setup_race_appearance(self):
        """Настроить базовую внешность по расе."""
        preset = self._preset
        
        # Уши (как раньше)
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
        
        # Глаза (как раньше)
        if "eye_types" in preset:
            eye_type = random.choice(preset["eye_types"])
            glow = eye_type in (EyeType.DEMONIC, EyeType.GLOWING)
            self.eyes = EyeAppearance(
                type=eye_type,
                color=self._get_eye_color_for_race(),
                glow=glow
            )
        
        # Кожа (как раньше)
        if "skin_color" in preset:
            self.skin_color = preset["skin_color"]
        if "skin_texture" in preset:
            self.skin_texture = preset["skin_texture"]
        
        # Рост (как раньше)
        if hasattr(self, 'height') and self.height == 0:
            if "height_range" in preset:
                self.height = random.uniform(*preset["height_range"])
    
    def _setup_anatomical_parts(self):
        """Настроить анатомические части по расе."""
        preset = self._preset
        
        # === РОТ ===
        if "lip_fullness" in preset:
            self.mouth_appearance.lip_fullness = preset["lip_fullness"]
        else:
            # По умолчанию по расе
            if self.race in (Race.ORC, Race.TROLL):
                self.mouth_appearance.lip_fullness = LipFullness.THIN
            elif self.race in (Race.ELF, Race.FELINE):
                self.mouth_appearance.lip_fullness = LipFullness.FULL
        
        if "lip_color" in preset:
            self.mouth_appearance.lip_color = preset["lip_color"]
        else:
            # Цвет губ по расе
            color_map = {
                Race.ORC: "purple",
                Race.TROLL: "green",
                Race.DEMON: "dark red",
                Race.VAMPIRE: "pale",
            }
            self.mouth_appearance.lip_color = color_map.get(self.race, "pink")
        
        # === ЖИВОТ ===
        if "belly_shape" in preset:
            self.belly_appearance.base_shape = preset["belly_shape"]
        else:
            # По умолчанию
            if self.race in (Race.ORC, Race.DWARF):
                self.belly_appearance.base_shape = BellyShape.SOFT
            elif self.race == Race.SLIME:
                self.belly_appearance.base_shape = BellyShape.ROUNDED
                self.belly_appearance.skin_texture = "translucent"
            else:
                self.belly_appearance.base_shape = BellyShape.SLIM
        
        # Пупок
        if self.race == Race.ELF:
            self.belly_appearance.belly_button = BellyButtonType.VERTICAL
        elif self.race in (Race.ORC, Race.TROLL):
            self.belly_appearance.belly_button = BellyButtonType.HORIZONTAL
        
        # === АНУС ===
        if "anus_type" in preset:
            self.anus_appearance.base_type = preset["anus_type"]
        else:
            if self.race in (Race.FELINE, Race.CANINE):
                self.anus_appearance.base_type = AnusAppearanceType.TIGHT
            elif self.race == Race.SLIME:
                self.anus_appearance.base_color = "translucent"
        
        # Цвет ануса по коже
        if self.race in (Race.ORC, Race.TROLL, Race.DEMON):
            self.anus_appearance.base_color = "dark"
        elif self.race == Race.ELF:
            self.anus_appearance.base_color = "pink"
    
    def update_appearance_from_anatomy(self, body):
        """
        Обновить внешность из текущего состояния анатомии.
        Вызывать в body.tick() или после изменений.
        """
        self.mouth_appearance.update_from_mouth(
            body.mouth_system.primary if hasattr(body, 'mouth_system') else None
        )
        self.belly_appearance.update_from_stomach(
            body.stomach_system.primary if hasattr(body, 'stomach_system') else None
        )
        if body.anuses:
            self.anus_appearance.update_from_anus(body.anuses[0])
    
    def get_full_description(self) -> Dict[str, str]:
        """Полное описание внешности всех частей."""
        return {
            "race": self.race.name,
            "eyes": f"{self.eyes.color.name} {self.eyes.type.name} eyes",
            "ears": f"{self.ears.type.name} ears ({self.ears.length:.1f}cm)",
            "skin": f"{self.skin_color.name} {self.skin_texture} skin",
            "mouth": self.mouth_appearance.get_description(),
            "belly": self.belly_appearance.get_description(),
            "anus": self.anus_appearance.get_description()
        }
    
    def render_full_body_appearance(self) -> str:
        """Отрисовка полной внешности для Rich."""
        from rich.table import Table
        from rich.panel import Panel
        
        table = Table(show_header=False, box=None)
        table.add_column("Part", style="cyan", width=10)
        table.add_column("Description", style="white")
        
        desc = self.get_full_description()
        for part, description in desc.items():
            table.add_row(part.capitalize(), description)
        
        return Panel(table, title="[bold]Body Appearance[/bold]", border_style="blue")
    
    # ============ Методы для изменения частей ============
    
    def modify_lips(self, fullness: Optional[LipFullness] = None, 
                   color: Optional[str] = None,
                   piercing: Optional[bool] = None):
        """Изменить внешность губ."""
        if fullness:
            self.mouth_appearance.lip_fullness = fullness
        if color:
            self.mouth_appearance.lip_color = color
        if piercing is not None:
            self.mouth_appearance.has_lip_piercing = piercing
    
    def modify_belly(self, shape: Optional[BellyShape] = None,
                    size: Optional[float] = None):
        """Изменить внешность живота."""
        if shape:
            self.belly_appearance.base_shape = shape
        if size is not None:
            self.belly_appearance.base_size = size
    
    def modify_anus(self, appearance_type: Optional[AnusAppearanceType] = None,
                   hair: Optional[bool] = None):
        """Изменить внешность ануса."""
        if appearance_type:
            self.anus_appearance.base_type = appearance_type
        if hair is not None:
            self.anus_appearance.has_hair = hair
    
    # ============ Оригинальные методы из AppearanceMixin ============
    
    def change_race(self, new_race: Race, regenerate: bool = True) -> Dict[str, Any]:
        """Сменить расу."""
        old_race = self.race
        self.race = new_race
        self._preset = self._get_preset()
        
        if regenerate:
            self._setup_race_appearance()
            self._setup_anatomical_parts()
        
        return {"old_race": old_race, "new_race": new_race}
    
    def _get_eye_color_for_race(self) -> Color:
        """Цвет глаз по расе."""
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
            Race.CYBORG: [Color.RED, Color.BLUE, Color.GREEN],
        }
        colors = color_map.get(self.race, [Color.BROWN])
        return random.choice(colors)
    
    def on_appearance(self, event: str, callback: Callable):
        """Подписаться на события."""
        self._appearance_listeners.setdefault(event, []).append(callback)
    
    def _emit_appearance_event(self, event: str, **data):
        """Вызвать обработчики."""
        for cb in self._appearance_listeners.get(event, []):
            cb(self, **data)
    
    def tick(self, dt: float):
        """Обновление (мигание, уши)."""
        if hasattr(self.eyes, 'tick'):
            self.eyes.tick(dt)
        if hasattr(self.ears, 'tick'):
            self.ears.tick(dt)
        
        # Случайные движения ушей
        if self.ears.mobility > 0 and random.random() < 0.05 * dt:
            if random.random() < 0.3:
                self.ears.perk() if hasattr(self.ears, 'perk') else None
            elif random.random() < 0.6:
                self.ears.flatten() if hasattr(self.ears, 'flatten') else None


# ============ Рендеринг для UI ============

def render_body_part_appearance(body, part: str) -> str:
    """
    Отрендерить внешность конкретной части.
    
    Args:
        part: 'mouth', 'belly', 'anus', 'all'
    """
    if not hasattr(body, 'mouth_appearance'):
        return "[red]Extended appearance not initialized[/red]"
    
    if part == 'mouth':
        app = body.mouth_appearance
        return f"""
[bold]Mouth Appearance[/bold]
  Lips: {app.get_description()}
  Current opening: {app.current_opening:.1f}cm
  State: {"Open" if app.is_open else "Closed"}
        """
    
    elif part == 'belly':
        app = body.belly_appearance
        return f"""
[bold]Belly Appearance[/bold]
  Shape: {app.get_description()}
  Current size: +{app.current_size:.1f}cm
  Circumference: {app.get_visual_circumference():.1f}cm
  Stretch marks: {len(app.stretch_marks)}
        """
    
    elif part == 'anus':
        app = body.anus_appearance
        return f"""
[bold]Anus Appearance[/bold]
  Type: {app.get_description()}
  Current diameter: {app.current_diameter:.1f}cm
  Prolapse: {app.prolapse_degree:.0%}
        """
    
    elif part == 'all':
        return body.render_full_body_appearance()
    
    return "[red]Unknown part[/red]"
    


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

# body_sim/appearance/renderer.py
"""
Rich-рендерер для системы внешности.
"""

from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box
from typing import Optional

from body_sim.appearance import (
    Appearance, Eye, Ear, Hair, Tail, Wings, Horn, Skin, FacialStructure,
    Race, EyeType, EyeColor, EarType, TailType, WingType, HornType,
    SkinTexture, HairType, HairStyle
)


class AppearanceRenderer:
    """Рендерер внешности для консольного вывода."""
    
    # Цвета для разных рас
    RACE_COLORS = {
        Race.HUMAN: "white",
        Race.ELF: "bright_green",
        Race.DARK_ELF: "bright_magenta",
        Race.ORC: "bright_red",
        Race.DWARF: "bright_yellow",
        Race.DEMON: "red",
        Race.ANGEL: "bright_yellow",
        Race.VAMPIRE: "bright_red",
        Race.WEREWOLF: "yellow",
        Race.CATGIRL: "yellow",
        Race.FOXGIRL: "bright_red",
        Race.WOLFGIRL: "bright_white",
        Race.BUNNYGIRL: "white",
        Race.DOGGIRL: "yellow",
        Race.BEARGIRL: "yellow",
        Race.COWGIRL: "white",
        Race.MOUSEGIRL: "white",
        Race.DRAGON: "bright_red",
        Race.LAMIA: "green",
        Race.CENTAUR: "yellow",
        Race.HARPY: "bright_cyan",
        Race.MERMAID: "bright_blue",
        Race.ARACHNE: "magenta",
        Race.SLIME: "bright_cyan",
        Race.GOLEM: "grey",
        Race.CYBORG: "cyan",
        Race.ALIEN: "green",
    }
    
    # Эмодзи для частей тела
    EMOJI = {
        "eye": "👁️",
        "ear": "👂",
        "hair": "💇",
        "horn": "🦄",
        "tail": "🦎",
        "wing": "🪶",
        "skin": "✋",
        "fangs": "🦷",
        "scar": "⚔️",
        "tattoo": "🎨",
    }
    
    # Эмодзи для рас
    RACE_EMOJIS = {
        Race.HUMAN: "👤",
        Race.ELF: "🧝",
        Race.DARK_ELF: "🧝‍♀️",
        Race.ORC: "👹",
        Race.DWARF: "🧔",
        Race.DEMON: "😈",
        Race.ANGEL: "👼",
        Race.VAMPIRE: "🧛",
        Race.WEREWOLF: "🐺",
        Race.CATGIRL: "🐱",
        Race.FOXGIRL: "🦊",
        Race.WOLFGIRL: "🐺",
        Race.BUNNYGIRL: "🐰",
        Race.DOGGIRL: "🐶",
        Race.BEARGIRL: "🐻",
        Race.COWGIRL: "🐮",
        Race.MOUSEGIRL: "🐭",
        Race.DRAGON: "🐲",
        Race.LAMIA: "🐍",
        Race.CENTAUR: "🐎",
        Race.HARPY: "🦅",
        Race.MERMAID: "🧜",
        Race.ARACHNE: "🕷️",
        Race.SLIME: "💧",
        Race.GOLEM: "🗿",
        Race.CYBORG: "🤖",
        Race.ALIEN: "👽",
    }
    
    def render(self, appearance: Appearance, compact: bool = False) -> Panel:
        """Создать панель с описанием внешности."""
        if compact:
            return self._render_compact(appearance)
        return self._render_full(appearance)
    
    def _render_full(self, app: Appearance) -> Panel:
        """Полный рендер с таблицами."""
        color = self.RACE_COLORS.get(app.race, "white")
        race_emoji = self.RACE_EMOJIS.get(app.race, "👤")
        
        # Главная таблица
        main_table = Table(show_header=False, box=box.SIMPLE)
        main_table.add_column("Feature", style="bold cyan")
        main_table.add_column("Value", style="white")
        
        # Основное
        main_table.add_row("Раса", f"[{color}]{race_emoji} {app.race.value}[/{color}]")
        main_table.add_row("Рост", f"{app.height:.0f} см")
        main_table.add_row("Телосложение", app.build)
        
        # Глаза
        eye_text = self._format_eyes(app)
        main_table.add_row(f"{self.EMOJI['eye']} Глаза", eye_text)
        
        # Уши
        ear_text = self._format_ears(app)
        main_table.add_row(f"{self.EMOJI['ear']} Уши", ear_text)
        
        # Волосы
        hair_text = self._format_hair(app)
        main_table.add_row(f"{self.EMOJI['hair']} Волосы", hair_text)
        
        # Особенности (рога, хвост, крылья)
        features = self._format_features(app)
        if features:
            main_table.add_row("Особенности", "\\n".join(features))
        
        # Кожа
        skin_text = self._format_skin(app)
        main_table.add_row(f"{self.EMOJI['skin']} Кожа/Покров", skin_text)
        
        # Лицо
        face_text = self._format_face(app)
        if face_text:
            main_table.add_row("Лицо", face_text)
        
        return Panel(
            main_table,
            title=f"[bold {color}]{race_emoji} {app.race.value.upper()}[/bold {color}]",
            border_style=color,
            box=box.ROUNDED
        )
    
    def _render_compact(self, app: Appearance) -> Panel:
        """Компактный рендер в одну строку."""
        color = self.RACE_COLORS.get(app.race, "white")
        race_emoji = self.RACE_EMOJIS.get(app.race, "👤")
        
        parts = [f"{race_emoji} {app.race.value}"]
        
        # Глаза
        if app.eyes:
            eye = app.eyes[0]
            glow = "✨" if eye.glow_intensity > 0.3 else ""
            parts.append(f"{self.EMOJI['eye']}{eye.color.value}{glow}")
        
        # Уши
        if app.ears and app.ears[0].ear_type != EarType.HUMAN:
            parts.append(f"{self.EMOJI['ear']}{app.ears[0].ear_type.value}")
        
        # Особенности
        if app.horns:
            parts.append(f"🦄x{len(app.horns)}")
        if app.tail.tail_type != TailType.NONE:
            parts.append(f"🦎")
        if app.wings.wing_type != WingType.NONE:
            parts.append(f"🪶")
        if app.face.has_fangs:
            parts.append("🦷")
        
        return Panel(
            " | ".join(parts),
            title=f"[{color}]{app.race.value}[/{color}]",
            border_style=color,
            box=box.SIMPLE,
            padding=(0, 1)
        )
    
    def _format_eyes(self, app: Appearance) -> str:
        """Форматирование описания глаз."""
        if not app.eyes:
            return "Нет"
        
        if len(app.eyes) == 1:
            e = app.eyes[0]
            glow = " ✨" if e.glow_intensity > 0.3 else ""
            magic = f" [{e.magic_effect}]" if e.is_magical and e.magic_effect else ""
            return f"{e.color.value}{glow} ({e.eye_type.value}){magic}"
        else:
            # Множественные глаза
            parts = []
            for i, e in enumerate(app.eyes):
                glow = "✨" if e.glow_intensity > 0.3 else ""
                parts.append(f"[{i}]{e.color.value}{glow}")
            return f"{len(app.eyes)} глаза: " + ", ".join(parts)
    
    def _format_ears(self, app: Appearance) -> str:
        """Форматирование ушей."""
        if not app.ears:
            return "Нет"
        
        types = []
        for ear in app.ears:
            mobility = "📳" if ear.mobility > 0.5 else ""
            types.append(f"{ear.ear_type.value}{mobility}")
        
        return ", ".join(set(types))
    
    def _format_hair(self, app: Appearance) -> str:
        """Форматирование волос."""
        h = app.hair
        parts = [f"{h.color.value}"]
        
        if h.hair_type != HairType.HAIR:
            parts.append(f"({h.hair_type.value})")
        
        parts.append(h.style.value)
        
        if h.length > 0:
            parts.append(f"{h.length:.0f}см")
        
        if h.glow_intensity > 0:
            parts.append("✨")
        
        return " ".join(parts)
    
    def _format_features(self, app: Appearance) -> list:
        """Форматирование особенностей (рога, хвост, крылья)."""
        features = []
        
        # Рога
        if app.horns:
            for h in app.horns:
                glow = "✨" if h.glows else ""
                features.append(f"🦄 {h.horn_type.value} {h.length:.0f}см{glow}")
        
        # Хвост
        if app.tail.tail_type != TailType.NONE:
            t = app.tail
            prehensile = "🤏" if t.prehensile else ""
            features.append(f"🦎 {t.tail_type.value} {t.length:.0f}см{prehensile}")
        
        # Крылья
        if app.wings.wing_type != WingType.NONE:
            w = app.wings
            status = "🫥" if w.is_hidden else "👁️"
            fly = "✈️" if w.can_fly else "❌"
            damage = "💔" if w.condition < 0.5 else ""
            features.append(f"🪶 {w.wing_type.value} {w.span:.0f}см {status}{fly}{damage}")
        
        return features
    
    def _format_skin(self, app: Appearance) -> str:
        """Форматирование кожи."""
        s = app.skin
        parts = [f"{s.texture.value}"]
        
        if s.transparency > 0:
            parts.append(f"прозрачность {s.transparency:.0%}")
        
        if s.glossiness > 0:
            parts.append(f"блеск {s.glossiness:.0%}")
        
        if s.wetness > 0:
            parts.append(f"влага {s.wetness:.0%}")
        
        if s.markings:
            parts.append(f"метки: {', '.join(s.markings)}")
        
        if s.scars:
            parts.append(f"шрамы: {len(s.scars)}")
        
        return " | ".join(parts)
    
    def _format_face(self, app: Appearance) -> Optional[str]:
        """Форматирование лица."""
        f = app.face
        parts = []
        
        if f.has_fangs:
            parts.append(f"🦷 Клыки {f.fang_size:.1f}см")
        
        if f.has_whiskers:
            parts.append(f"👃 Усы {f.whisker_length:.1f}см")
        
        if f.snout_length > 0:
            parts.append(f"Морда ({f.snout_length:.1f})")
        
        return " | ".join(parts) if parts else None
    
    def render_comparison(self, app1: Appearance, app2: Appearance) -> Table:
        """Сравнение двух внешностей."""
        table = Table(title="Сравнение внешности", box=box.DOUBLE_EDGE)
        table.add_column("Характеристика", style="bold")
        
        color1 = self.RACE_COLORS.get(app1.race, "white")
        color2 = self.RACE_COLORS.get(app2.race, "white")
        
        table.add_column(f"[{color1}]{app1.race.value}[/{color1}]", style=color1)
        table.add_column(f"[{color2}]{app2.race.value}[/{color2}]", style=color2)
        
        table.add_row("Рост", f"{app1.height:.0f}см", f"{app2.height:.0f}см")
        table.add_row("Телосложение", app1.build, app2.build)
        table.add_row("Глаза", app1.eyes[0].color.value if app1.eyes else "-", 
                     app2.eyes[0].color.value if app2.eyes else "-")
        table.add_row("Уши", app1.ears[0].ear_type.value if app1.ears else "-",
                     app2.ears[0].ear_type.value if app2.ears else "-")
        
        # Хвост
        tail1 = app1.tail.tail_type.value if app1.tail.tail_type != TailType.NONE else "Нет"
        tail2 = app2.tail.tail_type.value if app2.tail.tail_type != TailType.NONE else "Нет"
        table.add_row("Хвост", tail1, tail2)
        
        # Крылья
        wing1 = app1.wings.wing_type.value if app1.wings.wing_type != WingType.NONE else "Нет"
        wing2 = app2.wings.wing_type.value if app2.wings.wing_type != WingType.NONE else "Нет"
        table.add_row("Крылья", wing1, wing2)
        
        return table


# ============ COMPACT RENDERERS для интеграции с rich_render.py ============

def render_appearance_compact(body) -> Optional[Panel]:
    """Компактный рендер внешности для rich_render.py."""
    try:
        from body_sim.appearance import TailType, WingType
    except ImportError:
        return None
    
    if not hasattr(body, 'appearance') or not body.appearance:
        return None
    
    app = body.appearance
    renderer = AppearanceRenderer()
    color = renderer.RACE_COLORS.get(app.race, "white")
    race_emoji = renderer.RACE_EMOJIS.get(app.race, "👤")
    
    # Основная информация
    lines = [
        f"{race_emoji} {app.race.value.upper()} | {app.height:.0f}cm | {app.build}"
    ]
    
    # Глаза
    if app.eyes:
        eye = app.eyes[0]
        eye_emoji = "👁️"
        if eye.eye_type.value == "slit":
            eye_emoji = "🐱"
        elif eye.eye_type.value == "glowing":
            eye_emoji = "✨"
        elif len(app.eyes) > 2:
            eye_emoji = "👁️"
        
        glow = "✨" if eye.glow_intensity > 0.3 else ""
        lines.append(f"{eye_emoji} Eyes: {eye.color.value}{glow}")
    
    # Уши
    if app.ears:
        ear = app.ears[0]
        ear_emojis = {
            "human": "👂",
            "cat": "🐱",
            "fox": "🦊",
            "wolf": "🐺",
            "rabbit": "🐰",
            "pointed": "🧝",
            "dragon": "🐲",
        }
        ear_emoji = ear_emojis.get(ear.ear_type.value, "👂")
        if ear.mobility > 0.5:
            ear_emoji += "↔️"
        lines.append(f"{ear_emoji} Ears: {ear.ear_type.value}")
    
    # Волосы
    if app.hair:
        hair_emoji = "💇"
        if app.hair.hair_type.value == "fur":
            hair_emoji = "🦁"
        elif app.hair.hair_type.value == "slime":
            hair_emoji = "💧"
        lines.append(f"{hair_emoji} Hair: {app.hair.color.value}")
    
    # Особенности
    features = []
    if app.horns:
        features.append(f"🦄x{len(app.horns)}")
    if app.tail.tail_type != TailType.NONE:
        features.append(f"🦎")
    if app.wings.wing_type != WingType.NONE:
        features.append(f"🪶")
    if app.face.has_fangs:
        features.append("🦷")
    
    if features:
        lines.append(" | ".join(features))
    
    return Panel(
        "\\n".join(lines),
        title="[bold cyan]Appearance[/bold cyan]",
        border_style="cyan",
        box=box.SIMPLE,
        padding=(0, 1)
    )


def render_appearance_detailed(body) -> Optional[Panel]:
    """Детальный рендер внешности через AppearanceRenderer."""
    if not hasattr(body, 'appearance') or not body.appearance:
        return None
    
    try:
        renderer = AppearanceRenderer()
        return renderer.render(body.appearance, compact=False)
    except:
        return render_appearance_compact(body)

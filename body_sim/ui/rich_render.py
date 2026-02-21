# body_sim/ui/rich_render.py
"""
Компактный Rich-рендеринг для маленьких консолей.
Использует breast_render для рендеринга груди.
"""

from typing import List, Optional, TYPE_CHECKING, Dict, Any
from dataclasses import dataclass

from rich.console import Console, Group, RenderableType
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.layout import Layout
from rich.tree import Tree
from rich import box
from rich.align import Align
from rich.rule import Rule

if TYPE_CHECKING:
    from body_sim.body.body import Body
    from body_sim.anatomy.breast import Breast
    from body_sim.systems.grid import BreastGrid
    from body_sim.anatomy.genitals import Penis, Vagina, Scrotum

from body_sim.core.enums import Sex, FluidType, BreastState, LactationState, BodyType
from body_sim.core.fluids import FLUID_DEFS

# Импорт нового рендерера груди
from body_sim.ui.breast_render import (
    BreastRenderer,
    render_breast_compact
)
from body_sim.ui.body_list_render import render_body_list

console = Console()

# Ленивый импорт uterus renderer
def _get_uterus_renderer():
    """Ленивый импорт uterus renderer."""
    try:
        from .uterus_render import UterusRenderer
        return UterusRenderer()
    except ImportError as e:
        return None


try:
    from body_sim.appearance import Appearance, Race, EyeType, EarType, TailType, WingType
    from body_sim.appearance.renderer import AppearanceRenderer
    APPEARANCE_AVAILABLE = True
except ImportError:
    APPEARANCE_AVAILABLE = False

# ======================
# APPEARANCE RENDERING
# ======================

RACE_EMOJIS = {
    "human": "👤",
    "elf": "🧝",
    "dark_elf": "🧝‍♀️",
    "orc": "👹",
    "dwarf": "🧔",
    "demon": "😈",
    "angel": "👼",
    "vampire": "🧛",
    "catgirl": "🐱",
    "foxgirl": "🦊",
    "wolfgirl": "🐺",
    "bunnygirl": "🐰",
    "dragon": "🐲",
    "slime": "💧",
    "cyborg": "🤖",
}

def render_appearance_compact(body) -> Optional[Panel]:
    """Компактный рендер внешности."""
    if not APPEARANCE_AVAILABLE or not hasattr(body, 'appearance') or not body.appearance:
        return None
    
    app = body.appearance
    race_emoji = RACE_EMOJIS.get(app.race.value, "👤")
    
    # Основная информация
    lines = [
        f"{race_emoji} {app.race.value.upper()} | {app.height:.0f}cm | {app.build}"
    ]
    
    # Глаза
    if app.eyes:
        eye = app.eyes[0]  # Первый глаз
        eye_emoji = "👁️"
        if eye.eye_type == EyeType.SLIT:
            eye_emoji = "🐱"
        elif eye.eye_type == EyeType.GLOWING:
            eye_emoji = "✨"
        elif len(app.eyes) > 2:
            eye_emoji = "👁️"
        
        glow = "✨" if eye.glow_intensity > 0.3 else ""
        lines.append(f"{eye_emoji} Eyes: {eye.color.value}{glow} ({eye.eye_type.value})")
    
    # Уши
    if app.ears:
        ear = app.ears[0]
        ear_emojis = {
            EarType.HUMAN: "👂",
            EarType.CAT: "🐱",
            EarType.FOX: "🦊",
            EarType.WOLF: "🐺",
            EarType.RABBIT: "🐰",
            EarType.POINTED: "🧝",
            EarType.DRAGON: "🐲",
        }
        ear_emoji = ear_emojis.get(ear.ear_type, "👂")
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
        lines.append(f"{hair_emoji} Hair: {app.hair.color.value} {app.hair.style.value}")
    
    # Особенности
    features = []
    if app.horns:
        features.append(f"🦄 Рога x{len(app.horns)}")
    if app.tail.tail_type != TailType.NONE:
        features.append(f"🦎 Хвост ({app.tail.tail_type.value})")
    if app.wings.wing_type != WingType.NONE:
        features.append(f"🪶 Крылья ({app.wings.wing_type.value})")
    if app.face.has_fangs:
        features.append("🦷 Клыки")
    
    if features:
        lines.append(" | ".join(features))
    
    # Кожа/покров
    skin_emoji = "✋"
    if app.skin.texture.value == "furry":
        skin_emoji = "🦁"
    elif app.skin.texture.value == "scaly":
        skin_emoji = "🐲"
    elif app.skin.texture.value == "slimy":
        skin_emoji = "💧"
    lines.append(f"{skin_emoji} Skin: {app.skin.texture.value}")
    
    return Panel(
        "\\n".join(lines),
        title="[bold cyan]Appearance[/bold cyan]",
        border_style="cyan",
        box=box.SIMPLE,
        padding=(0, 1)
    )


def render_appearance_detailed(body) -> Optional[Panel]:
    """Детальный рендер внешности через AppearanceRenderer."""
    if not APPEARANCE_AVAILABLE or not hasattr(body, 'appearance') or not body.appearance:
        return None
    
    if APPEARANCE_AVAILABLE:
        try:
            renderer = AppearanceRenderer()
            return renderer.render(body.appearance)
        except:
            pass
    
    return render_appearance_compact(body)


# ======================
# COLORS & STYLES
# ======================

SEX_COLORS = {
    Sex.MALE: "bright_blue",
    Sex.FEMALE: "bright_magenta", 
    Sex.FUTANARI: "bright_magenta",
    Sex.NONE: "gray"
}

SEX_EMOJIS = {
    Sex.MALE: "♂",
    Sex.FEMALE: "♀",
    Sex.FUTANARI: "⚧",
    Sex.NONE: "○"
}

SEX_NAMES = {
    Sex.MALE: "M",
    Sex.FEMALE: "F",
    Sex.FUTANARI: "Fu",
    Sex.NONE: "-"
}

STATE_STYLES = {
    BreastState.EMPTY: "white",
    BreastState.NORMAL: "green",
    BreastState.TENSE: "yellow",
    BreastState.OVERPRESSURED: "magenta",
    BreastState.LEAKING: "red",
}

STATE_EMOJIS = {
    BreastState.EMPTY: "○",
    BreastState.NORMAL: "●",
    BreastState.TENSE: "◐",
    BreastState.OVERPRESSURED: "◉",
    BreastState.LEAKING: "💧",
}

FLUID_COLORS = {
    FluidType.MILK: "white",
    FluidType.CUM: "cyan",
    FluidType.WATER: "blue",
    FluidType.HONEY: "yellow",
    FluidType.OIL: "magenta",
    FluidType.CUSTOM: "green",
}

FLUID_EMOJIS = {
    FluidType.MILK: "M",
    FluidType.CUM: "C",
    FluidType.WATER: "W",
    FluidType.HONEY: "H",
    FluidType.OIL: "O",
    FluidType.CUSTOM: "?",
}

BODY_TYPE_EMOJIS = {
    BodyType.PETITE: "p",
    BodyType.SLENDER: "s",
    BodyType.AVERAGE: "a",
    BodyType.CURVY: "c",
    BodyType.MUSCULAR: "m",
    BodyType.HEAVY: "h",
    BodyType.AMAZON: "A",
}


# ======================
# COMPACT UTILS
# ======================

def make_compact_bar(value: float, max_value: float, width: int = 8, color: str = "blue") -> str:
    """Компактный прогресс-бар."""
    if max_value <= 0:
        return "░" * width
    ratio = min(max(value / max_value, 0.0), 1.0)
    filled = int(ratio * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{color}]{bar}[/{color}]"


def make_compact_gradient_bar(value: float, max_value: float, width: int = 8) -> str:
    """Компактный градиентный бар."""
    if max_value <= 0:
        return "░" * width
    ratio = min(max(value / max_value, 0.0), 1.0)
    filled = int(ratio * width)
    
    color = "green" if ratio < 0.4 else "yellow" if ratio < 0.7 else "red"
    return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/{color}]"


# ======================
# COMPACT BREAST RENDER (адаптировано под breast_render)
# ======================

# Глобальный экземпляр рендерера для переиспользования
_breast_renderer: Optional[BreastRenderer] = None

def _get_breast_renderer() -> BreastRenderer:
    """Получить или создать экземпляр BreastRenderer."""
    global _breast_renderer
    if _breast_renderer is None:
        _breast_renderer = BreastRenderer()
    return _breast_renderer


def render_breast_compact(breast, label: str = "") -> Panel:
    """
    Компактный рендер груди (обёртка над breast_render).
    Сохраняет совместимость со старым интерфейсом.
    """
    # Используем новый рендерер, но с компактными настройками
    renderer = _get_breast_renderer()
    return renderer.render_breast_compact(breast, label)


def render_breast_detail(breast, label: str = "") -> Panel:
    """
    Детальный но компактный рендер груди (обёртка).
    """
    renderer = _get_breast_renderer()
    return renderer.render_breast_detailed(breast, label)


# ======================
# COMPACT BREAST GRID (адаптировано)
# ======================

def render_breasts(grid, compact: bool = False) -> RenderableType:
    """
    Компактное отображение сетки грудей.
    Использует новый BreastRenderer.
    """
    renderer = _get_breast_renderer()
    
    all_breasts = grid.all()
    total_breasts = len(all_breasts)
    
    total_filled = sum((b.filled or 0) for b in all_breasts)
    total_capacity = sum((b._max_volume or 0) for b in all_breasts)
    leaking_count = sum(1 for b in all_breasts if getattr(b, '_state', None) == BreastState.LEAKING)
    
    # Компактный заголовок
    fill_pct = (total_filled / total_capacity * 100) if total_capacity > 0 else 0
    leak_str = f" [red]L:{leaking_count}[/red]" if leaking_count > 0 else ""
    header_text = f"🍼 B:{total_breasts} | 💧{total_filled:.0f}/{total_capacity:.0f}ml ({fill_pct:.0f}%){leak_str}"
    
    # Используем новый рендер сетки
    grid_panel = renderer.render_grid(grid, title=header_text)
    
    # Адаптируем стиль под компактный вид
    if compact and len(grid.rows) == 1 and len(grid.rows[0]) <= 2:
        # Для 1-2 грудей используем компактные панели
        panels = []
        for c_idx, breast in enumerate(grid.rows[0]):
            label = grid.get_label(0, c_idx)
            panels.append(renderer.render_breast_compact(breast, label))
        
        return Panel(
            Columns(panels, equal=True, expand=True),
            title=header_text,
            box=box.SIMPLE,
            border_style="bright_magenta",
            padding=(0, 1)
        )
    
    return grid_panel


# ======================
# COMPACT BODY HEADER
# ======================

def render_body_header(body) -> Panel:
    """Компактный заголовок."""
    sex_color = SEX_COLORS.get(body.sex, "white")
    sex_emoji = SEX_EMOJIS.get(body.sex, "?")
    sex_name = SEX_NAMES.get(body.sex, "?")
    type_emoji = BODY_TYPE_EMOJIS.get(body.body_type, "?")
    
    # Однострочная сводка
    stats = body.stats
    
    header_line = (
        f"[{sex_color}]{sex_emoji} {body.name}[/{sex_color}] "
        f"({type_emoji}|{sex_name}) "
        f"{stats.height:.0f}cm/{stats.weight:.0f}kg"
    )
    
    # Статсы в одну строку
    stats_line = (
        f"A:{make_compact_gradient_bar(stats.arousal, 1.0)} "
        f"P:{make_compact_gradient_bar(stats.pleasure, 1.0)} "
        f"💔{make_compact_bar(stats.pain, 1.0, color='red')} "
        f"😴{make_compact_bar(stats.fatigue, 1.0, color='yellow')}"
    )
    
    return Panel(
        f"{header_line}\n{stats_line}",
        title="[bold]Character[/bold]",
        border_style=sex_color,
        box=box.SIMPLE,
        padding=(0, 1)
    )




# ======================
# COMPACT GENITALS
# ======================
def render_penis_compact(penis, index: int = 0) -> str:
    """Компактный рендер пениса с индикатором давления."""
    status = "🔥" if penis.is_erect else "🍆"
    
    mult = penis._get_ejaculate_multiplier()
    mult_symbol = "↑" if mult > 1.0 else "↓" if mult < 1.0 else "→"
    urethra = penis.current_urethra_diameter
    
    if penis.has_scrotum():
        available = penis.get_available_volume()
        max_pulse = penis.calculate_max_ejaculate_volume(force=1.0)
        
        # НОВОЕ: индикатор давления
        pressure_tier = penis.scrotum.pressure_tier
        pressure_emoji = {
            "low": "💧",
            "normal": "",
            "high": "⚠",
            "critical": "🔴",
            "rupture_risk": "💥"
        }.get(pressure_tier, "")
        
        return (f"{status}#{index}:{penis.current_length:.1f}cm | "
                f"U:{urethra:.1f}mm | "
                f"C:{available:.1f}ml{pressure_emoji} | "
                f"Max:{max_pulse:.1f}ml/pulse")
    else:
        return f"{status}#{index}:{penis.current_length:.1f}cm | U:{urethra:.1f}mm | [red]No scrotum[/red]"

def render_vagina_compact(vagina, index: int = 0) -> str:
    """Компактный рендер влагалища (строка)."""
    status = "💧" if vagina.is_aroused else "🌸"
    return f"{status}#{index}:{vagina.current_depth:.1f}cm L{vagina.lubrication:.0%}"

def render_scrotum_compact(scrotum, index: int = 0) -> str:
    """Компактный рендер мошонки (строка)."""
    testicles = len(scrotum.testicles)
    fullness = scrotum.fullness
    
    # Детализация по сперме
    cum_amount = scrotum.total_stored_fluids.get(FluidType.CUM, 0)
    capacity = scrotum.total_storage_capacity
    
    return f"🥚#{index}:{testicles}t {cum_amount:.0f}/{capacity:.0f}ml ({fullness:.0%})"

def render_genitals(body) -> Panel:
    from .genitals_render import render_genitals
    return render_genitals(body)

# ======================
# COMPACT UTERUS
# ======================

def render_uterus_section(body) -> Optional[Panel]:
    """Компактный рендер матки."""
    if not hasattr(body, 'uterus_system') or not body.uterus_system:
        return None
    
    try:
        renderer = _get_uterus_renderer()
        if renderer is None:
            return None
        
        result = renderer.render_full_system(body.uterus_system, title="Uterus")
        if isinstance(result, Panel):
            return result
    except:
        pass
    return None


# ======================
# COMPACT FULL BODY
# ======================

def render_full_body(body, show_breasts: bool = True, show_genitals: bool = True, 
                     show_uterus: bool = True, compact: bool = False, show_appearance: bool = True) -> RenderableType:
    """Компактное полное отображение тела."""
    has_breasts = show_breasts and body.has_breasts
    has_genitals = show_genitals and (body.has_penis or body.has_vagina)
    has_uterus = show_uterus and hasattr(body, 'uterus_system') and body.uterus_system
    
    sections = []
    if show_appearance:
        appearance = render_appearance_compact(body)
        if appearance:
            sections.append(appearance)

    sections.append(render_body_header(body))
    
    if has_breasts:
        sections.append(render_breasts(body.breast_grid, compact=compact))
    
    if has_genitals:
        sections.append(render_genitals(body))
    
    if has_uterus:
        uterus = render_uterus_section(body)
        if uterus:
            sections.append(uterus)

    
    return Panel(
        Group(*sections),
        title=f"[bold]{body.name}[/bold]",
        box=box.SIMPLE,
        border_style=SEX_COLORS.get(body.sex, "white"),
        padding=(0, 1)
    )


def render_character_tree(body) -> Tree:
    """Компактное древовидное представление."""
    sex_color = SEX_COLORS.get(body.sex, "white")
    sex_emoji = SEX_EMOJIS.get(body.sex, "?")
    
    root = Tree(f"{sex_emoji} [{sex_color}]{body.name}[/]")
    
    # Статсы одной строкой
    stats = body.stats
    root.add(f"A:{stats.arousal:.0%} P:{stats.pleasure:.2f} 💔{stats.pain:.2f} 😴{stats.fatigue:.2f}")
    
    # Грудь через новый рендерер
    if body.has_breasts:
        renderer = _get_breast_renderer()
        breasts = root.add("🍼")
        
        for r_idx, row in enumerate(body.breast_grid.rows):
            for c_idx, breast in enumerate(row):
                label = body.breast_grid.get_label(r_idx, c_idx)
                # Используем стили нового рендерера
                state = breast.state
                emoji, color, state_desc = renderer._get_state_style(state)
                filled = getattr(breast, 'filled', 0) or 0
                volume = getattr(breast, 'volume', 0) or 0
                cup = breast.cup.name
                breasts.add(f"[{color}]{emoji}[/]{label}:{cup} {filled:.0f}/{volume:.0f}ml")
    
    if body.has_penis or body.has_vagina:
        gen = root.add("🔞")
        if body.has_penis:
            for i, p in enumerate(body.penises):
                gen.add(f"{'🔥' if p.is_erect else '🍆'}#{i}:{p.current_length:.1f}cm")
        if body.has_vagina:
            for i, v in enumerate(body.vaginas):
                gen.add(f"{'💧' if v.is_aroused else '🌸'}#{i}:{v.current_depth:.1f}cm")
    
    return root


def print_body(body, console: Optional[Console] = None):
    """Быстрый вывод тела."""
    con = console or Console()
    con.print(render_full_body(body))


def print_bodies(bodies: List, console: Optional[Console] = None):
    """Вывести список тел."""
    con = console or Console()
    con.print(render_body_list(bodies))


def print_character_sheet(body, console: Optional[Console] = None):
    """Печать листа персонажа."""
    con = console or Console()
    con.print(render_full_body(body))

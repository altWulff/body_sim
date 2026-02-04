# body_sim/ui/rich_render.py
"""
Компактный Rich-рендеринг для маленьких консолей.
"""

from typing import List, Optional, TYPE_CHECKING, Dict, Any, Tuple
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


console = Console()

# Ленивый импорт uterus renderer
def _get_uterus_renderer():
    """Ленивый импорт uterus renderer."""
    try:
        from .uterus_render import UterusRenderer
        return UterusRenderer()
    except ImportError as e:
        return None


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
# COMPACT BREAST RENDER
# ======================

def render_breast_compact(breast, label: str = "") -> Panel:
    """Компактный рендер груди (одна строка)."""
    state = breast._state
    style = STATE_STYLES.get(state, "white")
    emoji = STATE_EMOJIS.get(state, "○")
    
    # Однострочная сводка
    dyn_cup = breast.dynamic_cup.name
    base_cup = breast.cup.name
    cup_str = f"{base_cup}→{dyn_cup}" if dyn_cup != base_cup else base_cup
    
    pressure = breast.pressure(FLUID_DEFS)
    p_color = "green" if pressure < 1.0 else "yellow" if pressure < 2.0 else "red"
    
    fill_pct = 0
    if breast.volume and breast.volume > 0:
        fill_pct = (breast.filled / breast.volume) * 100
    
    lact = "L" if breast.lactation.state != LactationState.OFF else " "
    stretch = f"S{breast.inflation.stretch_ratio:.1f}" if breast.inflation.stretch_ratio > 1.1 else "  "
    
    content = (
        f"{emoji} [bold]{label}[/bold] {cup_str} | "
        f"[{p_color}]P{pressure:.1f}[/{p_color}] | "
        f"💧{fill_pct:.0f}% | "
        f"sag:{breast.sag:.2f} {lact}{stretch}"
    )
    
    # Предупреждения компактно
    warnings = []
    if state == BreastState.LEAKING:
        warnings.append("[red]LEAK[/red]")
    if pressure > 2.5:
        warnings.append("[red]HIGH P[/red]")
    
    if warnings:
        content += " | " + " ".join(warnings)
    
    return Panel(
        content,
        title=f"{label}",
        border_style=style,
        box=box.SIMPLE,
        padding=(0, 1)
    )


def render_breast_detail(breast, label: str = "") -> Panel:
    """Детальный но компактный рендер груди."""
    state = breast._state
    style = STATE_STYLES.get(state, "white")
    emoji = STATE_EMOJIS.get(state, "○")
    
    title = f"{emoji} {label}: [{style}]{state.name[:4]}[/{style}]"
    
    # Компактная таблица (2 колонки)
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="cyan", width=8)
    table.add_column("Val", style="white", width=12)
    table.add_column("Key", style="cyan", width=8)
    table.add_column("Val", style="white", width=12)
    
    # Размер
    dyn_cup = breast.dynamic_cup.name
    base_cup = breast.cup.name
    cup_str = f"{base_cup}→{dyn_cup}" if dyn_cup != base_cup else base_cup
    
    # Давление
    pressure = breast.pressure(FLUID_DEFS)
    p_bar = make_compact_bar(pressure, 3.0, width=6, color="green" if pressure < 1.0 else "yellow" if pressure < 2.0 else "red")
    
    # Заполнение
    fill_pct = 0
    if breast.volume and breast.volume > 0:
        fill_pct = (breast.filled / breast.volume) * 100
    
    table.add_row("Cup:", cup_str, "Press:", f"{p_bar} {pressure:.1f}")
    table.add_row("Fill:", f"{fill_pct:.0f}% ({breast.filled:.0f}ml)", "Sag:", f"{breast.sag:.2f}")
    table.add_row("Elast:", f"{breast.elasticity:.2f}", "Avail:", f"{breast.available_volume:.0f}ml")
    
    # Лактация
    lact = breast.lactation
    if lact.state != LactationState.OFF:
        table.add_row("Lact:", f"{lact.state.name[:4]} {lact.base_rate_per_100ml:.1f}", "Horm:", f"{lact.hormone_level:.1f}")
    
    # Соски (компактно)
    nip_info = []
    for idx, nip in enumerate(breast.areola.nipples[:2]):  # Макс 2 соска
        open_str = "O" if nip.is_open else "C"
        nip_info.append(f"{open_str}{idx}:{nip.gape_diameter:.1f}cm")
    if nip_info:
        table.add_row("Nips:", " | ".join(nip_info), "", "")
    
    # Объекты
    if breast.insertion_manager.inserted_objects:
        obj_count = len(breast.insertion_manager.inserted_objects)
        obj_vol = sum(obj.effective_volume for obj in breast.insertion_manager.inserted_objects)
        table.add_row(f"Objs({obj_count}):", f"{obj_vol:.0f}ml", "", "")
    
    # Жидкости (компактно)
    if breast.mixture.components:
        fluid_parts = []
        total = breast.mixture.total()
        for ft, vol in list(breast.mixture.components.items())[:3]:  # Макс 3 типа
            emoji = FLUID_EMOJIS.get(ft, "?")
            fluid_parts.append(f"{emoji}{vol:.0f}")
        table.add_row("Fluids:", " | ".join(fluid_parts) + f" ={total:.0f}ml", "", "")
    
    return Panel(
        table,
        title=title,
        border_style=style,
        box=box.ROUNDED,
        padding=(0, 1)
    )


# ======================
# COMPACT BREAST GRID
# ======================

def render_breasts(grid, compact: bool = True) -> RenderableType:
    """Компактное отображение сетки грудей."""
    all_breasts = grid.all()
    total_breasts = len(all_breasts)
    
    total_filled = sum((b.filled or 0) for b in all_breasts)
    total_capacity = sum((b._max_volume or 0) for b in all_breasts)
    leaking_count = sum(1 for b in all_breasts if getattr(b, '_state', None) == BreastState.LEAKING)
    
    # Компактный заголовок
    fill_pct = (total_filled / total_capacity * 100) if total_capacity > 0 else 0
    leak_str = f" [red]L:{leaking_count}[/red]" if leaking_count > 0 else ""
    header_text = f"🍼 B:{total_breasts} | 💧{total_filled:.0f}/{total_capacity:.0f}ml ({fill_pct:.0f}%){leak_str}"
    
    if compact and len(grid.rows) == 1 and len(grid.rows[0]) <= 2:
        # Для 1-2 грудей - горизонтальное расположение
        panels = []
        for c_idx, breast in enumerate(grid.rows[0]):
            label = grid.get_label(0, c_idx)
            panels.append(render_breast_compact(breast, label))
        
        return Panel(
            Columns(panels, equal=True, expand=True),
            title=header_text,
            box=box.SIMPLE,
            border_style="bright_magenta",
            padding=(0, 1)
        )
    
    # Для многих грудей - таблица
    all_rows = []
    for r_idx, row in enumerate(grid.rows):
        panels = []
        for c_idx, breast in enumerate(row):
            label = grid.get_label(r_idx, c_idx)
            if compact:
                panels.append(render_breast_compact(breast, label))
            else:
                panels.append(render_breast_detail(breast, label))
        
        all_rows.append(Columns(panels, equal=True, expand=True))
    
    return Panel(
        Group(*all_rows),
        title=header_text,
        box=box.SIMPLE,
        border_style="bright_magenta",
        padding=(0, 1)
    )


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
        f"{header_line}\\n{stats_line}",
        title="[bold]Character[/bold]",
        border_style=sex_color,
        box=box.SIMPLE,
        padding=(0, 1)
    )


def render_body_list(bodies: List, active_idx: int = 0) -> Panel:
    """Компактный список тел."""
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("#", width=3)
    table.add_column("Sex", width=3)
    table.add_column("Name", width=12)
    table.add_column("Type", width=5)
    table.add_column("Gen", width=10)
    table.add_column("Arousal", width=10)
    
    for i, body in enumerate(bodies):
        marker = ">" if i == active_idx else " "
        sex_color = SEX_COLORS.get(body.sex, "white")
        sex_emoji = SEX_EMOJIS.get(body.sex, "?")
        type_emoji = BODY_TYPE_EMOJIS.get(body.body_type, "?")
        
        genitals = []
        if body.has_penis:
            erect = sum(1 for p in body.penises if getattr(p, 'is_erect', False))
            genitals.append(f"P{len(body.penises)}{'🔥' if erect else ''}")
        if body.has_vagina:
            aroused = sum(1 for v in body.vaginas if getattr(v, 'is_aroused', False))
            genitals.append(f"V{len(body.vaginas)}{'💧' if aroused else ''}")
        if body.has_scrotum:
            testicles = sum(len(s.testicles) for s in body.scrotums)
            genitals.append(f"T{testicles}")
        
        arousal_bar = make_compact_gradient_bar(body.stats.arousal, 1.0, width=6)
        
        table.add_row(
            f"{marker}{i}",
            f"[{sex_color}]{sex_emoji}[/{sex_color}]",
            f"[{sex_color}]{body.name[:10]}[/{sex_color}]",
            type_emoji,
            ",".join(genitals) if genitals else "-",
            arousal_bar
        )
    
    return Panel(table, title="[bold]Bodies[/bold]", border_style="blue", box=box.SIMPLE)


# ======================
# COMPACT GENITALS
# ======================

def render_penis_compact(penis, index: int = 0) -> str:
    """Компактный рендер пениса (строка)."""
    status = "🔥" if penis.is_erect else "🍆"
    cum_pct = (penis.current_cum_volume / penis.cum_reservoir * 100) if penis.cum_reservoir > 0 else 0
    return f"{status}#{index}:{penis.current_length:.1f}cm C{cum_pct:.0f}%"


def render_vagina_compact(vagina, index: int = 0) -> str:
    """Компактный рендер влагалища (строка)."""
    status = "💧" if vagina.is_aroused else "🌸"
    return f"{status}#{index}:{vagina.current_depth:.1f}cm L{vagina.lubrication:.0%}"


def render_scrotum_compact(scrotum, index: int = 0) -> str:
    """Компактный рендер мошонки (строка)."""
    testicles = len(scrotum.testicles)
    fullness = scrotum.fullness
    return f"🥚#{index}:{testicles}t F{fullness:.0%}"


# def render_genitals(body) -> Panel:
#     """Компактное отображение гениталий."""
#     lines = []
    
#     if body.has_penis:
#         penis_line = " | ".join(render_penis_compact(p, i) for i, p in enumerate(body.penises))
#         lines.append(f"[bold]P:[/bold] {penis_line}")
    
#     if body.has_vagina:
#         vagina_line = " | ".join(render_vagina_compact(v, i) for i, v in enumerate(body.vaginas))
#         lines.append(f"[bold]V:[/bold] {vagina_line}")
    
#     if body.has_scrotum:
#         scrotum_line = " | ".join(render_scrotum_compact(s, i) for i, s in enumerate(body.scrotums))
#         lines.append(f"[bold]S:[/bold] {scrotum_line}")
    
#     if not lines:
#         return Panel("[dim]No genitals[/dim]", title="Genitals", box=box.SIMPLE, border_style="dim")
    
#     return Panel(
#         "\\n".join(lines),
#         title="[bold]🔞 Genitals[/bold]",
#         border_style="bright_red",
#         box=box.SIMPLE,
#         padding=(0, 1)
#     )

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
                     show_uterus: bool = True, compact: bool = True) -> RenderableType:
    """Компактное полное отображение тела."""
    has_breasts = show_breasts and body.has_breasts
    has_genitals = show_genitals and (body.has_penis or body.has_vagina)
    has_uterus = show_uterus and hasattr(body, 'uterus_system') and body.uterus_system
    
    sections = []
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
    
    if body.has_breasts:
        breasts = root.add("🍼")
        for r_idx, row in enumerate(body.breast_grid.rows):
            for c_idx, breast in enumerate(row):
                label = body.breast_grid.get_label(r_idx, c_idx)
                state_emoji = STATE_EMOJIS.get(getattr(breast, '_state', None), "○")
                filled = getattr(breast, 'filled', 0) or 0
                volume = getattr(breast, 'volume', 0) or 0
                breasts.add(f"{state_emoji}{label}:{filled:.0f}/{volume:.0f}ml")
    
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
# body_sim/ui/genitals_render.py
"""
Рендеринг гениталий с отображением типов.
"""

from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich import box


def render_penis(penis, index: int = 0) -> Panel:
    """Отобразить пенис с информацией о типе."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Property", style="dim cyan", width=14)
    table.add_column("Value")
    
    # Статус эрекции
    if penis.is_erect:
        status = "[bold red]ERECT 🔥[/bold red]"
        size_color = "bright_red"
    else:
        status = "[dim]Flaccid[/dim]"
        size_color = "white"
    
    table.add_row("Status:", status)
    
    # ТИП ПЕНИСА
    type_color = {
        "human": "white",
        "knotted": "red",
        "tapered": "purple",
        "flared": "magenta",
        "barbed": "dark_red",
        "double": "cyan",
        "prehensile": "green",
        "equine": "black",
        "canine": "red",
        "feline": "pink",
        "dragon": "purple",
        "demon": "red",
        "tentacle": "green",
        "horseshoe": "pink",
        "spiral": "blue",
        "ribbed": "orange",
        "bifurcated": "pink"
    }.get(penis.penis_type.id, "white")
    
    table.add_row(
        "Type:", 
        f"[{type_color}]{penis.penis_type.type_name}[/{type_color}]"
    )
    
    # Особые характеристики
    features = []
    if penis.has_knot:
        features.append(f"[red]Узел ×{penis.knot_factor:.1f}[/red]")
    if penis.has_barbs:
        features.append(f"[dark_red]Шипы ({penis.barb_count})[/dark_red]")
    if penis.has_ridges:
        features.append(f"[yellow]Гребни ({penis.ridge_count})[/yellow]")
    if penis.has_spines:
        features.append("[red]Шипы[/red]")
    if penis.is_prehensile:
        features.append("[green]Хватательный[/green]")
    if penis.has_ribs:
        features.append(f"[orange]Рёбра ({penis.rib_count})[/orange]")
    if penis.has_spiral:
        features.append(f"[blue]Спираль ({penis.spiral_turns}в)[/blue]")
    if penis.is_split:
        features.append(f"[pink]Раздвоен {penis.split_depth:.0%}[/pink]")
    if penis.glows:
        features.append("[bright_yellow]★Светится[/bright_yellow]")
    
    if features:
        table.add_row("Features:", " | ".join(features))
    
    # Размеры
    table.add_row(
        "Length:", 
        f"[{size_color}]{penis.current_length:.1f}cm[/{size_color}] (base: {penis.base_length:.1f}cm)"
    )
    table.add_row("Girth:", f"{penis.current_girth:.1f}cm")
    table.add_row("Diameter:", f"{penis.current_diameter:.1f}cm")
    
    # Узел если есть
    if penis.has_knot:
        table.add_row("Knot:", f"[red]{penis.knot_girth:.1f}cm[/red]")
    
    # Расширение если есть
    if penis.flare_factor > 1.2:
        table.add_row("Flare:", f"[magenta]{penis.flare_girth:.1f}cm[/magenta]")
    
    # Возбуждение
    table.add_row("Arousal:", f"{penis.arousal:.0%}")
    table.add_row("Pleasure:", f"{penis.pleasure:.2f}")
    
    # Сперма
    cum_color = "yellow" if penis.current_cum_volume > penis.cum_reservoir * 0.8 else "cyan"
    table.add_row(
        "Cum:", 
        f"[{cum_color}]{penis.current_cum_volume:.1f}ml / {penis.cum_reservoir:.1f}ml[/{cum_color}]"
    )
    
    # Объём
    table.add_row("Volume:", f"{penis.volume:.1f}ml")
    
    if penis.is_transformed_clitoris:
        table.add_row("Note:", "[magenta italic]Трансформированный клитор[/magenta italic]")
    
    # Эмодзи для заголовка
    type_emoji = {
        "human": "🍆",
        "knotted": "🍆",
        "tapered": "🥖",
        "flared": "🍄",
        "barbed": "🌵",
        "double": "🍆🍆",
        "prehensile": "🐙",
        "equine": "🐴",
        "canine": "🐕",
        "feline": "🐱",
        "dragon": "🐲",
        "demon": "😈",
        "tentacle": "🦑",
        "horseshoe": "🔱",
        "spiral": "🌀",
        "ribbed": "〰️",
        "bifurcated": "🔱"
    }.get(penis.penis_type.id, "🍆")
    
    return Panel(
        table,
        title=f"[bold]{type_emoji} Penis #{index} [{penis.penis_type.id.upper()}][/bold]",
        border_style="red" if penis.is_erect else "dim",
        box=box.ROUNDED,
        padding=(0, 1)
    )


def render_vagina(vagina, index: int = 0) -> Panel:
    """Отобразить влагалище с информацией о типе."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Property", style="dim cyan", width=14)
    table.add_column("Value")
    
    # Статус
    if vagina.is_aroused:
        status = "[bold magenta]AROUSED 💧[/bold magenta]"
        size_color = "bright_magenta"
    else:
        status = "[dim]Normal[/dim]"
        size_color = "white"
    
    table.add_row("Status:", status)
    
    # ТИП ВЛАГАЛИЩА
    type_color = {
        "human": "white",
        "sinuous": "purple",
        "deepcave": "blue",
        "ribbed": "orange",
        "tentacled": "green",
        "demonic": "red",
        "plant": "green",
        "slime": "cyan"
    }.get(vagina.vagina_type.id, "white")
    
    table.add_row(
        "Type:", 
        f"[{type_color}]{vagina.vagina_type.type_name}[/{type_color}]"
    )
    
    # Особые характеристики
    features = []
    if vagina.has_cervical_pouch:
        features.append("[blue]Цервикальный мешок[/blue]")
    if vagina.extra_depth:
        features.append("[blue]Глубокое[/blue]")
    if vagina.has_ridges:
        features.append(f"[orange]{vagina.ridge_count} гребней[/orange]")
    if vagina.has_tentacles:
        features.append("[green]Щупальца[/green]")
    if vagina.self_lubricating:
        features.append("[cyan]Самосмазка[/cyan]")
    if vagina.glows:
        features.append("[yellow]★Светится[/yellow]")
    if vagina.can_expand:
        features.append("[green]Расширяемое[/green]")
    if vagina.is_slime:
        features.append("[cyan]Слизь[/cyan]")
    if vagina.can_reform:
        features.append("[cyan]Реформируемое[/cyan]")
    
    if features:
        table.add_row("Features:", " | ".join(features))
    
    # Размеры
    table.add_row(
        "Depth:",
        f"[{size_color}]{vagina.current_depth:.1f}cm[/{size_color}] (base: {vagina.base_depth:.1f}cm)"
    )
    table.add_row(
        "Width:",
        f"{vagina.current_width:.1f}cm (stretch: ×{vagina.current_stretch:.2f})"
    )
    
    # Параметры
    table.add_row("Tightness:", f"{vagina.tightness:.2f}")
    table.add_row("Lubrication:", f"{vagina.lubrication:.0%}")
    table.add_row("Arousal:", f"{vagina.arousal:.0%}")
    table.add_row("Muscle tone:", f"{vagina.muscle_tone:.2f}")
    table.add_row("Elasticity:", f"{vagina.elasticity:.2f}")
    
    # Объём
    table.add_row("Volume:", f"{vagina.volume:.1f}ml")
    
    # Эмодзи для заголовка
    type_emoji = {
        "human": "🌸",
        "sinuous": "🌀",
        "deepcave": "🕳️",
        "ribbed": "〰️",
        "tentacled": "🐙",
        "demonic": "😈",
        "plant": "🌿",
        "slime": "💧"
    }.get(vagina.vagina_type.id, "🌸")
    
    return Panel(
        table,
        title=f"[bold]{type_emoji} Vagina #{index} [{vagina.vagina_type.id.upper()}][/bold]",
        border_style="magenta" if vagina.is_aroused else "dim",
        box=box.ROUNDED,
        padding=(0, 1)
    )


def render_scrotum(scrotum, index: int = 0) -> Panel:
    """Отобразить мошонку с информацией о типе."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Property", style="dim cyan", width=14)
    table.add_column("Value")
    
    # ТИП МОШОНКИ
    type_names = {
        "standard": "Обычная",
        "tight": "Плотная",
        "loose": "Свисающая",
        "sheathed": "В ножне",
        "internal": "Внутренняя",
        "segmented": "Сегментированная"
    }
    
    table.add_row(
        "Type:",
        type_names.get(scrotum.scrotum_type.id, "Unknown")
    )
    
    # Особенности
    features = []
    if scrotum.retracts:
        features.append("Втягивается")
    if scrotum.swings:
        features.append("Качается")
    if scrotum.has_sheath:
        features.append("Ножна")
    if scrotum.is_internal:
        features.append("Внутренняя")
    if scrotum.has_segments:
        features.append(f"{scrotum.segment_count} сегмента")
    
    if features:
        table.add_row("Features:", " | ".join(features))
    
    testicle_count = len(scrotum.testicles)
    table.add_row("Testicles:", f"🥚 ×{testicle_count}")
    table.add_row("Fullness:", f"{scrotum.fullness:.0%}")
    table.add_row("Capacity:", f"{scrotum.total_storage_capacity:.1f}ml")
    table.add_row("Stored:", f"{scrotum.total_stored_volume:.1f}ml")
    
    if scrotum.testicles:
        temp = scrotum.testicles[0].temperature
        temp_color = "red" if temp > 37.5 else "blue" if temp < 35 else "green"
        table.add_row("Temperature:", f"[{temp_color}]{temp:.1f}°C[/{temp_color}]")
    
    return Panel(
        table,
        title=f"[bold]🥚 Scrotum #{index} [{scrotum.scrotum_type.id.upper()}][/bold]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(0, 1)
    )


def render_anus(anus, index: int = 0) -> Panel:
    """Отобразить анус."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Property", style="dim cyan", width=14)
    table.add_column("Value")
    
    if getattr(anus, 'is_penetrated', False):
        status = "[bold red]PENETRATED[/bold red]"
    else:
        status = "[dim]Normal[/dim]"
    
    table.add_row("Status:", status)
    
    if hasattr(anus, 'current_diameter'):
        table.add_row("Diameter:", f"{anus.current_diameter:.2f}cm")
    if hasattr(anus, 'max_diameter'):
        table.add_row("Max stretch:", f"{anus.max_diameter:.2f}cm")
    if hasattr(anus, 'muscle_tone'):
        table.add_row("Muscle tone:", f"{anus.muscle_tone:.2f}")
    
    return Panel(
        table,
        title=f"[bold]🍑 Anus #{index}[/bold]",
        border_style="dim",
        box=box.ROUNDED,
        padding=(0, 1)
    )


def render_genitals(body) -> Panel:
    """Отобразить все гениталии тела."""
    panels = []
    
    if body.has_penis:
        for i, penis in enumerate(body.penises):
            panels.append(render_penis(penis, i))
    
    if body.has_vagina:
        for i, vagina in enumerate(body.vaginas):
            panels.append(render_vagina(vagina, i))
    
    if body.has_scrotum:
        for i, scrotum in enumerate(body.scrotums):
            panels.append(render_scrotum(scrotum, i))
    
    if hasattr(body, 'anuses') and body.anuses:
        for i, anus in enumerate(body.anuses):
            panels.append(render_anus(anus, i))
    
    if not panels:
        return Panel(
            "[dim italic]No genitals[/dim italic]",
            title="[bold]Genitals[/bold]",
            border_style="dim"
        )
    
    content = Columns(panels, equal=True, expand=True)
    
    return Panel(
        content,
        title="[bold]🔞 Genitals[/bold]",
        border_style="bright_red",
        box=box.ROUNDED,
        padding=(0, 1)
    )
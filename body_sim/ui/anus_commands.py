# body_sim/ui/anus_commands.py
"""
Команды для управления анусом и глубокой пенетрацией через прямую кишку в желудок.
"""

from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def _get_anus(body, anus_idx: int = 0):
    """Получить анус по индексу с проверкой."""
    if not body or not hasattr(body, 'anuses') or not body.anuses:
        return None, "No anus available"
    if anus_idx < 0 or anus_idx >= len(body.anuses):
        return None, f"Invalid anus index: {anus_idx} (max: {len(body.anuses)-1})"
    return body.anuses[anus_idx], None


def _get_rectum(body):
    """Получить rectum систему."""
    if not body or not hasattr(body, 'rectum_system') or not body.rectum_system:
        return None
    return body.rectum_system.primary


def _get_stomach(body):
    """Получить желудок."""
    if not body or not hasattr(body, 'stomach_system') or not body.stomach_system:
        return None
    return body.stomach_system.primary


# ============ STATUS COMMANDS ============

def cmd_anus_status(args: List[str], ctx) -> None:
    """Показать статус ануса и связанных систем."""
    anus_idx = int(args[0]) if args else 0
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    # Основная таблица ануса
    table = Table(show_header=True, box=box.ROUNDED, title=f"Anus #{anus_idx} Status")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("State", anus.sphincter_state.name if hasattr(anus, 'sphincter_state') else "NORMAL")
    table.add_row("Sphincter Tone", f"{anus.sphincter_tone:.2f}")
    table.add_row("Current Diameter", f"{anus.current_diameter:.1f} cm")
    table.add_row("Max Diameter", f"{anus.max_diameter:.1f} cm")
    table.add_row("Is Gaping", "Yes" if anus.is_gaping else "No")
    
    if anus.is_gaping:
        table.add_row("Gape Size", f"{anus.gaping_size:.1f} cm")
    
    if hasattr(anus, 'prolapse_degree') and anus.prolapse_degree > 0:
        table.add_row("Prolapse", f"{anus.prolapse_degree:.1%} ⚠️")
    
    console.print(table)
    
    # Информация о соединениях
    if anus.rectum_connection:
        rectum = anus.rectum_connection
        console.print(f"\n[dim]Connected to rectum (length: {rectum.total_length:.1f} cm)[/dim]")
        
        if rectum.stomach_connection:
            console.print(f"[dim]↳ Rectum connects to stomach[/dim]")
            
        # Инфо о текущей пенетрации
        if rectum.inserted_object:
            obj = rectum.inserted_object
            console.print(f"\n[bold yellow]Object inserted:[/bold yellow] {getattr(obj, 'name', 'unknown')}")
            console.print(f"  Depth in rectum: {rectum.penetration_depth:.1f} / {rectum.total_length:.1f} cm")
            
            # Проверяем, достиг ли желудка
            if rectum.stomach_connection and rectum.stomach_connection.inserted_object:
                console.print(f"  [bold red]⚠️ Object reached stomach![/bold red]")
        else:
            console.print(f"\n[dim]No object inserted[/dim]")


def cmd_anus_fullness(args: List[str], ctx) -> None:
    """Показать детальное заполнение (аналог uterus fullness)."""
    anus_idx = int(args[0]) if args else 0
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    rectum = _get_rectum(ctx.active_body)
    stomach = _get_stomach(ctx.active_body)
    
    # Создаем визуальное представление
    console.print(f"\n[bold cyan]Anal System Fullness #{anus_idx}[/bold cyan]\n")
    
    # Анус
    anus_fill = (anus.current_diameter / anus.max_diameter) * 100
    bar = _make_fill_bar(anus_fill, 20)
    console.print(f"[bold]Anus:[/bold]        [{bar}] {anus_fill:.0f}%")
    console.print(f"  Diameter: {anus.current_diameter:.1f} / {anus.max_diameter:.1f} cm")
    
    # Rectum
    if rectum:
        rect_fill = rectum.fill_ratio * 100
        bar = _make_fill_bar(rect_fill, 20)
        console.print(f"\n[bold]Rectum:[/bold]      [{bar}] {rect_fill:.0f}%")
        console.print(f"  Fluid: {rectum.filled:.1f} / {rectum.max_capacity * (rectum.inflation_ratio ** 2):.1f} ml")
        console.print(f"  Length: {rectum.total_length:.1f} cm (stretch: {rectum.wall.stretch_ratio:.2f}x)")
        console.print(f"  Diameter: {rectum.effective_diameter:.1f} cm")
        
        if rectum.inserted_object:
            obj = rectum.inserted_object
            depth_pct = (rectum.penetration_depth / rectum.total_length) * 100
            console.print(f"  [yellow]Object: {getattr(obj, 'name', 'unknown')} at {depth_pct:.0f}% depth[/yellow]")
    
    # Stomach (если объект дошел)
    if stomach and stomach.inserted_object:
        stom_fill = stomach.fill_ratio * 100
        bar = _make_fill_bar(stom_fill, 20)
        console.print(f"\n[bold magenta]Stomach:[/bold magenta]     [{bar}] {stom_fill:.0f}%")
        console.print(f"  Volume: {stomach.filled:.1f} / {stomach.current_volume:.1f} ml")
        console.print(f"  State: {stomach.state.name}")
        if stomach.penetration_depth > 0:
            console.print(f"  [red]↳ Object from rectum at depth: {stomach.penetration_depth:.1f} cm[/red]")


def _make_fill_bar(percentage: float, width: int = 20) -> str:
    """Создать текстовую полосу заполнения."""
    filled = int((percentage / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    return bar


# ============ CONTROL COMMANDS ============

def cmd_anus_relax(args: List[str], ctx) -> None:
    """Расслабить сфинктер."""
    anus_idx = int(args[0]) if args else 0
    amount = float(args[1]) if len(args) > 1 else 0.3
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    old_tone = anus.sphincter_tone
    anus.relax(amount)
    console.print(f"[green]Anus #{anus_idx} relaxed: {old_tone:.2f} → {anus.sphincter_tone:.2f}[/green]")


def cmd_anus_contract(args: List[str], ctx) -> None:
    """Сжать сфинктер."""
    anus_idx = int(args[0]) if args else 0
    amount = float(args[1]) if len(args) > 1 else 0.2
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    old_tone = anus.sphincter_tone
    anus.contract(amount)
    console.print(f"[green]Anus #{anus_idx} contracted: {old_tone:.2f} → {anus.sphincter_tone:.2f}[/green]")


def cmd_anus_stretch(args: List[str], ctx) -> None:
    """Растянуть анус до определенного диаметра."""
    if not args:
        console.print("[red]Usage: anus_stretch <diameter> [idx][/red]")
        return
    
    diameter = float(args[0])
    anus_idx = int(args[1]) if len(args) > 1 else 0
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    success = anus.stretch(diameter)
    if success:
        console.print(f"[bold magenta]Anus #{anus_idx} stretched to {diameter:.1f} cm[/bold magenta]")
        if diameter > anus.base_diameter * 2:
            console.print("[yellow]⚠️ Significant stretching![/yellow]")
    else:
        console.print(f"[red]Cannot stretch beyond {anus.max_diameter} cm[/red]")


def cmd_anus_close(args: List[str], ctx) -> None:
    """Закрыть анус."""
    anus_idx = int(args[0]) if args else 0
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    anus.close()
    console.print(f"[green]Anus #{anus_idx} closed[/green]")


# ============ PENETRATION COMMANDS ============

def cmd_anus_insert(args: List[str], ctx) -> None:
    """Вставить объект в анус."""
    if len(args) < 1:
        console.print("[red]Usage: anus_insert <object_name> [diameter] [length] [idx] [force][/red]")
        return
    
    obj_name = args[0]
    diameter = float(args[1]) if len(args) > 1 else 3.0
    length = float(args[2]) if len(args) > 2 else 15.0
    anus_idx = int(args[3]) if len(args) > 3 else 0
    force = args[4].lower() in ('true', '1', 'yes', 'force') if len(args) > 4 else False
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    # Создаем простой объект
    class PenetrationObject:
        def __init__(self, name, diameter, length):
            self.name = name
            self.diameter = diameter
            self.length = length
            self.volume = (diameter/2)**2 * 3.14159 * length
            self.effective_diameter = diameter
            self.effective_volume = self.volume
            self.is_inserted = False
    
    obj = PenetrationObject(obj_name, diameter, length)
    success = anus.insert_object(obj, force=force)
    
    if success:
        console.print(f"[green]✓ {obj_name} inserted into anus #{anus_idx}[/green]")
        console.print(f"[dim]Diameter: {diameter}cm, Volume: {obj.volume:.1f}ml[/dim]")
    else:
        console.print(f"[red]Failed to insert (too large or not relaxed)[/red]")


def cmd_anus_advance(args: List[str], ctx) -> None:
    """Продвинуть объект глубже к желудку."""
    if len(args) < 1:
        console.print("[red]Usage: anus_advance <depth> [idx][/red]")
        console.print("Example: anus_advance 10 (move 10cm deeper)")
        return
    
    depth = float(args[0])
    anus_idx = int(args[1]) if len(args) > 1 else 0
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if not anus.rectum_connection or not anus.rectum_connection.inserted_object:
        console.print("[red]No object inserted[/red]")
        return
    
    moved, reached, zone = anus.advance_object(depth)
    
    if reached:
        console.print(f"[bold red]🎯 Object reached stomach! (moved {moved:.1f}cm)[/bold red]")
    else:
        color = "yellow" if zone == "rectum" else "cyan" if zone == "sigmoid" else "white"
        console.print(f"[{color}]Advanced {moved:.1f}cm into {zone}[/{color}]")
        
    # Показываем текущую глубину
    rectum = anus.rectum_connection
    total_depth = anus.penetration_depth + (rectum.penetration_depth if rectum else 0)
    console.print(f"[dim]Total depth from anus: {total_depth:.1f} cm[/dim]")


def cmd_anus_retract(args: List[str], ctx) -> None:
    """Вытянуть объект наружу."""
    if len(args) < 1:
        console.print("[red]Usage: anus_retract <amount> [idx][/red]")
        return
    
    amount = float(args[0])
    anus_idx = int(args[1]) if len(args) > 1 else 0
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    moved, removed = anus.retract_object(amount)
    
    if removed:
        console.print(f"[green]Object removed from anus #{anus_idx} (moved {moved:.1f}cm)[/green]")
    else:
        console.print(f"[yellow]Retracted {moved:.1f}cm[/yellow]")


def cmd_anus_remove(args: List[str], ctx) -> None:
    """Полностью извлечь объект."""
    anus_idx = int(args[0]) if args else 0
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    obj = anus.remove_object()
    if obj:
        console.print(f"[green]Removed {getattr(obj, 'name', 'object')} from anus #{anus_idx}[/green]")
    else:
        console.print("[yellow]No object to remove[/yellow]")


# ============ FLUID COMMANDS ============

def cmd_anus_add_fluid(args: List[str], ctx) -> None:
    """Добавить жидкость (клизма)."""
    if len(args) < 2:
        console.print("[red]Usage: anus_add_fluid <type> <amount> [idx][/red]")
        console.print("Types: water, milk, cum, oil, honey")
        return
    
    fluid_name = args[0].upper()
    amount = float(args[1])
    anus_idx = int(args[2]) if len(args) > 2 else 0
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    try:
        from body_sim.core.enums import FluidType
        fluid_type = FluidType[fluid_name]
    except KeyError:
        console.print(f"[red]Unknown fluid type: {fluid_name}[/red]")
        return
    
    added = anus.add_fluid(fluid_type, amount)
    console.print(f"[cyan]Added {added:.1f}ml of {fluid_name} to anus #{anus_idx}[/cyan]")
    
    if added < amount:
        console.print(f"[yellow]⚠ {amount - added:.1f}ml could not fit[/yellow]")


def cmd_anus_drain(args: List[str], ctx) -> None:
    """Опустошить содержимое."""
    anus_idx = int(args[0]) if args else 0
    
    anus, error = _get_anus(ctx.active_body, anus_idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    rectum = anus.rectum_connection
    if rectum:
        removed = rectum.mixture.total()
        rectum.mixture.components.clear()
        console.print(f"[yellow]Drained {removed:.1f}ml from rectum[/yellow]")
    else:
        console.print("[dim]Nothing to drain[/dim]")


# ============ RECTUM/STOMACH COMMANDS ============

def cmd_rectum_stretch(args: List[str], ctx) -> None:
    """Растянуть прямую кишку."""
    if not args:
        console.print("[red]Usage: rectum_stretch <ratio>[/red]")
        return
    
    ratio = float(args[0])
    rectum = _get_rectum(ctx.active_body)
    
    if not rectum:
        console.print("[red]No rectum available[/red]")
        return
    
    success = rectum.wall.stretch(ratio)
    if success:
        console.print(f"[magenta]Rectum stretched to {ratio:.1f}x[/magenta]")
        rectum.current_diameter = rectum.base_diameter * ratio
    else:
        console.print("[red]Cannot stretch further - risk of damage![/red]")


def cmd_stomach_from_anus(args: List[str], ctx) -> None:
    """Показать статус желудка при пенетрации сзади."""
    stomach = _get_stomach(ctx.active_body)
    if not stomach:
        console.print("[red]No stomach available[/red]")
        return
    
    table = Table(title="Stomach (via Anus)", box=box.ROUNDED)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value")
    
    table.add_row("State", stomach.state.name)
    table.add_row("Fill", f"{stomach.filled:.1f} / {stomach.current_volume:.1f} ml")
    table.add_row("Fill Ratio", f"{stomach.fill_ratio:.1%}")
    table.add_row("Inflation", f"{stomach.inflation_ratio:.2f}x")
    table.add_row("Wall Stretch", f"{stomach.walls.stretch_ratio:.2f}x")
    
    if stomach.inserted_object:
        obj = stomach.inserted_object
        table.add_row("Object", f"{getattr(obj, 'name', 'unknown')}")
        table.add_row("Depth from pylorus", f"{stomach.penetration_depth:.1f} cm")
    
    console.print(table)


# ============ REGISTRATION FUNCTION ============

def register_anus_commands(registry, console_instance=None):
    """Зарегистрировать все команды ануса в реестре."""
    global console
    if console_instance:
        console = console_instance
    
    from body_sim.ui.commands import Command
    
    # Status commands
    registry.register(Command(
        "anus", ["anus_status"],
        "Show anus status",
        "anus [idx]",
        cmd_anus_status,
        "anus"
    ))
    
    registry.register(Command(
        "anus_fullness", ["afull", "af"],
        "Show detailed fullness (anus + rectum + stomach)",
        "anus_fullness [idx]",
        cmd_anus_fullness,
        "anus"
    ))
    
    # Control commands
    registry.register(Command(
        "anus_relax", ["arelax"],
        "Relax sphincter",
        "anus_relax [idx] [amount]",
        cmd_anus_relax,
        "anus"
    ))
    
    registry.register(Command(
        "anus_contract", ["acontract"],
        "Contract sphincter",
        "anus_contract [idx] [amount]",
        cmd_anus_contract,
        "anus"
    ))
    
    registry.register(Command(
        "anus_stretch", ["astretch"],
        "Stretch anus to diameter",
        "anus_stretch <diameter> [idx]",
        cmd_anus_stretch,
        "anus"
    ))
    
    registry.register(Command(
        "anus_close", ["aclose"],
        "Close anus",
        "anus_close [idx]",
        cmd_anus_close,
        "anus"
    ))
    
    # Penetration commands
    registry.register(Command(
        "anus_insert", ["ainsert", "ains"],
        "Insert object into anus",
        "anus_insert <name> [diameter] [length] [idx] [force]",
        cmd_anus_insert,
        "anus"
    ))
    
    registry.register(Command(
        "anus_advance", ["aadv", "go deeper"],
        "Advance object deeper toward stomach",
        "anus_advance <depth_cm> [idx]",
        cmd_anus_advance,
        "anus"
    ))
    
    registry.register(Command(
        "anus_retract", ["aret"],
        "Retract object outward",
        "anus_retract <amount> [idx]",
        cmd_anus_retract,
        "anus"
    ))
    
    registry.register(Command(
        "anus_remove", ["arem"],
        "Remove object completely",
        "anus_remove [idx]",
        cmd_anus_remove,
        "anus"
    ))
    
    # Fluid commands
    registry.register(Command(
        "anus_add_fluid", ["afluid", "enema"],
        "Add fluid (enema)",
        "anus_add_fluid <type> <amount> [idx]",
        cmd_anus_add_fluid,
        "anus"
    ))
    
    registry.register(Command(
        "anus_drain", ["adrain"],
        "Drain all fluid",
        "anus_drain [idx]",
        cmd_anus_drain,
        "anus"
    ))
    
    # Deep commands
    registry.register(Command(
        "rectum_stretch", ["rstretch"],
        "Stretch rectum walls",
        "rectum_stretch <ratio>",
        cmd_rectum_stretch,
        "anus"
    ))
    
    registry.register(Command(
        "stomach_anus", ["stomach_back", "sback"],
        "Show stomach status (back entry)",
        "stomach_anus",
        cmd_stomach_from_anus,
        "anus"
    ))
    
    console.print("[dim]Anus/Rectum commands registered (15 commands)[/dim]")

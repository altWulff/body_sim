# body_sim/ui/mouth_commands.py
"""
Команды для управления ртом, глоткой и пищеводом.
Система пенетрации аналогична анальной, но с рвотным рефлексом и дыханием.
"""

from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def _get_mouth(body, idx: int = 0):
    """Получить рот по индексу."""
    if not body or not hasattr(body, 'mouth_system') or not body.mouth_system:
        return None, "No mouth system available"
    mouths = body.mouth_system.mouths
    if idx < 0 or idx >= len(mouths):
        return None, f"Invalid mouth index: {idx} (max: {len(mouths)-1})"
    return mouths[idx], None


def _get_esophagus(body):
    """Получить пищевод."""
    if not body or not hasattr(body, 'esophagus') or not body.esophagus:
        return None
    return body.esophagus


def _get_stomach(body):
    """Получить желудок."""
    if not body or not hasattr(body, 'stomach_system') or not body.stomach_system:
        return None
    return body.stomach_system.primary


# ============ STATUS COMMANDS ============

def cmd_mouth_status(args: List[str], ctx) -> None:
    """Показать статус рта."""
    idx = int(args[0]) if args else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    table = Table(show_header=True, box=box.ROUNDED, title=f"Mouth #{idx} Status")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("State", mouth.state.name if hasattr(mouth, 'state') else "NORMAL")
    table.add_row("Can Breathe", "Yes" if mouth.can_breathe else "[red]No[/red]")
    table.add_row("Fill Ratio", f"{mouth.fill_ratio:.1%}")
    table.add_row("Fluid", f"{mouth.mixture.total():.1f} ml")
    
    # Губы
    if hasattr(mouth, 'lips'):
        lips = mouth.lips
        table.add_row("Lips State", lips.state.name if hasattr(lips, 'state') else "CLOSED")
        table.add_row("Lips Stretch", f"{lips.stretch_ratio:.2f}x")
        table.add_row("Opening", f"{lips.effective_opening:.1f} cm")
    
    # Глотка
    if hasattr(mouth, 'throat'):
        throat = mouth.throat
        table.add_row("Throat State", throat.state.name)
        table.add_row("Throat Diameter", f"{throat.effective_diameter:.1f} cm")
        table.add_row("Gag Reflex", "Triggered" if mouth.gag_triggered else "Ready")
    
    # Пенетрация
    if mouth.inserted_object:
        obj = mouth.inserted_object
        table.add_row("[yellow]Inserted[/yellow]", f"{getattr(obj, 'name', 'object')}")
        table.add_row("Depth", f"{mouth.penetration_depth:.1f} cm")
    
    console.print(table)


def cmd_mouth_fullness(args: List[str], ctx) -> None:
    """Детальное заполнение рта."""
    idx = int(args[0]) if args else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    console.print(f"\n[bold cyan]Mouth System Fullness #{idx}[/bold cyan]\n")
    
    # Рот
    fill = mouth.fill_ratio * 100
    bar = _make_bar(fill, 20)
    console.print(f"[bold]Mouth:[/bold]       [{bar}] {fill:.0f}%")
    console.print(f"  Fluid: {mouth.mixture.total():.1f} ml")
    console.print(f"  Cheeks: {mouth.cheek_stretch:.2f}x stretched")
    
    # Губы
    if hasattr(mouth, 'lips'):
        lips = mouth.lips
        console.print(f"\n[bold]Lips:[/bold]")
        console.print(f"  State: {lips.state.name}")
        console.print(f"  Opening: {lips.effective_opening:.1f} cm")
        console.print(f"  Fatigue: {lips.fatigue:.2f}")
    
    # Глотка
    if hasattr(mouth, 'throat'):
        throat = mouth.throat
        console.print(f"\n[bold]Throat:[/bold]")
        console.print(f"  State: {throat.state.name}")
        console.print(f"  Constriction: {throat.constriction:.2f}")
        console.print(f"  Length: {throat.length} cm")
    
    # Объект
    if mouth.inserted_object:
        obj = mouth.inserted_object
        depth_pct = (mouth.penetration_depth / (throat.length if hasattr(mouth, 'throat') else 12)) * 100
        console.print(f"\n[yellow]Object: {getattr(obj, 'name', 'unknown')}[/yellow]")
        console.print(f"  Depth: {mouth.penetration_depth:.1f} cm ({depth_pct:.0f}% into throat)")


def _make_bar(pct: float, width: int = 20) -> str:
    filled = int((pct / 100) * width)
    return "█" * filled + "░" * (width - filled)


# ============ CONTROL COMMANDS ============

def cmd_mouth_open(args: List[str], ctx) -> None:
    """Открыть рот."""
    idx = int(args[0]) if args else 0
    amount = float(args[1]) if len(args) > 1 else 0.5
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(mouth, 'lips'):
        mouth.lips.state = mouth.lips.__class__.__dict__.get('SLIGHTLY_OPEN', 0)  # Enum workaround
        console.print(f"[green]Mouth #{idx} opened[/green]")


def cmd_mouth_close(args: List[str], ctx) -> None:
    """Закрыть рот."""
    idx = int(args[0]) if args else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(mouth, 'lips'):
        mouth.lips.state = mouth.lips.__class__.__dict__.get('CLOSED', 0)
        console.print(f"[green]Mouth #{idx} closed[/green]")


def cmd_mouth_stretch(args: List[str], ctx) -> None:
    """Растянуть губы."""
    if not args:
        console.print("[red]Usage: mouth_stretch <ratio> [idx][/red]")
        return
    
    ratio = float(args[0])
    idx = int(args[1]) if len(args) > 1 else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(mouth, 'lips'):
        success = mouth.lips.stretch(ratio)
        if success:
            console.print(f"[magenta]Mouth #{idx} lips stretched to {ratio:.1f}x[/magenta]")
        else:
            console.print("[red]Cannot stretch further[/red]")


def cmd_mouth_puff(args: List[str], ctx) -> None:
    """Раздуть щеки."""
    if not args:
        console.print("[red]Usage: mouth_puff <ratio> [idx][/red]")
        return
    
    ratio = float(args[0])
    idx = int(args[1]) if len(args) > 1 else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    mouth.stretch_cheeks(ratio)
    console.print(f"[cyan]Cheeks puffed to {ratio:.1f}x[/cyan]")


# ============ PENETRATION COMMANDS ============

def cmd_mouth_insert(args: List[str], ctx) -> None:
    """Вставить объект в рот."""
    if len(args) < 1:
        console.print("[red]Usage: mouth_insert <name> [diameter] [length] [idx] [force][/red]")
        return
    
    name = args[0]
    diameter = float(args[1]) if len(args) > 1 else 3.0
    length = float(args[2]) if len(args) > 2 else 15.0
    idx = int(args[3]) if len(args) > 3 else 0
    force = args[4].lower() in ('true', '1', 'yes', 'force') if len(args) > 4 else False
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    class Obj:
        def __init__(self, n, d, l):
            self.name = n
            self.diameter = d
            self.length = l
            self.volume = (d/2)**2 * 3.14 * l
            self.is_inserted = False
    
    obj = Obj(name, diameter, length)
    success = mouth.insert_object(obj, force=force)
    
    if success:
        console.print(f"[green]✓ {name} inserted into mouth #{idx}[/green]")
    else:
        console.print("[red]Failed - mouth closed or object too large[/red]")


def cmd_mouth_advance(args: List[str], ctx) -> None:
    """Продвинуть в глотку."""
    if len(args) < 1:
        console.print("[red]Usage: mouth_advance <depth> [idx][/red]")
        return
    
    depth = float(args[0])
    idx = int(args[1]) if len(args) > 1 else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if not mouth.inserted_object:
        console.print("[red]No object inserted[/red]")
        return
    
    moved = mouth.advance_object(depth)
    
    # Проверяем рефлексы
    status = []
    if mouth.gag_triggered:
        status.append("[red]GAG REFLEX![/red]")
    if mouth.choking:
        status.append("[red]CHOKING![/red]")
    
    if status:
        console.print(f"[yellow]Advanced {moved:.1f}cm - {' '.join(status)}[/yellow]")
    else:
        console.print(f"[green]Advanced {moved:.1f}cm[/green]")
    
    console.print(f"[dim]Depth: {mouth.penetration_depth:.1f} cm[/dim]")


def cmd_mouth_retract(args: List[str], ctx) -> None:
    """Вытянуть объект."""
    if len(args) < 1:
        console.print("[red]Usage: mouth_retract <amount> [idx][/red]")
        return
    
    amount = float(args[0])
    idx = int(args[1]) if len(args) > 1 else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    moved = mouth.retract_object(amount)
    
    if mouth.penetration_depth <= 0:
        console.print(f"[green]Object at entrance (moved {moved:.1f}cm)[/green]")
    else:
        console.print(f"[yellow]Retracted {moved:.1f}cm[/yellow]")


def cmd_mouth_remove(args: List[str], ctx) -> None:
    """Извлечь объект."""
    idx = int(args[0]) if args else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    obj = mouth.remove_object()
    if obj:
        console.print(f"[green]Removed {getattr(obj, 'name', 'object')}[/green]")
    else:
        console.print("[dim]No object to remove[/dim]")


# ============ FLUID COMMANDS ============

def cmd_mouth_add_fluid(args: List[str], ctx) -> None:
    """Добавить жидкость в рот."""
    if len(args) < 2:
        console.print("[red]Usage: mouth_add_fluid <type> <amount> [idx][/red]")
        return
    
    fluid_name = args[0].upper()
    amount = float(args[1])
    idx = int(args[2]) if len(args) > 2 else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    try:
        from body_sim.core.enums import FluidType
        fluid_type = FluidType[fluid_name]
    except KeyError:
        console.print(f"[red]Unknown fluid: {fluid_name}[/red]")
        return
    
    added = mouth.add_fluid(fluid_type, amount)
    console.print(f"[cyan]Added {added:.1f}ml of {fluid_name}[/cyan]")


def cmd_mouth_swallow(args: List[str], ctx) -> None:
    """Проглотить содержимое."""
    idx = int(args[0]) if args else 0
    amount = float(args[0]) if args else None
    idx = 0
    
    # Определяем, что первый аргумент - индекс или количество
    if args:
        try:
            # Если можно конвертировать в float но это похоже на индекс...
            val = float(args[0])
            if val < 10:  # Скорее всего индекс
                idx = int(val)
                amount = None
            else:  # Скорее всего количество
                amount = val
        except:
            idx = 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    swallowed = mouth.swallow(amount)
    if swallowed > 0:
        console.print(f"[green]Swallowed {swallowed:.1f}ml[/green]")
    else:
        console.print("[dim]Nothing to swallow or throat constricted[/dim]")


def cmd_mouth_spit(args: List[str], ctx) -> None:
    """Выплюнуть содержимое."""
    idx = int(args[0]) if args else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    removed = mouth.remove_fluid(mouth.mixture.total())
    console.print(f"[yellow]Spit out {removed:.1f}ml[/yellow]")


# ============ THROAT COMMANDS ============

def cmd_throat_open(args: List[str], ctx) -> None:
    """Открыть глотку."""
    idx = int(args[0]) if args else 0
    amount = float(args[1]) if len(args) > 1 else 0.5
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(mouth, 'throat'):
        mouth.throat.open(amount)
        console.print(f"[green]Throat opened ({amount})[/green]")


def cmd_throat_relax(args: List[str], ctx) -> None:
    """Расслабить глотку (снять спазм)."""
    idx = int(args[0]) if args else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(mouth, 'throat'):
        mouth.throat.constriction = 0
        mouth.throat.state = mouth.throat.__class__.__dict__.get('RELAXED', 0)
        console.print("[green]Throat relaxed[/green]")


def cmd_throat_stretch(args: List[str], ctx) -> None:
    """Растянуть глотку."""
    if not args:
        console.print("[red]Usage: throat_stretch <ratio> [idx][/red]")
        return
    
    ratio = float(args[0])
    idx = int(args[1]) if len(args) > 1 else 0
    
    mouth, error = _get_mouth(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(mouth, 'throat'):
        success = mouth.throat.stretch(ratio)
        if success:
            console.print(f"[magenta]Throat stretched to {ratio:.1f}x[/magenta]")
        else:
            console.print("[red]Cannot stretch beyond limit[/red]")


# ============ REGISTRATION ============

def register_mouth_commands(registry, console_instance=None):
    """Зарегистрировать команды рта."""
    global console
    if console_instance:
        console = console_instance
    
    from body_sim.ui.commands import Command
    
    # Status
    registry.register(Command("mouth", ["mouth_status"], "Show mouth status", "mouth [idx]", cmd_mouth_status, "mouth"))
    registry.register(Command("mouth_fullness", ["mfull"], "Mouth fullness details", "mouth_fullness [idx]", cmd_mouth_fullness, "mouth"))
    
    # Control
    registry.register(Command("mouth_open", ["mopen"], "Open mouth", "mouth_open [idx] [amount]", cmd_mouth_open, "mouth"))
    registry.register(Command("mouth_close", ["mclose"], "Close mouth", "mouth_close [idx]", cmd_mouth_close, "mouth"))
    registry.register(Command("mouth_stretch", ["mstretch"], "Stretch lips", "mouth_stretch <ratio> [idx]", cmd_mouth_stretch, "mouth"))
    registry.register(Command("mouth_puff", ["mpuff"], "Puff cheeks", "mouth_puff <ratio> [idx]", cmd_mouth_puff, "mouth"))
    
    # Penetration
    registry.register(Command("mouth_insert", ["mins", "feed"], "Insert object", "mouth_insert <name> [d] [l] [idx] [force]", cmd_mouth_insert, "mouth"))
    registry.register(Command("mouth_advance", ["madv"], "Advance deeper", "mouth_advance <depth> [idx]", cmd_mouth_advance, "mouth"))
    registry.register(Command("mouth_retract", ["mret"], "Retract", "mouth_retract <amount> [idx]", cmd_mouth_retract, "mouth"))
    registry.register(Command("mouth_remove", ["mrem"], "Remove object", "mouth_remove [idx]", cmd_mouth_remove, "mouth"))
    
    # Fluid
    registry.register(Command("mouth_add_fluid", ["mfluid"], "Add fluid", "mouth_add_fluid <type> <amount> [idx]", cmd_mouth_add_fluid, "mouth"))
    registry.register(Command("mouth_swallow", ["swallow"], "Swallow", "mouth_swallow [amount] [idx]", cmd_mouth_swallow, "mouth"))
    registry.register(Command("mouth_spit", ["spit"], "Spit out", "mouth_spit [idx]", cmd_mouth_spit, "mouth"))
    
    # Throat
    registry.register(Command("throat_open", ["topen"], "Open throat", "throat_open [idx] [amount]", cmd_throat_open, "mouth"))
    registry.register(Command("throat_relax", ["trelax"], "Relax throat", "throat_relax [idx]", cmd_throat_relax, "mouth"))
    registry.register(Command("throat_stretch", ["tstretch"], "Stretch throat", "throat_stretch <ratio> [idx]", cmd_throat_stretch, "mouth"))
    
    console.print("[dim]Mouth/Throat commands registered (16 commands)[/dim]")

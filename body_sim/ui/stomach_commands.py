# body_sim/ui/stomach_commands.py
"""
Команды для управления желудком.
Система инфляции, пищеварения, пенетрации с обоих концов.
"""

from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def _get_stomach(body, idx: int = 0):
    """Получить желудок по индексу."""
    if not body or not hasattr(body, 'stomach_system') or not body.stomach_system:
        return None, "No stomach system available"
    stomachs = body.stomach_system.stomachs
    if idx < 0 or idx >= len(stomachs):
        return None, f"Invalid stomach index: {idx} (max: {len(stomachs)-1})"
    return stomachs[idx], None


# ============ STATUS COMMANDS ============

def cmd_stomach_status(args: List[str], ctx) -> None:
    """Показать статус желудка."""
    idx = int(args[0]) if args else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    table = Table(show_header=True, box=box.ROUNDED, title=f"Stomach #{idx} Status")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("State", stomach.state.name)
    table.add_row("Digestion", stomach.digestion.name if hasattr(stomach, 'digestion') else "N/A")
    table.add_row("Fill Ratio", f"{stomach.fill_ratio:.1%}")
    table.add_row("Fluid", f"{stomach.mixture.total():.1f} ml")
    table.add_row("Solid", f"{stomach.solid_content:.1f} g" if hasattr(stomach, 'solid_content') else "0g")
    table.add_row("Volume", f"{stomach.filled:.1f} / {stomach.current_volume:.1f} ml")
    
    # Инфляция
    table.add_row("Inflation", f"{stomach.inflation_ratio:.2f}x")
    table.add_row("Wall Stretch", f"{stomach.walls.stretch_ratio:.2f}x" if hasattr(stomach, 'walls') else "N/A")
    table.add_row("Integrity", f"{stomach.walls.integrity:.2f}" if hasattr(stomach, 'walls') else "N/A")
    
    # Кардия
    if hasattr(stomach, 'cardia'):
        cardia = stomach.cardia
        table.add_row("Cardia State", cardia.state.name if hasattr(cardia, 'state') else "N/A")
        table.add_row("Cardia Open", "Yes" if cardia.is_open else "No")
    
    # Давление
    pressure = stomach.pressure() if hasattr(stomach, 'pressure') else 0
    table.add_row("Pressure", f"{pressure:.2f}")
    
    # Объект
    if stomach.inserted_object:
        obj = stomach.inserted_object
        table.add_row("[yellow]Object Inside[/yellow]", f"{getattr(obj, 'name', 'object')}")
        entry = "Mouth" if stomach.penetration_depth < stomach.base_length * stomach.inflation_ratio / 2 else "Anus"
        table.add_row("Entry Point", entry)
    
    console.print(table)


def cmd_stomach_fullness(args: List[str], ctx) -> None:
    """Детальное заполнение желудка."""
    idx = int(args[0]) if args else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    console.print(f"\n[bold cyan]Stomach #{idx} Fullness[/bold cyan]\n")
    
    fill = stomach.fill_ratio * 100
    bar = _make_bar(fill, 25)
    color = "green" if fill < 50 else "yellow" if fill < 80 else "red"
    console.print(f"[bold]Fill:[/bold]       [{color}]{bar}[/{color}] {fill:.0f}%")
    
    console.print(f"\n[dim]Capacity:[/dim]  {stomach.filled:.1f} / {stomach.current_volume:.1f} ml")
    console.print(f"[dim]Base:[/dim]      {stomach.base_volume} ml")
    
    # Состав
    if stomach.mixture.components:
        console.print(f"\n[bold]Fluid Composition:[/bold]")
        for fluid, amount in stomach.mixture.components.items():
            print(f"  {fluid.name}: {amount:.1f}ml")
    
    if stomach.solid_content > 0:
        console.print(f"\n[bold]Solid Food:[/bold] {stomach.solid_content:.1f}g")
    
    # Инфляция детали
    if hasattr(stomach, 'get_inflation_details'):
        info = stomach.get_inflation_details()
        console.print(f"\n[bold]Inflation:[/bold]")
        console.print(f"  Ratio: {info.get('uterus_ratio', stomach.inflation_ratio):.2f}x")
        console.print(f"  Total stretch: {info.get('total_stretch', 1.0):.2f}x")
        console.print(f"  Skin tension: {info.get('skin_tension', 0):.1%}")
        if info.get('is_permanent'):
            console.print("  [yellow]⚠️ Permanently stretched[/yellow]")


def _make_bar(pct: float, width: int = 20) -> str:
    filled = int((pct / 100) * width)
    return "█" * filled + "░" * (width - filled)


# ============ INFLATION COMMANDS ============

def cmd_stomach_inflate(args: List[str], ctx) -> None:
    """Инфлировать желудок."""
    if not args:
        console.print("[red]Usage: stomach_inflate <ratio> [idx][/red]")
        return
    
    ratio = float(args[0])
    idx = int(args[1]) if len(args) > 1 else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    success = stomach.inflate(ratio)
    if success:
        console.print(f"[bold magenta]Stomach #{idx} inflated to {ratio:.1f}x[/bold magenta]")
        if stomach.state.name in ["RUPTURE_RISK", "RUPTURED"]:
            console.print("[red]⚠️ DANGER: High rupture risk![/red]")
    else:
        console.print("[red]Cannot inflate - limit reached![/red]")


def cmd_stomach_deflate(args: List[str], ctx) -> None:
    """Дефлировать желудок."""
    idx = int(args[0]) if args else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(stomach, 'walls'):
        stomach.walls.recover(10.0)
    
    if stomach.inflation_ratio > 1.0:
        old = stomach.inflation_ratio
        new = max(1.0, old * 0.8)
        stomach.inflate(new)
        console.print(f"[green]Deflated: {old:.2f}x → {new:.2f}x[/green]")
    else:
        console.print("[dim]Already at normal size[/dim]")


# ============ FLUID COMMANDS ============

def cmd_stomach_add_fluid(args: List[str], ctx) -> None:
    """Добавить жидкость в желудок."""
    if len(args) < 2:
        console.print("[red]Usage: stomach_add_fluid <type> <amount> [idx][/red]")
        return
    
    fluid_name = args[0].upper()
    amount = float(args[1])
    idx = int(args[2]) if len(args) > 2 else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    try:
        from body_sim.core.enums import FluidType
        fluid_type = FluidType[fluid_name]
    except KeyError:
        console.print(f"[red]Unknown fluid: {fluid_name}[/red]")
        return
    
    added = stomach.add_fluid(fluid_type, amount)
    console.print(f"[cyan]Added {added:.1f}ml of {fluid_name} to stomach #{idx}[/cyan]")
    
    if added < amount:
        console.print(f"[yellow]⚠ {amount - added:.1f}ml overflowed (stomach full)[/yellow]")


def cmd_stomach_drain(args: List[str], ctx) -> None:
    """Опустошить желудок."""
    idx = int(args[0]) if args else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    removed = stomach.drain_all() if hasattr(stomach, 'drain_all') else {}
    total = sum(removed.values()) if isinstance(removed, dict) else removed
    
    console.print(f"[yellow]Drained {total:.1f}ml from stomach #{idx}[/yellow]")
    if isinstance(removed, dict):
        for fluid, amt in removed.items():
            console.print(f"  [dim]{fluid.name}: {amt:.1f}ml[/dim]")


def cmd_stomach_remove_fluid(args: List[str], ctx) -> None:
    """Удалить часть жидкости."""
    if not args:
        console.print("[red]Usage: stomach_remove <amount> [idx][/red]")
        return
    
    amount = float(args[0])
    idx = int(args[1]) if len(args) > 1 else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    removed = stomach.remove_fluid(amount)
    console.print(f"[yellow]Removed {removed:.1f}ml[/yellow]")


# ============ FOOD COMMANDS ============

def cmd_stomach_add_food(args: List[str], ctx) -> None:
    """Добавить твердую пищу."""
    if not args:
        console.print("[red]Usage: stomach_add_food <amount_grams> [idx][/red]")
        return
    
    amount = float(args[0])
    idx = int(args[1]) if len(args) > 1 else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(stomach, 'add_solid'):
        added = stomach.add_solid(amount)
        console.print(f"[green]Added {added:.1f}g of food[/green]")
    else:
        console.print("[red]Solid food not supported in this stomach[/red]")


# ============ PENETRATION COMMANDS ============

def cmd_stomach_object_remove(args: List[str], ctx) -> None:
    """Извлечь объект из желудка."""
    idx = int(args[0]) if args else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    obj = stomach.remove_object() if hasattr(stomach, 'remove_object') else None
    if obj:
        console.print(f"[green]Removed {getattr(obj, 'name', 'object')} from stomach[/green]")
        console.print("[dim]Exiting through entry point...[/dim]")
    else:
        console.print("[dim]No object inside[/dim]")


def cmd_stomach_advance_reverse(args: List[str], ctx) -> None:
    """Продвинуть объект от пилоруса к кардии (при пенетрации сзади)."""
    if not args:
        console.print("[red]Usage: stomach_advance_rev <depth> [idx][/red]")
        return
    
    depth = float(args[0])
    idx = int(args[1]) if len(args) > 1 else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(stomach, 'advance_object_reverse'):
        moved = stomach.advance_object_reverse(depth)
        console.print(f"[cyan]Moved {moved:.1f}cm toward cardia[/cyan]")
        if stomach.penetration_depth <= 0:
            console.print("[yellow]⚠️ Object reached cardia - can exit to esophagus![/yellow]")
    else:
        console.print("[red]Reverse movement not available[/red]")


# ============ CARDIA COMMANDS ============

def cmd_cardia_open(args: List[str], ctx) -> None:
    """Открыть кардию (вход с передней стороны)."""
    idx = int(args[0]) if args else 0
    amount = float(args[1]) if len(args) > 1 else 1.0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(stomach, 'cardia'):
        stomach.cardia.dilate(amount)
        console.print(f"[green]Cardia opened by {amount}cm[/green]")


def cmd_cardia_close(args: List[str], ctx) -> None:
    """Закрыть кардию."""
    idx = int(args[0]) if args else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(stomach, 'cardia'):
        stomach.cardia.contract()
        console.print("[green]Cardia closed[/green]")


# ============ SIMULATION COMMANDS ============

def cmd_stomach_tick(args: List[str], ctx) -> None:
    """Ручной тик желудка."""
    dt = float(args[0]) if args else 1.0
    idx = int(args[1]) if len(args) > 1 else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    result = stomach.tick(dt)
    console.print(f"[dim]Tick result: {result}[/dim]")


def cmd_stomach_digestion(args: List[str], ctx) -> None:
    """Установить скорость пищеварения."""
    if not args:
        console.print("[red]Usage: stomach_digestion <rate> [idx][/red]")
        return
    
    rate = float(args[0])
    idx = int(args[1]) if len(args) > 1 else 0
    
    stomach, error = _get_stomach(ctx.active_body, idx)
    if error:
        console.print(f"[red]{error}[/red]")
        return
    
    if hasattr(stomach, 'digestion_rate'):
        stomach.digestion_rate = max(0.0, min(5.0, rate))
        console.print(f"[cyan]Digestion rate set to {stomach.digestion_rate:.1f}x[/cyan]")


# ============ REGISTRATION ============

def register_stomach_commands(registry, console_instance=None):
    """Зарегистрировать команды желудка."""
    global console
    if console_instance:
        console = console_instance
    
    from body_sim.ui.commands import Command
    
    # Status
    registry.register(Command("stomach", ["stomach_status", "st"], "Show stomach status", "stomach [idx]", cmd_stomach_status, "stomach"))
    registry.register(Command("stomach_fullness", ["sfull"], "Stomach fullness", "stomach_fullness [idx]", cmd_stomach_fullness, "stomach"))
    
    # Inflation
    registry.register(Command("stomach_inflate", ["sinflate", "si"], "Inflate stomach", "stomach_inflate <ratio> [idx]", cmd_stomach_inflate, "stomach"))
    registry.register(Command("stomach_deflate", ["sdeflate", "sd"], "Deflate stomach", "stomach_deflate [idx]", cmd_stomach_deflate, "stomach"))
    
    # Fluid
    registry.register(Command("stomach_add_fluid", ["sfluid"], "Add fluid", "stomach_add_fluid <type> <amount> [idx]", cmd_stomach_add_fluid, "stomach"))
    registry.register(Command("stomach_drain", ["sdrain"], "Drain stomach", "stomach_drain [idx]", cmd_stomach_drain, "stomach"))
    registry.register(Command("stomach_remove", ["sremove"], "Remove fluid amount", "stomach_remove <amount> [idx]", cmd_stomach_remove_fluid, "stomach"))
    
    # Food
    registry.register(Command("stomach_food", ["sfood"], "Add solid food", "stomach_food <grams> [idx]", cmd_stomach_add_food, "stomach"))
    
    # Penetration
    registry.register(Command("stomach_remove_obj", ["sremobj"], "Remove object", "stomach_remove_obj [idx]", cmd_stomach_object_remove, "stomach"))
    registry.register(Command("stomach_advance_rev", ["sadvrev"], "Advance reverse (from anus)", "stomach_advance_rev <depth> [idx]", cmd_stomach_advance_reverse, "stomach"))
    
    # Cardia
    registry.register(Command("cardia_open", ["copen"], "Open cardia", "cardia_open [idx] [amount]", cmd_cardia_open, "stomach"))
    registry.register(Command("cardia_close", ["cclose"], "Close cardia", "cardia_close [idx]", cmd_cardia_close, "stomach"))
    
    # Simulation
    registry.register(Command("stomach_tick", ["stick"], "Manual tick", "stomach_tick [dt] [idx]", cmd_stomach_tick, "stomach"))
    registry.register(Command("stomach_digestion", ["sdigest"], "Set digestion rate", "stomach_digestion <rate> [idx]", cmd_stomach_digestion, "stomach"))
    
    console.print("[dim]Stomach commands registered (16 commands)[/dim]")

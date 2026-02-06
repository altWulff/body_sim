# body_sim/ui/commands.py
"""
Регистрация и обработка консольных команд.
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from body_sim.core.enums import FluidType, CupSize, InsertableType
from body_sim.systems.insertion import (
    create_plug, create_tube, create_balloon, 
    create_beads, create_egg, create_vibrator
)
from body_sim.characters.roxy_migurdia import register_roxy_command
from body_sim.characters.breast_reactions import get_reaction_system, register_reaction_commands

console = Console()


@dataclass
class Command:
    name: str
    aliases: List[str]
    description: str
    usage: str
    handler: Callable
    category: str = "general"


class CommandRegistry:
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.aliases: Dict[str, str] = {}

    def register(self, cmd: Command) -> None:
        self.commands[cmd.name] = cmd
        for alias in cmd.aliases:
            self.aliases[alias] = cmd.name

    def get(self, name: str) -> Optional[Command]:
        if name in self.commands:
            return self.commands[name]
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        return None

    def execute(self, line: str, context: 'CommandContext') -> bool:
        parts = line.strip().split()
        if not parts:
            return False

        cmd_name = parts[0].lower()
        args = parts[1:]

        cmd = self.get(cmd_name)
        if cmd:
            try:
                cmd.handler(args, context)
                return True
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                return True

        return False

    def get_help(self, category: Optional[str] = None) -> Table:
        table = Table(show_header=True, box="round")
        table.add_column("Command", style="bold cyan")
        table.add_column("Aliases", style="dim")
        table.add_column("Usage")
        table.add_column("Description")

        for cmd in self.commands.values():
            if category and cmd.category != category:
                continue
            alias_str = ", ".join(cmd.aliases) if cmd.aliases else "—"
            table.add_row(cmd.name, alias_str, cmd.usage, cmd.description)

        return table


@dataclass
class CommandContext:
    bodies: List[Any]
    active_body_idx: int = 0
    running: bool = True
    last_result: Any = None

    @property
    def active_body(self):
        if 0 <= self.active_body_idx < len(self.bodies):
            return self.bodies[self.active_body_idx]
        return None

    def next_body(self):
        if self.bodies:
            self.active_body_idx = (self.active_body_idx + 1) % len(self.bodies)

    def prev_body(self):
        if self.bodies:
            self.active_body_idx = (self.active_body_idx - 1) % len(self.bodies)

    def select_body(self, idx: int):
        if 0 <= idx < len(self.bodies):
            self.active_body_idx = idx


# ============ Обработчики команд ============

def cmd_help(args: List[str], ctx: CommandContext):
    """Показать справку."""
    registry = ctx.registry if hasattr(ctx, 'registry') else None
    if registry:
        console.print(Panel(registry.get_help(), title="[bold]Available Commands[/bold]"))

def cmd_quit(args: List[str], ctx: CommandContext):
    """Выйти из программы."""
    ctx.running = False
    console.print("[yellow]Goodbye![/yellow]")

def cmd_list(args: List[str], ctx: CommandContext):
    """Список всех тел."""
    from .rich_render import render_body_list
    console.print(render_body_list(ctx.bodies, ctx.active_body_idx))

def cmd_select(args: List[str], ctx: CommandContext):
    """Выбрать тело по индексу."""
    if not args:
        console.print("[red]Usage: select <index>[/red]")
        return
    try:
        idx = int(args[0])
        ctx.select_body(idx)
        console.print(f"[green]Selected body #{idx}: {ctx.active_body.name}[/green]")
    except ValueError:
        console.print("[red]Invalid index[/red]")

def cmd_next(args: List[str], ctx: CommandContext):
    """Следующее тело."""
    ctx.next_body()
    console.print(f"[green]Switched to: {ctx.active_body.name}[/green]")

def cmd_prev(args: List[str], ctx: CommandContext):
    """Предыдущее тело."""
    ctx.prev_body()
    console.print(f"[green]Switched to: {ctx.active_body.name}[/green]")

def cmd_show(args: List[str], ctx: CommandContext):
    """Показать детали активного тела."""
    from .rich_render import render_full_body
    if ctx.active_body:
        console.print(render_full_body(ctx.active_body))
        
    else:
        console.print("[red]No body selected[/red]")

def cmd_stimulate(args: List[str], ctx: CommandContext):
    """Стимулировать часть тела."""
    if not ctx.active_body:
        console.print("[red]No body selected[/red]")
        return

    if len(args) < 1:
        console.print("[red]Usage: stimulate <region> [index] [intensity][/red]")
        console.print("Regions: penis, clitoris, vagina, anus, breasts")
        return

    region = args[0]
    index = int(args[1]) if len(args) > 1 else 0
    intensity = float(args[2]) if len(args) > 2 else 0.3

    try:
        ctx.active_body.stimulate(region, index, intensity)
        console.print(f"[magenta]Stimulated {region} #{index} with intensity {intensity}[/magenta]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def cmd_tick(args: List[str], ctx: CommandContext):
    """Обновить симуляцию."""
    dt = float(args[0]) if args else 1.0

    for body in ctx.bodies:
        body.tick(dt)

    console.print(f"[green]Ticked {len(ctx.bodies)} bodies (dt={dt})[/green]")

def cmd_add_fluid(args: List[str], ctx: CommandContext):
    """Добавить жидкость в грудь."""
    if not ctx.active_body or not ctx.active_body.has_breasts:
        console.print("[red]No breasts available[/red]")
        return

    if len(args) < 2:
        console.print("[red]Usage: add_fluid <fluid_type> <amount> [row] [col][/red]")
        console.print("Types: milk, cum, water, honey, oil, custom")
        return

    fluid_name = args[0].upper()
    amount = float(args[1])
    row = int(args[2]) if len(args) > 2 else 0
    col = int(args[3]) if len(args) > 3 else 0

    try:
        fluid_type = FluidType[fluid_name]
        breast = ctx.active_body.breast_grid.get(row, col)
        added = breast.add_fluid(fluid_type, amount)
        console.print(f"[cyan]Added {added:.1f}ml of {fluid_name} to breast [{row},{col}][/cyan]")
    except (KeyError, IndexError) as e:
        console.print(f"[red]Error: {e}[/red]")

def cmd_drain(args: List[str], ctx: CommandContext):
    """Слить жидкость из груди."""
    if not ctx.active_body or not ctx.active_body.has_breasts:
        console.print("[red]No breasts available[/red]")
        return

    percentage = float(args[0]) if args else 100.0
    result = ctx.active_body.breast_grid.drain_all(percentage)
    console.print(f"[cyan]Drained {result['total_removed']:.1f}ml ({percentage}%)[/cyan]")

def cmd_lactation(args: List[str], ctx: CommandContext):
    """Управление лактацией."""
    if not ctx.active_body or not ctx.active_body.has_breasts:
        console.print("[red]No breasts available[/red]")
        return

    if not args:
        # Показать статус
        for r_idx, row in enumerate(ctx.active_body.breast_grid.rows):
            for c_idx, breast in enumerate(row):
                state = breast.lactation.state.name
                console.print(f"[{r_idx},{c_idx}] Lactation: {state}")
        return

    action = args[0].lower()
    row = int(args[1]) if len(args) > 1 else 0
    col = int(args[2]) if len(args) > 2 else 0

    breast = ctx.active_body.breast_grid.get(row, col)

    if action == "start":
        breast.lactation.start()
        console.print(f"[green]Started lactation for breast [{row},{col}][/green]")
    elif action == "stop":
        breast.lactation.stop()
        console.print(f"[yellow]Stopped lactation for breast [{row},{col}][/yellow]")
    elif action == "stimulate":
        breast.lactation.stimulate()
        console.print(f"[magenta]Stimulated lactation for breast [{row},{col}][/magenta]")

def cmd_insert(args: List[str], ctx: CommandContext):
    """Вставить предмет в грудь."""
    if not ctx.active_body or not ctx.active_body.has_breasts:
        console.print("[red]No breasts available[/red]")
        return

    if len(args) < 2:
        console.print("[red]Usage: insert <object_type> <row> [col] [diameter][/red]")
        console.print("Types: plug, tube, balloon, beads, egg, vibrator")
        return

    obj_type = args[0].lower()
    row = int(args[1])
    col = int(args[2]) if len(args) > 2 else 0
    diameter = float(args[3]) if len(args) > 3 else 1.0

    breast = ctx.active_body.breast_grid.get(row, col)

    creators = {
        "plug": create_plug,
        "tube": create_tube,
        "balloon": create_balloon,
        "beads": create_beads,
        "egg": create_egg,
        "vibrator": create_vibrator,
    }

    if obj_type not in creators:
        console.print(f"[red]Unknown object type: {obj_type}[/red]")
        return

    obj = creators[obj_type](diameter=diameter)

    # Проверяем, помещается ли через сосок
    nipple = breast.areola.nipples[0] if breast.areola.nipples else None
    if nipple and not obj.can_fit_through(nipple.gape_diameter):
        console.print(f"[yellow]Warning: Object may not fit through nipple (gape: {nipple.gape_diameter:.2f}cm)[/yellow]")

    success = breast.insertion_manager.insert(obj)
    if success:
        console.print(f"[green]Inserted {obj.name} ({obj.volume_ml:.1f}ml) into breast [{row},{col}][/green]")
    else:
        console.print(f"[red]Failed to insert (max {breast.insertion_manager.max_objects} objects)[/red]")

def cmd_remove(args: List[str], ctx: CommandContext):
    """Извлечь предмет из груди."""
    if not ctx.active_body or not ctx.active_body.has_breasts:
        console.print("[red]No breasts available[/red]")
        return

    row = int(args[0]) if args else 0
    col = int(args[1]) if len(args) > 1 else 0
    obj_idx = int(args[2]) if len(args) > 2 else 0

    breast = ctx.active_body.breast_grid.get(row, col)
    obj = breast.insertion_manager.remove(obj_idx)

    if obj:
        console.print(f"[green]Removed {obj.name} from breast [{row},{col}][/green]")
    else:
        console.print(f"[red]No object at index {obj_idx}[/red]")

def cmd_ejaculate(args: List[str], ctx: CommandContext):
    """Эякуляция."""
    if not ctx.active_body or not ctx.active_body.has_penis:
        console.print("[red]No penis available[/red]")
        return

    penis_idx = int(args[0]) if args else 0
    force = float(args[1]) if len(args) > 1 else 1.0

    result = ctx.active_body.ejaculate(penis_idx, force)
    if result["success"]:
        console.print(f"[cyan]Ejaculated {result['amount']:.1f}ml from penis #{penis_idx}[/cyan]")
    else:
        console.print(f"[red]Ejaculation failed: {result.get('reason', 'unknown')}[/red]")

def cmd_penetration(args: List[str], ctx: CommandContext):
    """Проникновение."""
    if not ctx.active_body:
        console.print("[red]No body selected[/red]")
        return

    if len(args) < 2:
        console.print("[red]Usage: penetrate <target> <target_idx> [penis_idx][/red]")
        console.print("Targets: vagina, anus")
        return

    target = args[0]
    target_idx = int(args[1])
    penis_idx = int(args[2]) if len(args) > 2 else 0

    success = ctx.active_body.penetrate(target, target_idx, penis_idx)
    if success:
        console.print(f"[magenta]Penetrated {target} #{target_idx} with penis #{penis_idx}[/magenta]")
    else:
        console.print(f"[red]Penetration failed[/red]")

def cmd_create_body(args: List[str], ctx: CommandContext):
    """Создать новое тело."""
    from body_sim.body.factory import BodyFactory

    if not args:
        console.print("[red]Usage: create <male|female|futa> [name][/red]")
        return

    sex_type = args[0].lower()
    name = args[1] if len(args) > 1 else f"New_{sex_type}"

    try:
        body = BodyFactory.quick_create(sex_type, name)
        ctx.bodies.append(body)
        console.print(f"[green]Created {sex_type} body: {name}[/green]")
    except Exception as e:
        console.print(f"[red]Error creating body: {e}[/red]")


# ============ Создание реестра команд ============

def create_registry() -> CommandRegistry:
    registry = CommandRegistry()

    # General
    registry.register(Command("help", ["h", "?"], "Show help", "help", cmd_help, "general"))
    registry.register(Command("quit", ["q", "exit"], "Exit program", "quit", cmd_quit, "general"))
    registry.register(Command("list", ["ls", "bodies"], "List all bodies", "list", cmd_list, "general"))
    registry.register(Command("select", ["sel"], "Select body by index", "select <idx>", cmd_select, "general"))
    registry.register(Command("next", ["n"], "Next body", "next", cmd_next, "general"))
    registry.register(Command("prev", ["p"], "Previous body", "prev", cmd_prev, "general"))
    registry.register(Command("show", ["s", "status"], "Show body details", "show", cmd_show, "general"))
    registry.register(Command("tick", ["t", "update"], "Update simulation", "tick [dt]", cmd_tick, "general"))
    registry.register(Command("create", ["new"], "Create new body", "create <type> [name]", cmd_create_body, "general"))

    # Stimulation
    registry.register(Command("stimulate", ["stim"], "Stimulate body part", "stimulate <region> [idx] [intensity]", cmd_stimulate, "stimulation"))

    # Breasts
    registry.register(Command("add_fluid", ["add", "fill"], "Add fluid to breast", "add_fluid <type> <amount> [row] [col]", cmd_add_fluid, "breasts"))
    registry.register(Command("drain", ["empty"], "Drain breast fluid", "drain [percentage]", cmd_drain, "breasts"))
    registry.register(Command("lactation", ["lact"], "Control lactation", "lactation [start|stop|stimulate] [row] [col]", cmd_lactation, "breasts"))
    registry.register(Command("insert", ["ins"], "Insert object into breast", "insert <type> <row> [col] [diameter]", cmd_insert, "breasts"))
    registry.register(Command("remove", ["rm"], "Remove object from breast", "remove <row> [col] [obj_idx]", cmd_remove, "breasts"))

    # Genitals
    registry.register(Command("penetrate", ["pen"], "Penetrate orifice", "penetrate <target> <idx> [penis_idx]", cmd_penetration, "genitals"))
    registry.register(Command("ejaculate", ["ejac", "cum"], "Ejaculate", "ejaculate [penis_idx] [force]", cmd_ejaculate, "genitals"))
    
    register_roxy_command(registry)
    register_reaction_commands(registry, get_reaction_system())

    return registry

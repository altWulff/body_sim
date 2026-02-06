# body_sim/ui/commands.py
"""
Регистрация и обработка консольных команд.
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box  # Импортируем box модули

from body_sim.characters.roxy_migurdia import register_roxy_command

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
        """Зарегистрировать команду."""
        if not isinstance(cmd, Command):
            raise TypeError(f"Expected Command, got {type(cmd)}")
        self.commands[cmd.name] = cmd
        for alias in cmd.aliases:
            self.aliases[alias] = cmd.name

    def get(self, name: str) -> Optional[Command]:
        """Получить команду по имени или алиасу."""
        if name in self.commands:
            return self.commands[name]
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        return None

    def execute(self, line: str, context: 'CommandContext') -> bool:
        """Выполнить команду."""
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
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/dim]")
                return True

        return False

    def get_help(self, category: Optional[str] = None) -> Table:
        """Получить таблицу помощи."""
        table = Table(show_header=True, box=box.ROUNDED)
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
    registry: 'CommandRegistry' = None  # Добавлено для доступа к реестру

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
    if not ctx.registry:
        console.print("[red]Registry not available[/red]")
        return

    if not args:
        # Общая справка по категориям
        console.print(Panel(ctx.registry.get_help(), title="[bold]Available Commands[/bold]"))
        console.print("\n[dim]Type 'help <category>' for detailed help:[/dim]")
        console.print("  [cyan]help uterus[/cyan] - Uterus, ovaries, tubes commands")
        console.print("  [cyan]help breasts[/cyan] - Breast and lactation commands")
        console.print("  [cyan]help genitals[/cyan] - Genitals and penetration commands")
        console.print("  [cyan]help general[/cyan] - General commands")
        return

    topic = args[0].lower()

    if topic == "uterus":
        help_text = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║           UTERUS / OVARIES / FALLOPIAN TUBES                 ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]🌸 UTERUS COMMANDS (uterus / ut / womb)[/bold yellow]

  [green]uterus[/green]                    - Show full uterus system status
  [green]uterus status [idx][/green]       - Detailed view of specific uterus
  [green]uterus add_fluid <type> <amount> [idx][/green]
                            - Add fluid (milk, cum, water, honey, oil)
  [green]uterus drain [idx][/green]       - Remove all fluids
  [green]uterus dilate [amount][/green]  - Dilate cervix (cm)
  [green]uterus contract[/green]         - Contract cervix
  [green]uterus insert <object>[/green]  - Insert object (egg, ball, beads, speculum)
  [green]uterus remove [idx][/green]     - Remove object by index

[bold red]⚠️ PROLAPSE & EVERSION COMMANDS[/bold red]

  [green]uterus strain [force][/green]     - Apply strain (0.0-1.0), risk of prolapse
  [green]uterus evert[/green]            - [red]FORCE COMPLETE EVERSION[/red]
                            (ejects all contents, tubes visible externally)
  [green]uterus invert[/green]           - Invert uterus (internal, tubes visible inside)
  [green]uterus reduce [amount][/green]    - Try to reduce prolapse (manual reposition)

[bold yellow]🥚 OVARY COMMANDS (ovary / ov / ovaries)[/bold yellow]

  [green]ovary[/green]                    - Show all ovaries
  [green]ovary status <side>[/green]     - Show specific ovary (left/right)
  [green]ovary enlarge [amt] [side][/green] - Enlarge follicles
  [green]ovary rupture [idx] [side][/green] - Rupture follicle (ovulation)
  [green]ovary ovulate [idx] [side][/green] - Trigger ovulation

[bold red]⚠️ OVARY PROLAPSE[/bold red]

  [green]ovary evert [deg] [side][/green]  - [red]EVERT OVARY externally[/red]
  [green]ovary reposition [amt] [side][/green] - Try to reposition ovary

[bold yellow]🌊 FALLOPIAN TUBE COMMANDS (tube / ft / tubes)[/bold yellow]

  [green]tube[/green]                     - Show all tubes
  [green]tube status <side>[/green]      - Show specific tube
  [green]tube stretch <ratio> [side][/green] - Stretch tube (1.0-3.0x)
  [green]tube add_fluid <amt> [side][/green] - Add fluid to tube
  [green]tube clear [side][/green]       - Clear tube contents

[bold red]⚠️ TUBE EVERSION (requires stretched tube + visible openings)[/bold red]

  [green]tube evert <side>[/green]       - [red]EVERT TUBE WITH OVARY[/red]
                            (requires: uterus inverted/everted + stretch >2.0)
  [green]tube reposition [side][/green]  - Reposition tube

[bold magenta]╔══════════════════════════════════════════════════════════════╗[/bold magenta]
[bold magenta]║                    MECHANICS GUIDE                           ║[/bold magenta]
[bold magenta]╚══════════════════════════════════════════════════════════════╝[/bold magenta]

[yellow]Prolapse Risk Factors:[/yellow]
  • Weak ligaments (ligament_integrity)
  • Weak pelvic floor
  • Overstretched walls
  • High internal pressure (fluids/objects)
  • Tissue fatigue

[yellow]Eversion Requirements:[/yellow]
  1. Uterus must be in EVERTED or INVERTED state
  2. Fallopian tubes must be stretched (>2.0x)
  3. Then: [cyan]tube evert <side>[/cyan] to pull ovary out

[yellow]States:[/yellow]
  • NORMAL → DESCENDED → PROLAPSED → [red]EVERTED[/red]
  • INVERTED (special state, tubes visible internally)

[yellow]Ovary States:[/yellow]
  • NORMAL → ENLARGED → PROLAPSED → [red]EVERTED[/red] → TORSION (ischemia!)
        """
        console.print(Panel(help_text, title="[bold]Uterus System Help[/bold]", border_style="bright_magenta"))

    elif topic == "breasts":
        help_text = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║                    BREAST COMMANDS                           ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]🍼 BASIC COMMANDS[/bold yellow]

  [green]add_fluid <type> <amount> [row] [col][/green]
                            - Add fluid to breast
  [green]drain [percentage][/green]      - Drain fluid from all breasts
  [green]lactation[/green]               - Show lactation status
  [green]lactation start [r] [c][/green] - Start lactation
  [green]lactation stop [r] [c][/green]  - Stop lactation
  [green]lactation stimulate [r] [c][/green] - Stimulate lactation

[bold yellow]📦 INSERTION SYSTEM[/bold yellow]

  [green]insert <type> <row> [col] [diameter][/green]
                            - Insert object into breast
                            Types: plug, tube, balloon, beads, egg, vibrator
  [green]remove <row> [col] [obj_idx][/green]
                            - Remove object from breast

[bold magenta]States:[/bold magenta] EMPTY → NORMAL → TENSE → [red]OVERPRESSURED[/red] → [blue]LEAKING[/blue]
        """
        console.print(Panel(help_text, title="[bold]Breast System Help[/bold]", border_style="bright_cyan"))

    elif topic == "genitals":
        help_text = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║                   GENITAL COMMANDS                           ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]🔥 STIMULATION[/bold yellow]

  [green]stimulate <region> [idx] [intensity][/green]
                            - Stimulate body part
                            Regions: penis, clitoris, vagina, anus, breasts

[bold yellow]🔞 PENETRATION & EJACULATION[/bold yellow]

  [green]penetrate <target> <idx> [penis_idx][/green]
                            - Penetrate orifice
                            Targets: vagina, anus
  [green]ejaculate [penis_idx] [force][/green]
                            - Ejaculate from penis

[bold magenta]Penis Types:[/bold magenta] human, knotted, tapered, flared, barbed, double,
              prehensile, equine, canine, feline, dragon, demon,
              tentacle, horseshoe, spiral, ribbed, bifurcated

[bold magenta]Vagina Types:[/bold magenta] human, sinuous, deepcave, ribbed, tentacled,
               demonic, plant, slime
        """
        console.print(Panel(help_text, title="[bold]Genitals Help[/bold]", border_style="bright_red"))

    elif topic == "general":
        help_text = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║                   GENERAL COMMANDS                           ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]🎮 CONTROL[/bold yellow]

  [green]help [topic][/green]            - Show help (topics: uterus, breasts, genitals)
  [green]quit / q / exit[/green]       - Exit program
  [green]tick [dt][/green]             - Update simulation (time delta)

[bold yellow]👤 BODY MANAGEMENT[/bold yellow]

  [green]list / ls / bodies[/green]    - List all bodies
  [green]select <idx> / sel[/green]    - Select body by index
  [green]next / n[/green]              - Next body
  [green]prev / p[/green]              - Previous body
  [green]show / s / status[/green]     - Show active body details
  [green]create <type> [name][/green]  - Create new body (male/female/futa)
  [green]roxy / migurdia[/green]       - Create Roxy Migurdia character

[bold yellow]📊 DISPLAY[/bold yellow]

  Use [cyan]show[/cyan] command to see full body status including:
  • Body stats (arousal, pleasure, pain, fatigue)
  • Breast grid with fill levels
  • Genitals status
  • Uterus system (if present)
        """
        console.print(Panel(help_text, title="[bold]General Commands Help[/bold]", border_style="bright_green"))

    else:
        console.print(f"[yellow]Unknown help topic: {topic}[/yellow]")
        console.print("[dim]Available topics: uterus, breasts, genitals, general[/dim]")
        console.print("[dim]Or use 'help' without arguments for command list[/dim]")




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
        console.print(f"[green]Selected body #{idx}: {ctx.active_body.name if ctx.active_body else 'none'}[/green]")
    except ValueError:
        console.print("[red]Invalid index[/red]")


def cmd_next(args: List[str], ctx: CommandContext):
    """Следующее тело."""
    ctx.next_body()
    console.print(f"[green]Switched to: {ctx.active_body.name if ctx.active_body else 'none'}[/green]")


def cmd_prev(args: List[str], ctx: CommandContext):
    """Предыдущее тело."""
    ctx.prev_body()
    console.print(f"[green]Switched to: {ctx.active_body.name if ctx.active_body else 'none'}[/green]")


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

    if len(args) < 1:
        console.print("[red]Usage: add_fluid <fluid_type> <amount> [row] [col][/red]")
        console.print("Types: milk, cum, water, honey, oil, custom")
        return

    fluid_name = args[0].upper()
    amount = float(args[1])
    row = int(args[2]) if len(args) > 2 else 0
    col = int(args[3]) if len(args) > 3 else 0

    try:
        from body_sim.core.enums import FluidType
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
                state = breast.lactation.state.name if hasattr(breast.lactation.state, 'name') else str(breast.lactation.state)
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

    if len(args) < 1:
        console.print("[red]Usage: insert <object_type> <row> [col] [diameter][/red]")
        console.print("Types: plug, tube, balloon, beads, egg, vibrator")
        return

    obj_type = args[0].lower()
    row = int(args[1])
    col = int(args[2]) if len(args) > 2 else 0
    diameter = float(args[3]) if len(args) > 3 else 1.0

    breast = ctx.active_body.breast_grid.get(row, col)

    from body_sim.systems.insertion import (
        create_plug, create_tube, create_balloon, 
        create_beads, create_egg, create_vibrator
    )

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

    if len(args) < 1:
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


def cmd_create_roxy(args: List[str], ctx: CommandContext):
    """Создать Рокси Мигурдию."""
    try:
        from body_sim.characters.roxy_migurdia import create_roxy
        roxy = create_roxy()
        ctx.bodies.append(roxy)
        console.print(f"[bold cyan]Created {roxy.name} - Migurdian Mage![/bold cyan]")
        console.print(f"[dim]{roxy.character_info['age_real']} years old, appears {roxy.character_info['age_appearance']}[/dim]")
        console.print(f"[blue]Hair:[/blue] Blue | [red]Eyes:[/red] Achromatic crimson | [magenta]Chest:[/magenta] {roxy.breast_cup}-cup")
    except Exception as e:
        console.print(f"[red]Error creating Roxy: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")




def cmd_uterus(args: List[str], ctx: CommandContext):
    """Управление маткой (uterus)."""
    if not ctx.active_body:
        console.print("[red]No body selected[/red]")
        return

    if not hasattr(ctx.active_body, 'uterus_system') or not ctx.active_body.uterus_system:
        console.print("[red]No uterus available[/red]")
        return

    system = ctx.active_body.uterus_system

    if not args:
        # Показать статус
        from body_sim.ui.uterus_render import UterusRenderer
        renderer = UterusRenderer()
        console.print(renderer.render_full_system(system))
        return

    # Отладка
    console.print(f"[dim]DEBUG: args={args}[/dim]")

    action = args[0].lower()

    # Убираем action из args (создаем копию!)
    args = list(args[1:])

    console.print(f"[dim]DEBUG: action={action}, args after pop={args}[/dim]")

    # Определяем индекс матки - только если последний аргумент число 0-9
    uterus_idx = 0
    if args:
        try:
            potential_idx = int(args[-1])
            if 0 <= potential_idx <= 9 and len(system.uteri) > potential_idx:
                uterus_idx = potential_idx
                args = args[:-1]  # Удаляем индекс из args
        except ValueError:
            pass  # Последний аргумент не число, используем индекс 0

    if uterus_idx >= len(system.uteri):
        console.print(f"[red]Invalid uterus index: {uterus_idx}[/red]")
        return

    uterus = system.uteri[uterus_idx]

    if action == "status":
        from body_sim.ui.uterus_render import UterusRenderer
        renderer = UterusRenderer()
        console.print(renderer.render_uterus_detailed(uterus, f"Uterus #{uterus_idx}"))

    elif action == "add_fluid":
        if len(args) < 2:
            console.print("[red]Usage: uterus add_fluid <type> <amount> [idx][/red]")
            return
        from body_sim.core.enums import FluidType
        fluid_type = FluidType[args[0].upper()]
        amount = float(args[1])
        added = uterus.add_fluid(fluid_type, amount)
        console.print(f"[cyan]Added {added:.1f}ml of {args[0].upper()} to uterus #{uterus_idx}[/cyan]")

    elif action == "drain":
        removed = uterus.remove_fluid()
        total = sum(removed.values())
        console.print(f"[yellow]Drained {total:.1f}ml from uterus #{uterus_idx}[/yellow]")

    elif action == "dilate":
        amount = float(args[0]) if args else 1.0
        uterus.cervix.dilate(amount)
        console.print(f"[magenta]Dilated cervix to {uterus.cervix.current_dilation:.1f}cm[/magenta]")

    elif action == "contract":
        uterus.cervix.contract()
        console.print("[green]Cervix contracted[/green]")

    elif action == "strain":
        force = float(args[0]) if args else 0.5
        result = uterus.apply_strain(force)
        if result:
            console.print(f"[red]⚠️ Prolapse progressed! State: {uterus.state.name}[/red]")
        else:
            console.print("[green]Strain applied, no prolapse[/green]")

    elif action == "evert":
        if uterus.state != UterusState.EVERTED:
            uterus._complete_eversion()
            console.print(f"[bold red]🔴 UTERUS EVERTED! All contents ejected.[/bold red]")
        else:
            console.print("[yellow]Already everted[/yellow]")

    elif action == "reduce":
        amount = float(args[0]) if args else 0.5
        success = uterus.reduce_prolapse(amount)
        if success:
            console.print(f"[green]Prolapse reduced. State: {uterus.state.name}[/green]")
        else:
            console.print("[red]Failed to reduce - requires medical intervention[/red]")

    elif action == "invert":
        force = float(args[0]) if args else 1.0
        success = uterus.invert(force)
        if success:
            console.print(f"[red]Uterus inverted! Tube openings visible internally.[/red]")
        else:
            console.print("[red]Cannot invert - uterus not in normal state[/red]")

    elif action == "insert":
        if not args:
            console.print("[red]Usage: uterus insert <object_type>[/red]")
            return
        obj_type = args[0].lower()
        # Создаем простой объект для вставки
        class SimpleObject:
            def __init__(self, name, volume, diameter):
                self.name = name
                self.volume = volume
                self.effective_volume = volume
                self.diameter = diameter
                self.is_inserted = False

        objects = {
            "egg": SimpleObject("Egg", 5.0, 2.0),
            "ball": SimpleObject("Ball", 10.0, 3.0),
            "beads": SimpleObject("Beads", 15.0, 2.5),
            "speculum": SimpleObject("Speculum", 20.0, 4.0),
        }

        if obj_type not in objects:
            console.print(f"[red]Unknown object: {obj_type}[/red]")
            return

        obj = objects[obj_type]
        success = uterus.insert_object(obj)
        if success:
            console.print(f"[green]Inserted {obj.name} into uterus #{uterus_idx}[/green]")
        else:
            console.print("[red]Failed to insert - cervix closed or no space[/red]")

    elif action == "remove":
        idx = int(args[0]) if args else 0
        obj = uterus.remove_object(idx)
        if obj:
            console.print(f"[green]Removed {obj.name} from uterus[/green]")
        else:
            console.print("[red]No object at that index[/red]")

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Actions: status, add_fluid, drain, dilate, contract, strain, evert, reduce, invert, insert, remove")

def cmd_ovary(args: List[str], ctx: CommandContext):
    """Управление яичниками (ovaries)."""
    if not ctx.active_body:
        console.print("[red]No body selected[/red]")
        return

    if not hasattr(ctx.active_body, 'uterus_system') or not ctx.active_body.uterus_system:
        console.print("[red]No uterus system available[/red]")
        return

    system = ctx.active_body.uterus_system

    if not args:
        # Показать все яичники
        from body_sim.ui.ovary_tube_render import OvaryTubeRenderer
        renderer = OvaryTubeRenderer()

        for uterus in system.uteri:
            for ovary in uterus.ovaries:
                if ovary:
                    console.print(renderer.render_ovary_detailed(ovary))
        return

    action = args[0].lower()

    # Убираем action из args
    args = args[1:]

    # Определяем side и uterus_idx
    side = "left"
    uterus_idx = 0

    # Проверяем последний аргумент на индекс матки (0-9)
    if args:
        try:
            potential_idx = int(args[-1])
            if 0 <= potential_idx <= 9 and len(system.uteri) > potential_idx:
                uterus_idx = potential_idx
                args = args[:-1]
        except ValueError:
            pass

    # Проверяем первый аргумент на side
    if args:
        if args[0].lower() in ("left", "right"):
            side = args[0].lower()
            args = args[1:]

    if uterus_idx >= len(system.uteri):
        console.print(f"[red]Invalid uterus index[/red]")
        return

    uterus = system.uteri[uterus_idx]
    ovary = uterus.left_ovary if side == "left" else uterus.right_ovary

    if not ovary:
        console.print(f"[red]No {side} ovary found[/red]")
        return

    if action == "status":
        from body_sim.ui.ovary_tube_render import OvaryTubeRenderer
        renderer = OvaryTubeRenderer()
        console.print(renderer.render_ovary_detailed(ovary))

    elif action == "enlarge":
        amount = float(args[0]) if args else 0.3
        ovary.enlarge_follicles(amount)
        console.print(f"[yellow]Follicles enlarged on {side} ovary[/yellow]")

    elif action == "rupture":
        idx = int(args[0]) if args else 0
        success = ovary.rupture_follicle(idx)
        if success:
            console.print(f"[magenta]Follicle {idx} ruptured! Ovulation occurred.[/magenta]")
        else:
            console.print("[red]Failed to rupture follicle[/red]")

    elif action == "evert":
        degree = float(args[0]) if args else 1.0
        ovary.evert(degree)
        console.print(f"[bold red]🔴 {side.upper()} OVARY EVERTED![/bold red]")
        console.print(f"[red]Visible externally: {ovary.external_description}[/red]")

    elif action == "reposition":
        amount = float(args[0]) if args else 0.5
        success = ovary.reposition(amount)
        if success:
            console.print(f"[green]{side} ovary repositioned. State: {ovary.state.name}[/green]")
        else:
            console.print("[red]Failed to reposition - requires stronger intervention[/red]")

    elif action == "ovulate":
        follicle_idx = int(args[0]) if args else -1
        success = uterus.ovulate(side, follicle_idx)
        if success:
            if ovary.is_everted:
                console.print(f"[red]⚠️ External ovulation from {side} ovary![/red]")
            else:
                console.print(f"[cyan]Ovulation from {side} ovary - egg in fallopian tube[/cyan]")
        else:
            console.print("[red]Ovulation failed[/red]")

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Actions: status, enlarge, rupture, evert, reposition, ovulate")

def cmd_tube(args: List[str], ctx: CommandContext):
    """Управление фаллопиевыми трубами (fallopian tubes)."""
    if not ctx.active_body:
        console.print("[red]No body selected[/red]")
        return

    if not hasattr(ctx.active_body, 'uterus_system') or not ctx.active_body.uterus_system:
        console.print("[red]No uterus system available[/red]")
        return

    system = ctx.active_body.uterus_system

    if not args:
        # Показать все трубы
        from body_sim.ui.ovary_tube_render import OvaryTubeRenderer
        renderer = OvaryTubeRenderer()

        for uterus in system.uteri:
            for tube in uterus.tubes:
                if tube:
                    console.print(renderer.render_tube_detailed(tube))
        return

    action = args[0].lower()

    # Убираем action из args
    args = args[1:]

    # Определяем side и uterus_idx
    side = "left"
    uterus_idx = 0

    # Проверяем последний аргумент на индекс матки (0-9)
    if args:
        try:
            potential_idx = int(args[-1])
            if 0 <= potential_idx <= 9 and len(system.uteri) > potential_idx:
                uterus_idx = potential_idx
                args = args[:-1]
        except ValueError:
            pass

    # Проверяем первый аргумент на side
    if args:
        if args[0].lower() in ("left", "right"):
            side = args[0].lower()
            args = args[1:]

    if uterus_idx >= len(system.uteri):
        console.print(f"[red]Invalid uterus index[/red]")
        return

    uterus = system.uteri[uterus_idx]
    tube = uterus.left_tube if side == "left" else uterus.right_tube

    if not tube:
        console.print(f"[red]No {side} tube found[/red]")
        return

    if action == "status":
        from body_sim.ui.ovary_tube_render import OvaryTubeRenderer
        renderer = OvaryTubeRenderer()
        console.print(renderer.render_tube_detailed(tube))

    elif action == "stretch":
        ratio = float(args[0]) if args else 2.0
        success = tube.stretch(ratio)
        if success:
            console.print(f"[yellow]{side} tube stretched to ×{ratio:.1f}[/yellow]")
            if tube.can_prolapse_ovary:
                console.print("[red]⚠️ Ovary can now prolapse through this tube![/red]")
        else:
            console.print("[red]Tube blocked due to overstretching![/red]")

    elif action == "evert":
        if not tube.ovary:
            console.print("[red]No ovary attached to this tube[/red]")
            return

        if not uterus.tube_openings_visible:
            console.print("[red]Tube openings not visible - requires uterus inversion/eversion[/red]")
            return

        if tube.current_stretch < 2.0:
            console.print("[red]Tube not stretched enough (need 2.0x)[/red]")
            return

        tube.evert_with_ovary()
        console.print(f"[bold red]🔴 {side.upper()} TUBE EVERTED WITH OVARY![/bold red]")
        console.print(f"[red]External opening visible: {tube.external_description}[/red]")

    elif action == "reposition":
        tube.reposition()
        console.print(f"[green]{side} tube repositioned[/green]")

    elif action == "add_fluid":
        amount = float(args[0]) if args else 5.0
        tube.contained_fluid += amount
        console.print(f"[cyan]Added {amount:.1f}ml fluid to {side} tube[/cyan]")

    elif action == "clear":
        tube.contained_fluid = 0.0
        tube.contained_ovum = None
        console.print(f"[yellow]{side} tube cleared[/yellow]")

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Actions: status, stretch, evert, reposition, add_fluid, clear")

# ============ Создание реестра команд ============

def create_registry() -> CommandRegistry:
    """Создать и настроить реестр команд."""
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
    registry.register(Command("roxy", ["migurdia"], "Create Roxy Migurdia", "roxy", cmd_create_roxy, "characters"))

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
    # Uterus
    registry.register(Command("uterus", ["ut", "womb"], "Uterus management", "uterus [action] [args...]", cmd_uterus, "uterus"))

    # Ovaries
    registry.register(Command("ovary", ["ov", "ovaries"], "Ovary management", "ovary [action] [side] [args...]", cmd_ovary, "uterus"))

    # Fallopian tubes
    registry.register(Command("tube", ["ft", "tubes"], "Fallopian tube management", "tube [action] [side] [args...]", cmd_tube, "uterus"))


    register_roxy_command(registry)
    # Реакции (если доступны)
    try:
        from body_sim.characters.breast_reactions import get_reaction_system, register_reaction_commands
        register_reaction_commands(registry, get_reaction_system())
        console.print("[dim]Reaction commands loaded[/dim]")
    except ImportError as e:
        console.print(f"[dim]Reaction commands not available: {e}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to load reaction commands: {e}[/yellow]")

    return registry

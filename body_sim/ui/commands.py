# body_sim/ui/commands.py
"""
Регистрация и обработка консольных команд.
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from body_sim.anatomy.genitals import Penis


try:
    from magic import (
        MagicRenderer, 
        FluidRegenerationPerk, 
        OverfillCapacityPerk,
        PressureMasteryPerk, 
        SensitiveOrgansPerk,
        MilkSpray, LactationHeal, BreastShield,
        CumShot, VirilityBoost, SemenWeb,
        DualRelease, GenderFusion
    )
    from magic.skills.milk_skills import get_female_skills
    from magic.skills.cum_skills import get_male_skills
    from magic.skills.hybrid_skills import get_futanari_skills
    MAGIC_AVAILABLE = True
except ImportError as e:
    MAGIC_AVAILABLE = False
    print(f"[dim]Magic system not available: {e}[/dim]")

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
    registry: 'CommandRegistry' = None

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

    help_topics = {
        "uterus": """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║         UTERUS - INFLATION & FLUID SYSTEM                    ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]💧 FLUID COMMANDS[/bold yellow]

  [green]uterus[/green]                    - Show full uterus system status
  [green]uterus status [idx][/green]       - Detailed status with fluid distribution
  [green]uterus fullness [idx][/green]    - Show detailed fluid/objects distribution
  [green]uterus add_fluid <type> <amount> [idx][/green]
                            - Add fluid (auto-distributes to tubes/ovaries)
                            Types: milk, cum, water, honey, oil, blood
  [green]uterus drain [idx][/green]       - Drain ALL fluid from entire system
  [green]uterus remove <amount> [idx][/green]
                            - Remove specific amount from system

[bold yellow]🎈 INFLATION COMMANDS[/bold yellow]

  [green]uterus inflate <ratio> [idx][/green]
                            - Inflate uterus (1.0=normal, 2.0=2x size, max 4.0)
  [green]uterus deflate [idx][/green]     - Reduce inflation (recovery)
  [green]uterus inflation [idx][/green]   - Show inflation details
                            (skin tension, stretch marks risk, permanent stretch)

[bold magenta]Inflation Status Progression:[/bold magenta]
  NORMAL → STRETCHED → DISTENDED → HYPERDISTENDED → RUPTURE_RISK → RUPTURED

[bold yellow]🌊 FALLOPIAN TUBE COMMANDS[/bold yellow]

  [green]uterus tube_inflate <side> <ratio> [idx][/green]
                            - Inflate specific tube (left/right)
  [green]uterus tube_stretch <side> <ratio> [idx][/green]
                            - Stretch tube length
  [green]uterus tube_status [idx][/green]
                            - Show tube status (fluid, inflation, stretch)

[bold yellow]🥚 OVARY COMMANDS[/bold yellow]

  [green]uterus ovary_fill <side> <amount> [idx][/green]
                            - Fill ovary directly through tube
  [green]uterus ovary_drain <side> [idx][/green]
                            - Drain ovary fluid

[bold yellow]🔧 CERVIX & OBJECTS[/bold yellow]

  [green]uterus dilate <amount> [idx][/green]
                            - Dilate cervix (allows leakage!)
  [green]uterus contract [idx][/green]    - Contract cervix (stops leakage)
  [green]uterus insert <type> [idx][/green]
                            - Insert object (egg, ball, beads, speculum)
  [green]uterus remove_obj [idx] [obj_idx][/green]
                            - Remove object by index
  [green]uterus objects [idx][/green]     - List all inserted objects

[bold red]⚠️ PROLAPSE & EVERSION[/bold red]

  [green]uterus strain [force] [idx][/green]
                            - Apply strain (0.0-1.0), risk of prolapse
  [green]uterus evert [idx][/green]       - [red]FORCE COMPLETE EVERSION[/red]
                            (ejects all contents, tubes visible externally)
  [green]uterus reduce [amount] [idx][/green]
                            - Try to reduce prolapse
  [green]uterus risk [idx][/green]        - Show detailed prolapse risk factors

[bold yellow]⚙️ SIMULATION CONTROL[/bold yellow]

  [green]uterus tick [dt] [idx][/green]    - Manual update tick (for testing)
  [green]uterus peristalsis <strength> [idx][/green]
                            - Set peristalsis strength (0.0-1.0)
                            (pushes fluid from uterus to tubes over time)
  [green]uterus backflow <on/off> [idx][/green]
                            - Enable/disable backflow from ovaries

[bold magenta]╔══════════════════════════════════════════════════════════════╗[/bold magenta]
[bold magenta]║                    FLUID DISTRIBUTION                        ║[/bold magenta]
[bold magenta]╚══════════════════════════════════════════════════════════════╝[/bold magenta]

[yellow]Auto-distribution on add_fluid:[/yellow]
  • 70% stays in uterus cavity
  • 30% goes to fallopian tubes (split between left/right)
  • From tubes: auto-transfer to ovaries when tube >80% full
  • Backflow: returns to uterus when ovaries overfilled (if enabled)

[yellow]Peristalsis:[/yellow]
  • Natural movement pushing fluid uterus→tubes
  • Set strength: uterus peristalsis 0.8
  • Higher = faster fluid transfer

[yellow]Inflation Mechanics:[/yellow]
  • Increases capacity of uterus and tubes
  • Can become permanent (plasticity factor)
  • Risk of stretch marks at high inflation
  • Skin tension increases with inflation

[yellow]Leakage (like breast nipples):[/yellow]
  • Occurs in LEAKING state through dilated cervix
  • Rate depends on cervix dilation and pressure
  • High viscosity fluids leak slower

[bold magenta]╔══════════════════════════════════════════════════════════════╗[/bold magenta]
[bold magenta]║                    STATE PROGRESSIONS                        ║[/bold magenta]
[bold magenta]╚══════════════════════════════════════════════════════════════╝[/bold magenta]

[yellow]Fill States:[/yellow]
  EMPTY → NORMAL → TENSE → OVERPRESSURED → LEAKING

[yellow]Inflation States:[/yellow]
  NORMAL → STRETCHED → DISTENDED → HYPERDISTENDED → RUPTURE_RISK → RUPTURED

[yellow]Prolapse States:[/yellow]
  NORMAL → DESCENDED → PROLAPSED → [red]EVERTED[/red]

[yellow]Ovary States:[/yellow]
  NORMAL → ENLARGED → PROLAPSED → [red]EVERTED[/red] → TORSION (ischemia!)
        """,

        "breasts": """
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

[bold yellow]📊 FULLNESS & DETAILS (NEW)[/bold yellow]

  [green]breasts[/green]                 - Show breast grid overview
  [green]breasts fullness [r] [c][/green]  - [cyan]Detailed fullness display[/cyan]
                            Shows: fluid volume, mixture composition, 
                            inserted objects, nipple status, areola params
  [green]breasts detail [r] [c][/green]  - Detailed breast anatomy
  [green]breasts status [r] [c][/green]  - Compact status for one breast
  [green]breasts grid[/green]           - Show full breast grid

[bold magenta]States:[/bold magenta] EMPTY → NORMAL → TENSE → [red]OVERPRESSURED[/red] → [blue]LEAKING[/blue]

[bold magenta]Fullness Display includes:[/bold magenta]
  • Visual fill bars (color-coded: green/yellow/red)
  • Fluid mixture composition (MILK:50ml | CUM:30ml...)
  • Inserted objects list with volumes
  • Nipple status (open/closed, gape diameter, leaking)
  • Areola parameters (diameter, sensitivity, puffiness)
  • Physical stats (pressure, sag, elasticity)
  • Lactation and inflation status
        """,

        "genitals": """
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
        """,

        "general": """
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
        """,
        "sex": """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║              SEX & PENETRATION COMMANDS                      ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]🔞 БАЗОВЫЕ КОМАНДЫ[/bold yellow]

  [green]penetrate <target> [organ] [penis] [force][/green]
                            - Начать проникновение в цель
                            Пример: penetrate roxy vagina penis 70
                            Пример: penetrate 1 vagina (по индексу)
  [green]stimulate_self [amount][/green]   - Вызвать эрекцию (masturbation)
  [green]sex_status[/green]              - Показать статус текущего акта

[bold yellow]🍆 УПРАВЛЕНИЕ ПРОНИКНОВЕНИЕМ[/bold yellow]

  [green]thrust <amount> [force][/green]   - Толчок (положительное = вглубь)
                            Пример: thrust 5 80 (глубже на 5см)
                            Пример: thrust -3 40 (наружу на 3см)
  [green]cum[/green]                     - Эякуляция внутрь целевого органа
  [green]pullout[/green]                 - Извлечь член (проверяет узел/вакуум)

[bold magenta]Особенности:[/bold magenta]
• При полной эрекции пенис увеличивается в размерах
• Узел (knot) блокирует выход после эякуляции до спада возбуждения
• Вакуум от спермы может удерживать член внутри
• Глубина отслеживается в реальном времени
• Сперма добавляется как жидкость в целевой орган

[bold red]⚠️ Требования:[/bold red]
• У цели должен быть поддерживающий проникновение орган (vagina/anus)
• У вас должен быть пенис с достаточной эрекцией
• Используйте 'stimulate penis' или 'stimulate_self' перед penetrate
""",
"combat": """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║                    COMBAT SYSTEM                             ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]⚔️ БОЕВЫЕ КОМАНДЫ[/bold yellow]

  [green]combat_start [idx1] [idx2][/green] - Начать бой между телами
  [green]combat_status / cstat[/green]  - Показать статус боя и скиллы
  [green]combat_use <n> <target>[/green] - Использовать скилл (n - номер)
  [green]combat_skip / cskip[/green]    - Пропустить ход
  [green]combat_end / cend[/green]      - Завершить бой досрочно

[bold yellow]🎯 МЕХАНИКА[/bold yellow]

• Бой пошаговый, каждый ход дается 3 AP (Action Points)
• Скиллы требуют AP и имеют перезарядку (cooldown)
• Анатомия тела определяет доступные скиллы:
  - Грудь: Milk Spray, Breast Crush (>800ml)
  - Матка: Uterus Slam (пролапс или >60% fill)
  - Пенис: Cum Blast, Deep Pierce
  - Яичники: Ovary Burst (самоповреждение!)
  
[bold yellow]💥 ТИПЫ УРОНА[/bold yellow]

  BLUNT    - Удар/давление (Breast Crush)
  FLUID    - Жидкостный (Milk Spray, Cum Blast)
  PIERCE   - Пронзание (Prolapse Whip)
  STRETCH  - Растяжение (Deep Pierce)
  HORMONE  - Гормональный (Ovary Burst)
  INTERNAL - Внутренний урон органам

[bold yellow]⚡ СТАТУСЫ[/bold yellow]

  Оглушение (Stun)    - Пропуск хода
  Утечка (Leaking)    - Потеря жидкости каждый ход
  Критическое сост.   - При HP < 20%

[bold magenta]Пример:[/bold magenta]
  > combat_start 0 1    # Начать бой между телом 0 и 1
  > cstat               # Смотрим скиллы
  > cuse 1 Roxy         # Использовать скилл 1 на Roxy
  > cskip               # Пропустить ход
        """,
        "magic": """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║                    MAGIC SYSTEM                              ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]COMMANDS[/bold yellow]
  cast <skill> [target] [organ]  - Cast spell using fluids
  mana, m                        - Show fluid levels (mana)
  skills, sk                     - Show available skills
  perks                          - Show active perks
  learn <Class>                  - Learn new skill
  add_perk <type> [organ]        - Add passive perk
  magic_help, mhelp              - This help

[bold yellow]SCHOOLS[/bold yellow]
  [white]MILK[/white] (Breasts) - Healing & shields
  [yellow]CUM[/yellow] (Penis)   - Damage & buffs  
  [purple]HYBRID[/purple]        - Futanari only

Use [cyan]help[/cyan] without args to see all command categories.
""",
    }

    if topic in help_topics:
        border_colors = {
            "uterus": "bright_magenta",
            "breasts": "bright_cyan", 
            "genitals": "bright_red",
            "general": "bright_green",
        }
        console.print(Panel(help_topics[topic], 
                           title=f"[bold]{topic.upper()} System Help[/bold]", 
                           border_style=border_colors.get(topic, "white")))
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
    dt = float(args[0]) if args else 1.0

    for body in ctx.bodies:
        body.tick(dt)

    # Автоматические реакции (breasts + uterus)
    _process_auto_reactions(ctx.bodies, dt)

    console.print(f"[green]Ticked {len(ctx.bodies)} bodies (dt={dt})[/green]")


def _process_auto_reactions(bodies: List, dt: float):
    """Обработать автоматические реакции для всех тел."""
    for body in bodies:
        profile_name = "default"
        body_type = type(body).__name__.lower()

        if "roxy" in body_type or "migurdia" in body_type:
            profile_name = "roxy"
        elif "misaka" in body_type:
            profile_name = "misaka"

        # Breast reactions
        try:
            from body_sim.characters.breast_reactions import get_reaction_system
            breast_system = get_reaction_system()

            if hasattr(body, 'has_breasts') and body.has_breasts:
                reactions = breast_system.process_reactions(body, profile_name)
                for reaction in reactions:
                    _print_reaction(console, reaction, "Breast")
        except:
            pass

        # Uterus reactions
        try:
            from body_sim.characters.uterus_reactions import get_uterus_reaction_system
            uterus_system = get_uterus_reaction_system()

            if hasattr(body, 'uterus_system') and body.uterus_system:
                reactions = uterus_system.process_reactions(body, profile_name)
                for reaction in reactions:
                    _print_reaction(console, reaction, "Uterus")
        except:
            pass


def _print_reaction(console, reaction, source: str):
    """Вывести реакцию с цветовым кодированием."""
    color_map = {
        "neutral": "white",
        "pleasure": "magenta",
        "pain": "red",
        "embarrassment": "yellow",
        "panic": "bright_red",
        "tsundere": "bright_cyan",
        "discomfort": "yellow",
        "surprise": "cyan",
        "shock": "bright_cyan",
        "sadness": "blue",
        "denial": "dim",
        "anxiety": "yellow",
        "confusion": "yellow",
        "wonder": "green",
        "fear": "bright_red",
        "weird": "yellow",
        "overwhelm": "red",
        "agony": "bright_red",
        "dissociation": "dim",
        "unconscious": "dim",
        "panic_embarrassment": "bright_yellow",
        "pleasure_pain": "magenta",
    }
    color = color_map.get(reaction.emotion, "white")
    prefix = f"[{source}]"

    console.print(f"\n[{color}]{prefix} {reaction.text}[/{color}]")
    if reaction.sound_effect:
        console.print(f"[dim italic]{reaction.sound_effect}[/dim italic]")


# ============ НОВАЯ КОМАНДА BREASTS ============

def cmd_breasts(args: List[str], ctx: CommandContext):
    """Управление грудью - показ fullness и детальной информации."""
    if not ctx.active_body or not ctx.active_body.has_breasts:
        console.print("[red]No breasts available[/red]")
        return

    from body_sim.ui.breast_render import BreastRenderer
    renderer = BreastRenderer()
    
    if not args:
        # Показать всю сетку грудей в компактном виде
        console.print(renderer.render_grid(ctx.active_body.breast_grid, "Breast Grid"))
        return
    
    action = args[0].lower()
    args = args[1:]
    
    # Определяем индексы груди (по умолчанию [0,0])
    row = int(args[0]) if args else 0
    col = int(args[1]) if len(args) > 1 else 0
    
    try:
        breast = ctx.active_body.breast_grid.get(row, col)
    except (IndexError, AttributeError):
        console.print(f"[red]Invalid breast index [{row},{col}][/red]")
        return
    
    if action == "fullness":
        """Показать детальное заполнение груди (аналог uterus fullness)."""
        panel = renderer.render_fullness(breast, f"Breast [{row},{col}] Fullness")
        console.print(panel)
        
    elif action == "detail":
        """Показать детальную информацию о груди."""
        label = f"Breast [{row},{col}]"
        console.print(renderer.render_breast_detailed(breast, label))
        
    elif action == "status":
        """Показать компактный статус."""
        console.print(renderer.render_breast_compact(breast, f"[{row},{col}]"))
        
    elif action == "grid":
        """Показать всю сетку грудей."""
        console.print(renderer.render_grid(ctx.active_body.breast_grid))
        
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("[dim]Available actions:[/dim]")
        console.print("  [cyan]fullness [r] [c][/cyan] - Detailed fullness display (fluid + objects)")
        console.print("  [cyan]detail [r] [c][/cyan]   - Detailed breast info")
        console.print("  [cyan]status [r] [c][/cyan]   - Compact status")
        console.print("  [cyan]grid[/cyan]           - Show all breasts grid")



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

def cmd_penis_type(args: List[str], ctx: CommandContext):
    """Изменить тип пениса (анатомия, форма, особенности)."""
    if not ctx.active_body:
        console.print("[red]No body selected[/red]")
        return
    
    if not ctx.active_body.has_penis:
        console.print("[red]No penis available[/red]")
        return
    
    if len(args) < 1:
        console.print("[red]Usage: penis_type <type> [index][/red]")
        console.print("\n[bold cyan]Available types:[/bold cyan]")
        
        # Используем статический метод класса
        for type_id, name, color in Penis.get_available_types():
            console.print(f"  [{color}]{type_id:12}[/{color}] - {name}")
        return
    
    type_name = args[0].upper()
    penis_idx = int(args[1]) if len(args) > 1 else 0
    
    if penis_idx >= len(ctx.active_body.penises):
        console.print(f"[red]Invalid penis index: {penis_idx} (max: {len(ctx.active_body.penises)-1})[/red]")
        return
    
    try:
        from body_sim.core.enums import PenisType
        new_type = PenisType[type_name]
    except KeyError:
        console.print(f"[red]Unknown penis type: {type_name}[/red]")
        console.print("[dim]Use 'penis_type' without args to see list[/dim]")
        return
    
    penis = ctx.active_body.penises[penis_idx]
    
    # Вызываем метод трансформации
    result = penis.transform_type(new_type)
    
    if not result["success"]:
        console.print("[red]Transformation failed![/red]")
        return
    
    # Выводим результат
    console.print(f"[bold green]✓ Penis #{penis_idx} transformed![/bold green]")
    console.print(f"[dim]{result['old_type'].id} → {result['new_type'].id}[/dim]")
    
    if result["size_changed"]:
        console.print(f"\n[bold]Size changes:[/bold]")
        
        len_ratio = result["length_ratio"]
        len_color = "green" if len_ratio > 1.0 else "red" if len_ratio < 1.0 else "white"
        console.print(f"  Length: {result['old_length']:.1f}cm → {result['new_length']:.1f}cm "
                     f"([{len_color}]×{len_ratio:.2f}[/{len_color}])")
        
        girth_ratio = result["girth_ratio"]
        girth_color = "green" if girth_ratio > 1.0 else "red" if girth_ratio < 1.0 else "white"
        console.print(f"  Girth:  {result['old_girth']:.1f}cm → {result['new_girth']:.1f}cm "
                     f"([{girth_color}]×{girth_ratio:.2f}[/{girth_color}])")
    
    console.print(f"  Urethra: {result['urethra_diameter']:.1f}mm diameter")
    
    # Новые особенности
    if result["new_features"]:
        features_str = " | ".join(result["new_features"])
        console.print(f"\n[bold cyan]New features:[/bold cyan] {features_str}")
    
    # Инфо об эякуляции
    if penis.has_scrotum():
        max_pulse = penis.calculate_max_ejaculate_volume(force=1.0)
        console.print(f"\n[dim]Ejaculate: ×{result['ejaculate_mult']:.2f} mult | "
                     f"Max per pulse: {max_pulse:.1f}ml[/dim]")

def cmd_uterus(args: List[str], ctx: CommandContext):
    """Управление маткой (uterus) - система инфляции и жидкости."""
    if not ctx.active_body:
        console.print("[red]No body selected[/red]")
        return

    if not hasattr(ctx.active_body, 'uterus_system') or not ctx.active_body.uterus_system:
        console.print("[red]No uterus available[/red]")
        return

    system = ctx.active_body.uterus_system

    if not args:
        # Показать статус всех маток
        from body_sim.ui.uterus_render import UterusRenderer
        renderer = UterusRenderer()
        console.print(renderer.render_full_system(system))
        return

    action = args[0].lower()
    args = args[1:]  # Убираем action

    # Определяем индекс матки
    uterus_idx = 0
    if args:
        try:
            potential_idx = int(args[-1])
            if 0 <= potential_idx <= 9 and len(system.uteri) > potential_idx:
                uterus_idx = potential_idx
                args = args[:-1]
        except ValueError:
            pass

    if uterus_idx >= len(system.uteri):
        console.print(f"[red]Invalid uterus index: {uterus_idx}[/red]")
        return

    uterus = system.uteri[uterus_idx]

    if action == "status":
        from body_sim.ui.uterus_render import UterusRenderer
        renderer = UterusRenderer()
        console.print(renderer.render_uterus_detailed(uterus, f"Uterus #{uterus_idx}"))

        # Дополнительная инфо о жидкости и инфляции
        console.print(f"\n[bold cyan]Fluid Distribution:[/bold cyan]")
        console.print(f"  [dim]Uterus:[/dim] {uterus.uterus_filled:.1f}ml")
        console.print(f"  [dim]Tubes:[/dim] {uterus.tubes_filled:.1f}ml")
        console.print(f"  [dim]Ovaries:[/dim] {uterus.ovaries_filled:.1f}ml")
        console.print(f"  [dim]Total:[/dim] {uterus.filled:.1f}ml")

        console.print(f"\n[bold magenta]Inflation:[/bold magenta]")
        console.print(f"  [dim]Status:[/dim] {uterus.inflation_status.value}")
        console.print(f"  [dim]Ratio:[/dim] {uterus.inflation_ratio:.2f}x")
        console.print(f"  [dim]Wall stretch:[/dim] {uterus.walls.stretch_ratio:.2f}x")

        if hasattr(uterus.walls, 'is_permanently_stretched') and uterus.walls.is_permanently_stretched:
            console.print("  [yellow]⚠️ Permanently stretched![/yellow]")

    elif action == "fullness":
        """Показать детальное заполнение системы (жидкость + предметы)."""
        from body_sim.ui.uterus_render import UterusRenderer
        renderer = UterusRenderer()
        console.print(renderer.render_fullness(uterus, f"Uterus #{uterus_idx} Fullness"))

    elif action == "add_fluid":
        if len(args) < 2:
            console.print("[red]Usage: uterus add_fluid <type> <amount> [idx][/red]")
            console.print("Types: milk, cum, water, honey, oil, blood")
            return
        from body_sim.core.enums import FluidType
        try:
            fluid_type = FluidType[args[0].upper()]
        except KeyError:
            console.print(f"[red]Unknown fluid type: {args[0]}[/red]")
            return
        amount = float(args[1])
        added = uterus.add_fluid(fluid_type, amount)

        console.print(f"[cyan]Added {added:.1f}ml of {args[0].upper()}[/cyan]")
        console.print(f"[dim]Distribution: Uterus {uterus.uterus_filled:.1f}ml | "
                     f"Tubes {uterus.tubes_filled:.1f}ml | Ovaries {uterus.ovaries_filled:.1f}ml[/dim]")

        if uterus.inflation_status.value != "normal":
            console.print(f"[yellow]Inflation: {uterus.inflation_status.value.upper()}[/yellow]")

    elif action == "drain":
        removed = uterus.drain_all()
        total = sum(removed.values())
        if total > 0:
            console.print(f"[yellow]Drained {total:.1f}ml from entire system[/yellow]")
            for ft, amt in removed.items():
                console.print(f"  [dim]- {ft.name}: {amt:.1f}ml[/dim]")
        else:
            console.print("[dim]System was empty[/dim]")

    elif action == "remove":
        amount = float(args[0]) if args else 10.0
        removed = uterus.remove_fluid(amount)
        console.print(f"[yellow]Removed {removed:.1f}ml from system[/yellow]")

    elif action == "dilate":
        amount = float(args[0]) if args else 1.0
        old_dilation = uterus.cervix.current_dilation
        uterus.cervix.dilate(amount)
        console.print(f"[magenta]Cervix: {old_dilation:.1f}cm → {uterus.cervix.current_dilation:.1f}cm[/magenta]")

    elif action == "contract":
        uterus.cervix.contract()
        console.print("[green]Cervix contracted[/green]")

    # ============ ИНФЛЯЦИЯ ============
    elif action == "inflate":
        if not args:
            console.print("[red]Usage: uterus inflate <ratio> [idx][/red]")
            console.print("Example: uterus inflate 2.0  (2x normal size)")
            return
        ratio = float(args[0])
        success = uterus.inflate(ratio)
        if success:
            console.print(f"[bold magenta]🔵 Uterus inflated to {ratio:.1f}x[/bold magenta]")
            info = uterus.get_inflation_details()
            console.print(f"[dim]Skin tension: {info['skin_tension']:.1%} | "
                         f"Stretch marks risk: {info['stretch_marks_risk']:.1%}[/dim]")
            if info['is_permanent']:
                console.print("[yellow]⚠️ Permanent stretching occurred![/yellow]")
        else:
            console.print("[red]Cannot inflate further - risk of rupture![/red]")

    elif action == "deflate":
        """Уменьшить инфляцию (восстановление)."""
        uterus.walls.recover(10.0)  # Ускоренное восстановление
        if uterus.inflation_ratio > 1.0:
            old_ratio = uterus.inflation_ratio
            # Постепенное уменьшение
            new_ratio = max(1.0, uterus.inflation_ratio * 0.8)
            uterus.inflate(new_ratio)
            console.print(f"[green]Deflated: {old_ratio:.2f}x → {new_ratio:.2f}x[/green]")
        else:
            console.print("[dim]Already at normal size[/dim]")

    elif action == "inflation":
        """Показать детали инфляции."""
        info = uterus.get_inflation_details()
        console.print(f"[bold cyan]Inflation Details:[/bold cyan]")
        console.print(f"  Status: {uterus.inflation_status.value}")
        console.print(f"  Uterus ratio: {info['uterus_ratio']:.2f}x")
        console.print(f"  Wall stretch: {info['wall_stretch']:.2f}x")
        console.print(f"  Total stretch: {info['total_stretch']:.2f}x")
        console.print(f"  Skin tension: {info['skin_tension']:.1%}")
        console.print(f"  Stretch marks risk: {info['stretch_marks_risk']:.1%}")
        console.print(f"  Permanent: {info['is_permanent']}")

    # ============ ТРУБЫ ============
    elif action == "tube_inflate":
        if len(args) < 2:
            console.print("[red]Usage: uterus tube_inflate <side> <ratio> [idx][/red]")
            return
        side = args[0].lower()
        ratio = float(args[1])
        success = uterus.inflate_tube(side, ratio)
        if success:
            tube = uterus.left_tube if side == "left" else uterus.right_tube
            console.print(f"[magenta]{side.upper()} tube inflated to {ratio:.1f}x[/magenta]")
            console.print(f"[dim]Status: {tube.inflation_status.value} | "
                         f"Fluid: {tube.contained_fluid:.1f}ml[/dim]")
        else:
            console.print("[red]Cannot inflate tube further![/red]")

    elif action == "tube_stretch":
        if len(args) < 2:
            console.print("[red]Usage: uterus tube_stretch <side> <ratio> [idx][/red]")
            return
        side = args[0].lower()
        ratio = float(args[1])
        success = uterus.stretch_tube(side, ratio)
        if success:
            tube = uterus.left_tube if side == "left" else uterus.right_tube
            console.print(f"[yellow]{side.upper()} tube stretched to {ratio:.1f}x[/yellow]")
            console.print(f"[dim]Length: {tube.stretched_length:.1f}cm | "
                         f"Can prolapse ovary: {tube.can_prolapse_ovary}[/dim]")
        else:
            console.print("[red]Tube blocked or overstretched![/red]")

    elif action == "tube_status":
        """Показать статус труб."""
        console.print(f"[bold cyan]Fallopian Tubes:[/bold cyan]")
        for tube in uterus.tubes:
            if tube:
                console.print(f"\n[bold]{tube.side.upper()}:[/bold]")
                console.print(f"  Length: {tube.current_length:.1f}cm (stretch: {tube.current_stretch:.1f}x)")
                console.print(f"  Diameter: {tube.current_diameter:.1f}cm (inflate: {tube.inflation_ratio:.1f}x)")
                console.print(f"  Status: {tube.inflation_status.value}")
                console.print(f"  Fluid: {tube.contained_fluid:.1f}ml / {tube.max_fluid_capacity:.1f}ml")
                if tube.ovary:
                    console.print(f"  → Ovary: {tube.ovary.fluid_content:.1f}ml")

    # ============ ЯИЧНИКИ ============
    elif action == "ovary_fill":
        """Наполнить яичник напрямую (через трубу)."""
        if len(args) < 2:
            console.print("[red]Usage: uterus ovary_fill <side> <amount> [idx][/red]")
            return
        side = args[0].lower()
        amount = float(args[1])
        tube = uterus.left_tube if side == "left" else uterus.right_tube
        if tube and tube.ovary:
            added = tube.ovary.add_fluid(amount)
            console.print(f"[cyan]Added {added:.1f}ml to {side} ovary[/cyan]")
            console.print(f"[dim]Total: {tube.ovary.fluid_content:.1f}ml / {tube.ovary.max_fluid_capacity:.1f}ml[/dim]")
        else:
            console.print("[red]Ovary not found[/red]")

    elif action == "ovary_drain":
        """Опустошить яичник."""
        side = args[0].lower() if args else "left"
        ovary = uterus.left_ovary if side == "left" else uterus.right_ovary
        if ovary:
            removed = ovary.remove_fluid(ovary.fluid_content)
            console.print(f"[yellow]Drained {removed:.1f}ml from {side} ovary[/yellow]")
        else:
            console.print("[red]Ovary not found[/red]")

    # ============ ПРОЛАПС ============
    elif action == "strain":
        force = float(args[0]) if args else 0.5
        result = uterus.apply_strain(force)
        if result:
            console.print(f"[red]⚠️ Prolapse progressed! State: {uterus.state.name}[/red]")
        else:
            console.print("[green]Strain applied, no prolapse[/green]")

    elif action == "evert":
        if not uterus.is_everted:
            uterus._complete_eversion()
            console.print(f"[bold red]🔴 UTERUS #{uterus_idx} EVERTED![/bold red]")
            console.print("[red]All contents ejected. Internal surface exposed.[/red]")
        else:
            console.print("[yellow]Already everted[/yellow]")

    elif action == "reduce":
        amount = float(args[0]) if args else 0.5
        success = uterus.reduce_prolapse(amount)
        if success:
            console.print(f"[green]Prolapse reduced. State: {uterus.state.name}[/green]")
        else:
            console.print("[red]Failed to reduce - requires medical intervention[/red]")

    elif action == "risk":
        """Показать риск пролапса."""
        risk = uterus.calculate_prolapse_risk()
        console.print(f"[bold]Prolapse Risk: {risk:.1%}[/bold]")
        console.print(f"[dim]Factors:[/dim]")
        console.print(f"  Ligament integrity: {uterus.ligament_integrity:.2f}")
        console.print(f"  Pelvic floor: {uterus.pelvic_floor_strength:.2f}")
        console.print(f"  Wall fatigue: {uterus.walls.fatigue:.2f}")
        console.print(f"  Inflation: {uterus.inflation_ratio:.2f}x")
        if risk > 0.7:
            console.print("[red]⚠️ HIGH RISK![/red]")

    # ============ ОБЪЕКТЫ ============
    elif action == "insert":
        if not args:
            console.print("[red]Usage: uterus insert <object_type>[/red]")
            console.print("Types: egg, ball, beads, speculum")
            return
        obj_type = args[0].lower()

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
            console.print(f"[green]Inserted {obj.name} ({obj.volume}ml)[/green]")
            fill_pct = (uterus.uterus_filled / uterus.current_volume * 100) if uterus.current_volume > 0 else 0
            console.print(f"[dim]Uterus fill: {fill_pct:.0f}%[/dim]")
        else:
            console.print("[red]Failed to insert - cervix closed or no space[/red]")

    elif action == "remove_obj":
        idx = int(args[0]) if args else 0
        obj = uterus.remove_object(idx)
        if obj:
            console.print(f"[green]Removed {obj.name}[/green]")
        else:
            console.print("[red]No object at that index[/red]")

    elif action == "objects":
        """Показать вставленные объекты."""
        if uterus.inserted_objects:
            console.print(f"[bold]Inserted objects:[/bold]")
            for i, obj in enumerate(uterus.inserted_objects):
                vol = getattr(obj, 'volume', 0) or getattr(obj, 'effective_volume', 0)
                console.print(f"  {i}: {obj.name} ({vol}ml)")
        else:
            console.print("[dim]No objects inserted[/dim]")

    # ============ СИМУЛЯЦИЯ ============
    elif action == "tick":
        dt = float(args[0]) if args else 1.0
        result = uterus.tick(dt=dt)
        console.print(f"[dim]Tick: {result}[/dim]")

    elif action == "peristalsis":
        """Установить силу перистальтики."""
        strength = float(args[0]) if args else 0.5
        uterus.peristalsis_strength = max(0.0, min(1.0, strength))
        console.print(f"[cyan]Peristalsis strength: {uterus.peristalsis_strength:.1%}[/cyan]")

    elif action == "backflow":
        """Включить/выключить обратный поток."""
        enable = args[0].lower() in ("on", "true", "1", "yes") if args else True
        uterus.backflow_enabled = enable
        status = "enabled" if enable else "disabled"
        console.print(f"[cyan]Backflow {status}[/cyan]")

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Actions: status, add_fluid, drain, remove, dilate, contract")
        console.print("         inflate, deflate, inflation, tube_inflate, tube_stretch, tube_status")
        console.print("         ovary_fill, ovary_drain, strain, evert, reduce, risk")
        console.print("         insert, remove_obj, objects, tick, peristalsis, backflow")


def cmd_ovary(args: List[str], ctx: CommandContext):
    """Управление яичниками (ovaries) - упрощённый интерфейс."""
    if not ctx.active_body:
        console.print("[red]No body selected[/red]")
        return

    if not hasattr(ctx.active_body, 'uterus_system') or not ctx.active_body.uterus_system:
        console.print("[red]No uterus system available[/red]")
        return

    system = ctx.active_body.uterus_system

    # Парсим аргументы
    side = "left"
    uterus_idx = 0
    action = "status"

    if args:
        # Первый аргумент может быть action или side
        if args[0].lower() in ("left", "right"):
            side = args[0].lower()
            args = args[1:]
        elif args[0].lower() in ("status", "enlarge", "rupture", "evert", "reposition", "ovulate"):
            action = args[0].lower()
            args = args[1:]
        else:
            action = args[0].lower()
            args = args[1:]

    # Проверяем последний аргумент на индекс матки
    if args:
        try:
            potential_idx = int(args[-1])
            if 0 <= potential_idx <= 9:
                uterus_idx = potential_idx
                args = args[:-1]
        except ValueError:
            pass

    if uterus_idx >= len(system.uteri):
        console.print(f"[red]Invalid uterus index: {uterus_idx}[/red]")
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
    """Управление фаллопиевыми трубами (fallopian tubes) - упрощённый интерфейс."""
    if not ctx.active_body:
        console.print("[red]No body selected[/red]")
        return

    if not hasattr(ctx.active_body, 'uterus_system') or not ctx.active_body.uterus_system:
        console.print("[red]No uterus system available[/red]")
        return

    system = ctx.active_body.uterus_system

    # Парсим аргументы
    side = "left"
    uterus_idx = 0
    action = "status"

    if args:
        # Первый аргумент может быть action или side
        if args[0].lower() in ("left", "right"):
            side = args[0].lower()
            args = args[1:]
        elif args[0].lower() in ("status", "stretch", "evert", "reposition", "add_fluid", "clear"):
            action = args[0].lower()
            args = args[1:]
        else:
            action = args[0].lower()
            args = args[1:]

    # Проверяем последний аргумент на индекс матки
    if args:
        try:
            potential_idx = int(args[-1])
            if 0 <= potential_idx <= 9:
                uterus_idx = potential_idx
                args = args[:-1]
        except ValueError:
            pass

    if uterus_idx >= len(system.uteri):
        console.print(f"[red]Invalid uterus index: {uterus_idx}[/red]")
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

def cmd_reactions_all(args: List[str], ctx: CommandContext):
    """Показать все реакции (грудь + матка) для текущего персонажа."""
    if not ctx.active_body:
        console.print("[red]No active body![/red]")
        return

    # Определяем профиль персонажа
    profile_name = "default"
    body_type = type(ctx.active_body).__name__.lower()

    if "roxy" in body_type or "migurdia" in body_type:
        profile_name = "roxy"
    elif "misaka" in body_type:
        profile_name = "misaka"

    has_reactions = False

    # ============ BREAST REACTIONS ============
    try:
        from body_sim.characters.breast_reactions import get_reaction_system
        breast_system = get_reaction_system()

        if hasattr(ctx.active_body, 'has_breasts') and ctx.active_body.has_breasts:
            breast_reactions = breast_system.process_reactions(ctx.active_body, profile_name)

            if breast_reactions:
                has_reactions = True
                console.print("\n[bold cyan]╔══════════════════════════════════════════╗[/bold cyan]")
                console.print("[bold cyan]║           BREAST REACTIONS               ║[/bold cyan]")
                console.print("[bold cyan]╚══════════════════════════════════════════╝[/bold cyan]")

                for reaction in breast_reactions:
                    color_map = {
                        "neutral": "white",
                        "pleasure": "magenta",
                        "pain": "red",
                        "embarrassment": "yellow",
                        "panic": "bright_red",
                        "tsundere": "bright_cyan",
                        "discomfort": "yellow",
                        "surprise": "cyan",
                        "shock": "bright_cyan",
                        "sadness": "blue",
                        "denial": "dim",
                        "anxiety": "yellow",
                        "confusion": "yellow",
                        "wonder": "green",
                        "fear": "bright_red",
                        "weird": "yellow",
                        "overwhelm": "red",
                        "agony": "bright_red",
                        "dissociation": "dim",
                        "unconscious": "dim",
                        "panic_embarrassment": "bright_yellow",
                        "pleasure_pain": "magenta",
                    }
                    color = color_map.get(reaction.emotion, "white")

                    console.print(f"\n[{color}]{reaction.text}[/{color}]")
                    if reaction.sound_effect:
                        console.print(f"[dim italic]{reaction.sound_effect}[/dim italic]")
                    if reaction.physical_effect:
                        console.print(f"[dim]*{reaction.physical_effect}*[/dim]")
    except Exception as e:
        if args and args[0] == 'debug':
            console.print(f"[dim]Breast reactions error: {e}[/dim]")

    # ============ UTERUS REACTIONS ============
    try:
        from body_sim.characters.uterus_reactions import get_uterus_reaction_system
        uterus_system = get_uterus_reaction_system()

        if hasattr(ctx.active_body, 'uterus_system') and ctx.active_body.uterus_system:
            uterus_reactions = uterus_system.process_reactions(ctx.active_body, profile_name)

            if uterus_reactions:
                has_reactions = True
                console.print("\n[bold magenta]╔══════════════════════════════════════════╗[/bold magenta]")
                console.print("[bold magenta]║           UTERUS REACTIONS               ║[/bold magenta]")
                console.print("[bold magenta]╚══════════════════════════════════════════╝[/bold magenta]")

                for reaction in uterus_reactions:
                    color_map = {
                        "neutral": "white",
                        "pleasure": "magenta",
                        "pain": "red",
                        "embarrassment": "yellow",
                        "panic": "bright_red",
                        "tsundere": "bright_cyan",
                        "discomfort": "yellow",
                        "surprise": "cyan",
                        "shock": "bright_cyan",
                        "sadness": "blue",
                        "denial": "dim",
                        "anxiety": "yellow",
                        "confusion": "yellow",
                        "wonder": "green",
                        "fear": "bright_red",
                        "weird": "yellow",
                        "overwhelm": "red",
                        "agony": "bright_red",
                        "dissociation": "dim",
                        "unconscious": "dim",
                        "panic_embarrassment": "bright_yellow",
                        "pleasure_pain": "magenta",
                    }
                    color = color_map.get(reaction.emotion, "white")

                    console.print(f"\n[{color}]{reaction.text}[/{color}]")
                    if reaction.sound_effect:
                        console.print(f"[dim italic]{reaction.sound_effect}[/dim italic]")
                    if reaction.physical_effect:
                        console.print(f"[dim]*{reaction.physical_effect}*[/dim]")
    except Exception as e:
        if args and args[0] == 'debug':
            console.print(f"[dim]Uterus reactions error: {e}[/dim]")

    if not has_reactions:
        console.print("[dim]No new reactions...[/dim]")
        if args and args[0] == 'debug':
            console.print(f"[dim]Body type: {body_type}, Profile: {profile_name}[/dim]")


def cmd_reactions_clear_all(args: List[str], ctx: CommandContext):
    """Очистить все состояния реакций (грудь + матка)."""
    cleared = []

    # Очистка breast reactions
    try:
        from body_sim.characters.breast_reactions import get_reaction_system
        breast_system = get_reaction_system()
        if ctx.active_body:
            breast_system.clear_state(id(ctx.active_body))
        else:
            breast_system.clear_state()
        cleared.append("breast")
    except:
        pass

    # Очистка uterus reactions
    try:
        from body_sim.characters.uterus_reactions import get_uterus_reaction_system
        uterus_system = get_uterus_reaction_system()
        if ctx.active_body:
            uterus_system.clear_state(id(ctx.active_body))
        else:
            uterus_system.clear_state()
        cleared.append("uterus")
    except:
        pass

    if cleared:
        console.print(f"[green]Cleared {', '.join(cleared)} reaction states[/green]")
    else:
        console.print("[yellow]No reaction systems to clear[/yellow]")

def cmd_vagina(args: List[str], ctx: CommandContext):
    """Управление вагиной - fullness, fluid, penetration."""
    if not ctx.active_body:
        console.print("[red]No body selected[/red]")
        return
    
    if not hasattr(ctx.active_body, 'vaginas') or not ctx.active_body.vaginas:
        console.print("[red]No vagina available[/red]")
        return
    
    # По умолчанию индекс 0
    vagina_idx = 0
    action = "status"
    action_args = []
    
    # Парсинг аргументов
    if args:
        # Проверяем, является ли первый аргумент индексом
        try:
            potential_idx = int(args[0])
            if 0 <= potential_idx < len(ctx.active_body.vaginas):
                vagina_idx = potential_idx
                action_args = args[1:]
            else:
                action_args = args
        except ValueError:
            # Это action, не индекс
            action_args = args
    
    # Определяем action из оставшихся аргументов
    if action_args:
        action = action_args[0].lower()
        action_args = action_args[1:]
    
    vagina = ctx.active_body.vaginas[vagina_idx]
    
    # Проверяем наличие fluid_system
    if not hasattr(vagina, 'fluid_system'):
        console.print(f"[red]Vagina #{vagina_idx} doesn't have fluid system[/red]")
        return
    
    fs = vagina.fluid_system
    
    # === FULLNESS (основная команда) ===
    if action in ("fullness", "full", "f"):
        from body_sim.ui.vagina_render import VaginaRenderer
        renderer = VaginaRenderer()
        console.print(renderer.render_fullness(vagina, f"Vagina #{vagina_idx} Fullness"))
    
    # === STATUS (компактный) ===
    elif action in ("status", "s"):
        from body_sim.ui.vagina_render import VaginaRenderer
        renderer = VaginaRenderer()
        console.print(renderer.render_compact(vagina, f"Vagina[{vagina_idx}]"))
    
    # === ADD FLUID (как у uterus) ===
    elif action in ("add_fluid", "add", "fill"):
        if len(action_args) < 2:
            console.print("[red]Usage: vagina <idx> add_fluid <type> <amount>[/red]")
            console.print("Types: milk, cum, water, honey, oil, blood")
            return
        
        from body_sim.core.enums import FluidType
        try:
            fluid_type = FluidType[action_args[0].upper()]
        except KeyError:
            console.print(f"[red]Unknown fluid type: {action_args[0]}[/red]")
            return
        
        try:
            amount = float(action_args[1])
        except ValueError:
            console.print("[red]Amount must be a number[/red]")
            return
        
        added = vagina.add_fluid(amount, action_args[0])
        
        if added > 0:
            console.print(f"[cyan]Added {added:.1f}ml of {action_args[0].upper()}[/cyan]")
            console.print(f"[dim]Total: {fs.filled:.1f}ml / {fs.max_volume:.1f}ml ({fs.fill_percentage:.1f}%)[/dim]")
            
            if added < amount:
                console.print(f"[yellow]⚠ {amount - added:.1f}ml overflowed![/yellow]")
        else:
            console.print("[red]Cannot add - container full![/red]")
    
    # === DRAIN (полная очистка) ===
    elif action in ("drain", "empty", "clear"):
        removed = vagina.drain_all()
        total = sum(removed.values())
        
        if total > 0:
            console.print(f"[yellow]Drained {total:.1f}ml:[/yellow]")
            for fluid, amt in removed.items():
                console.print(f"  [dim]- {fluid}: {amt:.1f}ml[/dim]")
        else:
            console.print("[dim]Already empty[/dim]")
    
    # === REMOVE (частичное удаление) ===
    elif action in ("remove", "rm"):
        amount = float(action_args[0]) if action_args else 10.0
        removed = vagina.remove_fluid(amount)
        console.print(f"[yellow]Removed {removed:.1f}ml[/yellow]")
        console.print(f"[dim]Remaining: {fs.filled:.1f}ml[/dim]")
    
    # === INFLATE (растяжение) ===# В commands.py cmd_vagina
    elif action == "inflate":
        if not action_args:
            console.print("[red]Usage: vagina <idx> inflate <ratio>[/red]")
            return
        
        ratio = float(action_args[0])
        old_length = vagina.canal_length
        old_diam = vagina.rest_diameter
        
        success = vagina.inflate(ratio)  # Теперь это метод класса
        
        if success:
            console.print(f"[magenta]Inflated to {ratio:.1f}x volume[/magenta]")
            console.print(f"[dim]Dimensions: {old_length:.1f}cm→{vagina.canal_length:.1f}cm, "
                         f"{old_diam:.1f}cm→{vagina.rest_diameter:.1f}cm[/dim]")
        else:
            console.print("[red]Cannot inflate further - risk of rupture![/red]")

    
    
    # === DEFLATE ===
    elif action == "deflate":
        old_ratio = fs.inflation_ratio
        fs.deflate(0.5)  # Быстрое восстановление
        console.print(f"[green]Deflated: {old_ratio:.2f}x → {fs.inflation_ratio:.2f}x[/green]")
    
    # === PENETRATION STATUS ===
    elif action in ("pen", "penetration", "inserted"):
        if vagina.is_penetrated:
            console.print(f"[bold]Inserted objects ({len(vagina.inserted_objects)}):[/bold]")
            for i, data in enumerate(vagina.inserted_objects):
                obj = data.object
                console.print(f"  {i}: {obj.name} at {obj.inserted_depth:.1f}cm")
        else:
            console.print("[dim]Not penetrated[/dim]")
    
    # === LIST всех вагин ===
    elif action == "list":
        console.print(f"[bold]Vaginas for {ctx.active_body.name}:[/bold]")
        for i, v in enumerate(ctx.active_body.vaginas):
            fs = v.fluid_system if hasattr(v, 'fluid_system') else None
            if fs:
                status = "🔴" if fs.is_leaking else f"{fs.fill_percentage:.0f}%"
                pen = "⬇" if v.is_penetrated else "○"
                console.print(f"  [{i}] {pen} {fs.filled:.0f}ml / {fs.max_volume:.0f}ml ({status})")
    
    # === HELP / DEFAULT ===
    else:
        console.print(f"[yellow]Unknown action: {action}[/yellow]")
        console.print("[dim]Available actions:[/dim]")
        console.print("  [cyan]fullness [idx][/cyan]     - Detailed fullness display")
        console.print("  [cyan]status [idx][/cyan]       - Compact status")
        console.print("  [cyan]add_fluid <type> <amount> [idx][/cyan]")
        console.print("  [cyan]drain [idx][/cyan]        - Empty completely")
        console.print("  [cyan]remove <amount> [idx][/cyan]")
        console.print("  [cyan]inflate <ratio> [idx][/cyan]")
        console.print("  [cyan]deflate [idx][/cyan]")
        console.print("  [cyan]penetration [idx][/cyan]  - Show inserted objects")
        console.print("  [cyan]list[/cyan]               - List all vaginas")


#============ MAGIC COMMAND HANDLERS ============

def cmd_cast(args: List[str], ctx: CommandContext):
    """Использовать магический скилл: cast <skill_name> [target_idx] [target_organ]"""
    if not MAGIC_AVAILABLE:
        console.print("[red]Magic system not available[/red]")
        return
    
    if not ctx.active_body:
        console.print("[red]No active body[/red]")
        return
    
    if len(args) < 1:
        console.print("[red]Usage: cast <skill_name> [target_idx] [organ][/red]")
        console.print("[dim]Example: cast 'Milk Spray' 1[/dim]")
        console.print("[dim]Example: cast 'Cum Shot' 0 vagina[/dim]")
        return
    
    skill_name = args[0]
    target_idx = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    target_organ = args[2] if len(args) > 2 else None
    
    # Получаем цель
    target = None
    if target_idx is not None and 0 <= target_idx < len(ctx.bodies):
        target = ctx.bodies[target_idx]
    
    # Проверяем инициализацию магии
    if not hasattr(ctx.active_body, 'skill_book'):
        console.print("[red]Active body has no magic system initialized[/red]")
        console.print("[dim]Hint: Use body.init_magic() first[/dim]")
        return
    
    # Используем скилл
    result = ctx.active_body.cast_spell(skill_name, target, target_organ=target_organ)
    
    # Отображаем результат
    renderer = MagicRenderer(ctx.active_body)
    console.print(renderer.render_casting_result(result))
    
    # Если успех и есть эффекты - показываем детали
    if result.get("success"):
        for effect in result.get("results", []):
            if effect.get("type") == "damage" and target:
                console.print(f"[red]💥 {target.name} takes {effect.get('value', 0):.1f} damage![/red]")
            elif effect.get("type") == "heal":
                console.print(f"[green]💚 Healed for {effect.get('amount', 0):.1f} HP[/green]")
            elif effect.get("type") == "fill":
                console.print(f"[blue]💧 Filled {effect.get('organ', 'organ')} with {effect.get('amount', 0):.1f}ml[/blue]")


def cmd_skills(args: List[str], ctx: CommandContext):
    """Показать доступные магические скиллы"""
    if not MAGIC_AVAILABLE:
        console.print("[red]Magic system not available[/red]")
        return
    
    if not ctx.active_body:
        console.print("[red]No active body[/red]")
        return
    
    if not hasattr(ctx.active_body, 'skill_book'):
        console.print("[red]Active body has no magic system[/red]")
        return
    
    renderer = MagicRenderer(ctx.active_body)
    console.print(renderer.render_skill_book())
    
    # Показываем combo-возможности если есть история
    history = ctx.active_body.skill_book.skill_history[-3:]
    if history:
        console.print(f"\\n[dim]Recent casts: {' → '.join(history)}[/dim]")


def cmd_mana(args: List[str], ctx: CommandContext):
    """Показать статус маны (жидкостей в органах)"""
    if not MAGIC_AVAILABLE:
        console.print("[red]Magic system not available[/red]")
        return
    
    if not ctx.active_body:
        console.print("[red]No active body[/red]")
        return
    
    if not hasattr(ctx.active_body, 'get_mana_status'):
        console.print("[red]Active body has no mana system[/red]")
        return
    
    renderer = MagicRenderer(ctx.active_body)
    console.print(renderer.render_mana_status())
    
    # Дополнительная информация о магической силе
    if hasattr(ctx.active_body, 'magic_power'):
        power = ctx.active_body.magic_power
        color = "green" if power > 1.0 else "white"
        console.print(f"\\n[{color}]Magic Power: {power:.2f}x[/{color}]")


def cmd_perks(args: List[str], ctx: CommandContext):
    """Показать активные перки"""
    if not MAGIC_AVAILABLE:
        console.print("[red]Magic system not available[/red]")
        return
    
    if not ctx.active_body:
        console.print("[red]No active body[/red]")
        return
    
    renderer = MagicRenderer(ctx.active_body)
    console.print(renderer.render_perks())


def cmd_learn(args: List[str], ctx: CommandContext):
    """Выучить новый скилл: learn <skill_class>"""
    if not MAGIC_AVAILABLE:
        console.print("[red]Magic system not available[/red]")
        return
    
    if not ctx.active_body:
        console.print("[red]No active body[/red]")
        return
    
    if len(args) < 1:
        console.print("[red]Usage: learn <SkillClassName>[/red]")
        console.print("[dim]Available:[/dim]")
        console.print("  [cyan]MilkSpray[/cyan], [cyan]LactationHeal[/cyan], [cyan]BreastShield[/cyan]")
        console.print("  [cyan]CumShot[/cyan], [cyan]VirilityBoost[/cyan], [cyan]SemenWeb[/cyan]")
        console.print("  [cyan]DualRelease[/cyan], [cyan]GenderFusion[/cyan]")
        return
    
    skill_class = args[0]
    
    # Карта доступных скиллов
    skill_map = {
        "MilkSpray": MilkSpray,
        "LactationHeal": LactationHeal,
        "BreastShield": BreastShield,
        "CumShot": CumShot,
        "VirilityBoost": VirilityBoost,
        "SemenWeb": SemenWeb,
        "DualRelease": DualRelease,
        "GenderFusion": GenderFusion,
    }
    
    if skill_class not in skill_map:
        console.print(f"[red]Unknown skill class: {skill_class}[/red]")
        return
    
    try:
        skill = skill_map[skill_class]()
        ctx.active_body.skill_book.add_skill(skill)
        console.print(f"[green]✓ Learned: {skill.name}[/green]")
        console.print(f"[dim]{skill.description}[/dim]")
    except Exception as e:
        console.print(f"[red]Error learning skill: {e}[/red]")


def cmd_add_perk(args: List[str], ctx: CommandContext):
    """Добавить перк: add_perk <perk_type> [organ]"""
    if not MAGIC_AVAILABLE:
        console.print("[red]Magic system not available[/red]")
        return
    
    if not ctx.active_body:
        console.print("[red]No active body[/red]")
        return
    
    if len(args) < 1:
        console.print("[red]Usage: add_perk <type> [organ][/red]")
        console.print("[dim]Types:[/dim]")
        console.print("  [cyan]regen[/cyan] <organ>  - Fluid regeneration")
        console.print("  [cyan]expand[/cyan] <organ> - Increase capacity")
        console.print("  [cyan]pressure[/cyan]       - Reduce skill costs")
        console.print("  [cyan]sensitive[/cyan> <organ> - Power boost when full")
        console.print("[dim]Organs: breasts, uterus, penis, testicles[/dim]")
        return
    
    perk_type = args[0].lower()
    organ = args[1] if len(args) > 1 else None
    
    try:
        from body_sim.core.enums import FluidType
        
        perk = None
        if perk_type == "regen":
            if not organ:
                console.print("[red]Specify organ for regen perk[/red]")
                return
            fluid = FluidType.MILK if organ in ["breasts", "uterus"] else FluidType.CUM
            perk = FluidRegenerationPerk(organ, fluid, 5.0)
        elif perk_type == "expand":
            if not organ:
                console.print("[red]Specify organ for expand perk[/red]")
                return
            perk = OverfillCapacityPerk(organ, 0.2)
        elif perk_type == "pressure":
            perk = PressureMasteryPerk()
        elif perk_type == "sensitive":
            if not organ:
                console.print("[red]Specify organ for sensitive perk[/red]")
                return
            perk = SensitiveOrgansPerk(organ)
        else:
            console.print(f"[red]Unknown perk type: {perk_type}[/red]")
            return
        
        if perk:
            perk.apply_to(ctx.active_body)
            ctx.active_body.skill_book.passive_perks.append(perk)
            console.print(f"[green]✓ Gained perk: {perk.name}[/green]")
            console.print(f"[dim]{perk.description}[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error adding perk: {e}[/red]")


def cmd_magic_help(args: List[str], ctx: CommandContext):
    """Показать справку по магической системе"""
    help_text = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║                    MAGIC SYSTEM HELP                         ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]🎆 MAGIC COMMANDS[/bold yellow]

  [green]cast[/green] <skill> [target] [organ]
                            - Cast a spell using body fluids as mana
                            Example: cast "Milk Spray" 0
                            Example: cast "Cum Shot" 1 vagina
  
  [green]mana[/green]                     - Show mana status (fluids in all organs)
                            Displays: breasts, uterus, penis, testicles
  
  [green]skills[/green]                   - List all learned skills with costs
                            Shows cooldowns and availability
  
  [green]perks[/green]                    - Show active passive perks
  
  [green]learn[/green] <SkillClass>       - Learn new skill
                            Example: learn MilkSpray
  
  [green]add_perk[/green] <type> [organ]   - Add passive perk
                            Example: add_perk regen breasts
                            Example: add_perk expand penis

[bold yellow]💧 MANA SYSTEM[/bold yellow]

Each organ with fluid capacity is a mana source:
• [white]Breasts[/white] (Milk)  - White color, healing/defensive magic
• [yellow]Penis[/yellow] (Cum)   - Yellow color, offensive/summoning magic  
• [cyan]Uterus[/cyan] (Any)   - Cyan color, universal source
• [gold]Testicles[/gold] (Cum) - Gold color, high capacity

[bold]Overload Bonus:[/bold] Casting at >90% fullness gives 50% power boost!

[bold yellow]⚡ COMBO SYSTEM[/bold yellow]

Certain skills create combos when cast in sequence:
• Milk Spray → Colostrum Surge → Milk Explosion (AoE)
• Cum Shot ×3 → Cum Meteor (Ultimate)
• Dual Release available only for Futanari

[bold yellow]🎓 SKILL SCHOOLS[/bold yellow]

  [white]MILK[/white]     - Healing, shields, control (Female)
  [yellow]CUM[/yellow]      - Damage, buffs, summons (Male)
  [purple]HYBRID[/purple]   - Combined effects (Futanari only)

[bold yellow]💎 PERK TYPES[/bold yellow]

  [green]regen[/green]      - Passive fluid regeneration (+5ml/tick per rank)
  [green]expand[/green]     - +20% max volume per rank
  [green]pressure[/green]   - -20% skill cost per rank
  [green]sensitive[/green]  - +50% power when organ >50% full
    """
    console.print(help_text)        

# ============ Создание реестра команд ============

def create_registry() -> CommandRegistry:
    """Создать и настроить реестр команд."""
    registry = CommandRegistry()

    # General
    registry.register(Command("help", ["h", "?"], "Show help", "help [topic]", cmd_help, "general"))
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

    # Breasts - НОВАЯ КОМАНДА FULLNESS
    registry.register(Command("breasts", ["breast", "b"], "Breast fullness and details", "breasts [fullness|detail|status|grid] [row] [col]", cmd_breasts, "breasts"))
    
    # Старые команды груди
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
    registry.register(Command("ovary", ["ov", "ovaries"], "Ovary management", "ovary [side] [action] [args...] [idx]", cmd_ovary, "uterus"))

    # Fallopian tubes
    registry.register(Command("tube", ["ft", "tubes"], "Fallopian tube management", "tube [side] [action] [args...] [idx]", cmd_tube, "uterus"))
    
    # Combined reactions command
    registry.register(Command(
        "reactions", ["react", "r"],
        "Show all body reactions (breasts + uterus)",
        "reactions [debug]",
        cmd_reactions_all,
        "reactions"
    ))

    registry.register(Command(
        "reactions_clear", ["rclearall", "rca"],
        "Clear all reaction states",
        "reactions_clear",
        cmd_reactions_clear_all,
        "reactions"
    ))
    
    registry.register(Command(
        "vagina", ["vag", "v"],
        "Vagina fullness and fluid management",
        "vagina [idx] [fullness|add_fluid|drain|...]",
        cmd_vagina,
        "genitals"
    ))
    registry.register(Command(
        "penis_type", 
        ["ptype", "penistype", "cock_type"], 
        "Change penis type/anatomy", 
        "penis_type <type> [index]", 
        cmd_penis_type, 
        "genitals"
    ))

    # Реакции (если доступны)
    try:
        from body_sim.characters.breast_reactions import get_reaction_system, register_reaction_commands
        register_reaction_commands(registry, get_reaction_system())
        console.print("[dim]Breasts reaction commands loaded[/dim]")
    except ImportError as e:
        console.print(f"[dim]Breasts reaction commands not available: {e}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to load breasts reaction commands: {e}[/yellow]")

    try:
        from body_sim.characters.uterus_reactions import get_uterus_reaction_system, register_uterus_reaction_commands
        register_uterus_reaction_commands(registry, get_uterus_reaction_system())
        console.print("[dim]Uterus reaction commands loaded[/dim]")
    except ImportError as e:
        console.print(f"[dim]Uterus reaction commands not available: {e}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to load uterus reaction commands: {e}[/yellow]")

    # Рокси команды (если доступны)
    try:
        from body_sim.characters.roxy_migurdia import register_roxy_command
        register_roxy_command(registry)
    except ImportError:
        pass  # Не критично

    # ============ SEX / PENETRATION COMMANDS ============
    try:
        from body_sim.ui.sex_commands import register_sex_commands
        sex_handler = register_sex_commands(registry)
        console.print("[dim]Sex/penetration commands loaded[/dim]")
    except ImportError as e:
        console.print(f"[dim]Sex commands not available: {e}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to load sex commands: {e}[/yellow]")
    # ============ DEEP PENETRATION COMMANDS ============
    try:
        from body_sim.ui.deep_sex_commands import register_deep_sex_commands
        deep_handler = register_deep_sex_commands(registry)
        console.print("[dim]Deep penetration commands loaded[/dim]")
    except ImportError as e:
        console.print(f"[dim]Deep penetration commands not available: {e}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to load deep penetration commands: {e}[/yellow]")

          # ============ COMBAT COMMANDS ============
    try:
        from body_sim.combat.commands import register_combat_commands
        register_combat_commands(registry)
        console.print("[dim]Combat system integrated[/dim]")
    except ImportError as e:
        console.print(f"[dim]Combat system not available: {e}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to load combat system: {e}[/yellow]")

    return registry

    return registry

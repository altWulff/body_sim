# body_sim/ui/sex_commands.py
from typing import Dict, Optional, List, Any
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

try:
    from body_sim.ui.commands import console
except ImportError:
    console = Console()

from body_sim.systems.penetration import CrossBodyPenetration, EjaculationResult, IndexedOrganRef


class SexCommandHandler:
    def __init__(self):
        self.active_encounters: Dict[int, CrossBodyPenetration] = {}
    
    def _get_player_body(self, ctx) -> Any:
        return ctx.active_body
    
    def _get_target_body(self, ctx, target_name: str) -> Any:
        for body in ctx.bodies:
            if hasattr(body, 'name') and body.name.lower() == target_name.lower():
                return body
            if target_name.isdigit():
                idx = int(target_name)
                if 0 <= idx < len(ctx.bodies):
                    return ctx.bodies[idx]
        return None
    
    def _has_penis(self, body, index: int = 0) -> bool:
        """Проверить наличие пениса по индексу"""
        if not body:
            return False
        # Проверяем список penises[]
        if hasattr(body, 'penises') and isinstance(body.penises, list):
            return len(body.penises) > index and body.penises[index] is not None
        # Проверяем одиночный penis
        if hasattr(body, 'penis') and body.penis is not None:
            return index == 0
        return False
    
    def _get_penis(self, body, organ_name: str = "penis", index: int = 0):
        """Получить пенис из списка или одиночный"""
        # Сначала проверяем список penises[]
        if hasattr(body, 'penises') and isinstance(body.penises, list):
            if index < len(body.penises):
                return body.penises[index]
            elif len(body.penises) > 0:
                return body.penises[0]  # fallback на первый
            return None
        # Одиночный penis
        if hasattr(body, organ_name):
            return getattr(body, organ_name)
        return None
    
    def _get_target_organ(self, target, organ_type: str, index: int = 0):
        """Получить целевой орган из списка или одиночный"""
        # Проверяем множественные (vaginas[], anuses[])
        plural_name = organ_type + "s"
        if hasattr(target, plural_name):
            organs_list = getattr(target, plural_name)
            if isinstance(organs_list, list) and len(organs_list) > index:
                return organs_list[index], f"{plural_name}[{index}]"
        # Одиночный
        if hasattr(target, organ_type):
            return getattr(target, organ_type), organ_type
        return None, None
    
    def cmd_penetrate(self, args: List[str], ctx):
        """Начать проникновение: penetrate <target> [organ] [organ_idx] [penis_idx] [force]"""
        source = self._get_player_body(ctx)
        if not source:
            console.print("[red]Нет активного тела (игрока)[/red]")
            return
        
        if not args:
            console.print("[red]Usage: penetrate <target> [organ] [organ_idx] [penis_idx] [force][/red]")
            console.print("[dim]Примеры:[/dim]")
            console.print("  penetrate roxy              - vaginas[0] пенисом penises[0]")
            console.print("  penetrate roxy vagina 0 1   - vaginas[0] пенисом penises[1]")
            console.print("  penetrate roxy anus 0 0 70  - anuses[0] пенисом penises[0], сила 70")
            return
        
        target_name = args[0]
        target = self._get_target_body(ctx, target_name)
        
        if not target:
            console.print(f"[red]Цель '{target_name}' не найдена[/red]")
            return
        
        # Парсинг аргументов с умолчаниями
        organ_type = args[1] if len(args) > 1 else "vagina"
        organ_idx = 0
        penis_idx = 0
        force = 60.0
        
        # Разбор аргументов начиная со 2-й позиции
        arg_pos = 2
        try:
            if arg_pos < len(args):
                organ_idx = int(args[arg_pos])
                arg_pos += 1
            if arg_pos < len(args):
                penis_idx = int(args[arg_pos])
                arg_pos += 1
            if arg_pos < len(args):
                force = float(args[arg_pos])
        except (ValueError, IndexError):
            pass
        
        # ========== ПРОВЕРКА ПЕНИСА С FALLBACK ==========
        penis = None
        
        # Сначала пробуем получить из списка penises
        if hasattr(source, 'penises'):
            penises_attr = getattr(source, 'penises')
            
            # Если это список
            if isinstance(penises_attr, list):
                if penis_idx < len(penises_attr):
                    penis = penises_attr[penis_idx]
                else:
                    console.print(f"[red]Нет penises[{penis_idx}]. Доступно: {len(penises_attr)} пенисов[/red]")
                    return
            else:
                # Если penises существует, но не список (например, один объект)
                # и запрошен индекс 0, используем как singular
                if penis_idx == 0:
                    penis = penises_attr
                else:
                    console.print(f"[red]penises не является списком, доступен только индекс 0[/red]")
                    return
        
        # Fallback на singular 'penis', если penises не найден или penis_idx == 0
        if penis is None and hasattr(source, 'penis') and penis_idx == 0:
            penis = source.penis
        
        # Если всё ещё не нашли
        if penis is None:
            available = []
            if hasattr(source, 'penises'):
                available.append(f"penises ({type(getattr(source, 'penises')).__name__})")
            if hasattr(source, 'penis'):
                available.append("penis (singular)")
            
            console.print(f"[red]У {getattr(source, 'name', 'игрока')} нет доступных пенисов[/red]")
            if available:
                console.print(f"[dim]Найдены атрибуты: {', '.join(available)}[/dim]")
            return
        
        # Проверка эрекции
        if hasattr(penis, 'is_erect') and not penis.is_erect:
            console.print(f"[yellow]penis[{penis_idx}] не эрегирован! Используйте 'stimulate_self {penis_idx}'[/yellow]")
            return
        
        # Проверка что пенис не занят
        if getattr(penis, 'is_inserted', False):
            console.print(f"[red]penis[{penis_idx}] уже используется[/red]")
            return
        
        # ========== ПОЛУЧЕНИЕ ЦЕЛЕВОГО ОРГАНА ==========
        target_org = None
        plural_name = organ_type + "s"
        
        if hasattr(target, plural_name):
            organs_list = getattr(target, plural_name)
            if isinstance(organs_list, list):
                if organ_idx < len(organs_list):
                    target_org = organs_list[organ_idx]
                else:
                    console.print(f"[red]Нет {plural_name}[{organ_idx}]. Доступно:[/red]")
                    for line in self._get_available_organs(target, organ_type):
                        console.print(f"  {line}")
                    return
            else:
                # Если не список, но индекс 0
                if organ_idx == 0:
                    target_org = organs_list
                else:
                    console.print(f"[red]{plural_name} не является списком, доступен только индекс 0[/red]")
                    return
        elif hasattr(target, organ_type) and organ_idx == 0:
            target_org = getattr(target, organ_type)
        else:
            console.print(f"[red]У цели нет {plural_name} или {organ_type}[/red]")
            # Показываем что есть
            available_types = []
            for attr in ['vaginas', 'anuses', 'vagina', 'anus']:
                if hasattr(target, attr):
                    val = getattr(target, attr)
                    if isinstance(val, list):
                        available_types.append(f"{attr}[{len(val)}]")
                    else:
                        available_types.append(attr)
            if available_types:
                console.print(f"[yellow]Доступно:[/yellow] {', '.join(available_types)}")
            return
        
        # Проверка что орган не занят
        if getattr(target_org, 'is_penetrated', False):
            console.print(f"[red]{plural_name}[{organ_idx}] уже занят другим пенисом[/red]")
            return
        
        # ========== СОЗДАНИЕ СЕССИИ ПРОНИКНОВЕНИЯ ==========
        try:
            source_ref = IndexedOrganRef("penis", penis_idx)
            target_ref = IndexedOrganRef(organ_type, organ_idx)
            
            encounter = CrossBodyPenetration(source, target, source_ref, target_ref)
            print(encounter.source_ref, source_ref)
            success, msg = encounter.start(force)
            
            if success:
                self.active_encounters[id(source)] = encounter
                console.print(f"[green]✓ {msg}[/green]")
                
                # Показываем информацию о соединении
                target_depth = getattr(target_org, 'canal_length', '?')
                console.print(f"[dim]Соединение: penis[{penis_idx}] → {plural_name}[{organ_idx}] "
                            f"(глубина канала: {target_depth}см)[/dim]")
                self._show_penetration_ui(encounter)
            else:
                console.print(f"[yellow]⚠ {msg}[/yellow]")
                
        except ValueError as e:
            console.print(f"[red]Ошибка инициализации: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Неожиданная ошибка: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    def cmd_thrust(self, args: List[str], ctx):
        """Толчок: thrust <amount> [force]"""
        source = self._get_player_body(ctx)
        if not source:
            return
        
        encounter = self.active_encounters.get(id(source))
        if not encounter:
            console.print("[red]Нет активного проникновения[/red]")
            return
        
        if not args:
            console.print("[red]Usage: thrust <amount> [force][/red]")
            return
        
        amount = float(args[0])
        force = float(args[1]) if len(args) > 1 else 50.0
        
        success, msg = encounter.thrust(amount, force)
        color = "green" if success else "yellow"
        console.print(f"[{color}]{msg}[/{color}]")
        
        if success:
            self._show_depth_bar(encounter)
    
    def cmd_cum(self, args: List[str], ctx):
        """Эякуляция: cum [penis_idx]"""
        source = self._get_player_body(ctx)
        if not source:
            return
        
        encounter = self.active_encounters.get(id(source))
        if not encounter:
            console.print("[red]Нет активного проникновения[/red]")
            return
        
        # Если указан индекс пениса, проверяем что это тот же что в penetrate
        penis_idx = int(args[0]) if args else 0
        
        result = encounter.ejaculate()
        
        if result.success:
            fill_pct = 0
            if hasattr(encounter.target_organ, 'max_volume') and encounter.target_organ.max_volume > 0:
                fill_pct = (result.volume / encounter.target_organ.max_volume) * 100
            
            console.print(Panel(
                f"[bold magenta]✦ ЭЯКУЛЯЦИЯ ✦[/bold magenta]\n"
                f"Объем: [cyan]{result.volume:.1f}мл[/cyan]\n"
                f"Глубина: [green]{result.depth:.1f}см[/green]\n"
                f"Заполнение: [yellow]{fill_pct:.1f}%[/yellow]",
                border_style="magenta"
            ))
            
            if result.is_knotted:
                console.print("[bold red]⚠ УЗЕЛ ЗАБЛОКИРОВАЛ ВЫХОД[/bold red]")
        else:
            console.print(f"[yellow]{result.message}[/yellow]")
    
    def cmd_pullout(self, args: List[str], ctx):
        """Извлечь: pullout"""
        source = self._get_player_body(ctx)
        if not source:
            return
        
        encounter = self.active_encounters.get(id(source))
        if not encounter:
            console.print("[red]Нет активного проникновения[/red]")
            return
        
        success, msg = encounter.pullout()
        
        if success:
            console.print(f"[green]{msg}[/green]")
            del self.active_encounters[id(source)]
        else:
            console.print(f"[yellow]{msg}[/yellow]")
    
    def cmd_sex_status(self, args: List[str], ctx):
        """Статус: sex_status [target]"""
        source = self._get_player_body(ctx)
        if not source:
            return
        
        # Показываем пенисы игрока
        if hasattr(source, 'penises') and isinstance(source.penises, list):
            console.print(f"[cyan]Ваши пенисы ({len(source.penises)}):[/cyan]")
            for i, p in enumerate(source.penises):
                status = "✓ эрегирован" if p.is_erect else "✗ вялый"
                console.print(f"  [{i}] {p.current_length:.1f}см {status}")
        
        # Активное проникновение
        encounter = self.active_encounters.get(id(source))
        if encounter:
            self._show_status(encounter)
        else:
            console.print("[dim]Нет активного акта. Используйте 'penetrate <target>'[/dim]")
    
    def cmd_stimulate_self(self, args: List[str], ctx):
        """Стимуляция: stimulate_self [penis_idx] [amount]"""
        source = self._get_player_body(ctx)
        if not source:
            return
        
        # Определяем индекс пениса и силу стимуляции
        penis_idx = 0
        amount = 0.2
        
        if args:
            try:
                # Пробуем первый аргумент как индекс
                if len(args) == 1:
                    if '.' in args[0]:
                        amount = float(args[0])
                    else:
                        penis_idx = int(args[0])
                else:
                    penis_idx = int(args[0])
                    amount = float(args[1])
            except ValueError:
                amount = float(args[0]) if args else 0.2
        
        if not self._has_penis(source, penis_idx):
            console.print(f"[red]Нет пениса с индексом {penis_idx}[/red]")
            return
        
        penis = self._get_penis(source, "penis", penis_idx)
        if not penis:
            console.print("[red]Не удалось получить пенис[/red]")
            return
        
        # Стимуляция
        if hasattr(penis, 'stimulate'):
            penis.stimulate(amount)
        elif hasattr(penis, 'update_arousal'):
            penis.update_arousal(amount)
        else:
            if hasattr(penis, 'arousal'):
                penis.arousal = min(1.0, penis.arousal + amount)
            if hasattr(penis, 'is_erect') and penis.arousal > 0.7:
                penis.is_erect = True
        
        console.print(f"[magenta]Стимуляция penises[{penis_idx}]... Возбуждение: {penis.arousal:.0%}[/magenta]")
        
        if penis.is_erect:
            console.print(f"[green]Полная эрекция! Диаметр: {penis.current_diameter:.1f}см[/green]")
    
    def _show_penetration_ui(self, encounter):
        status = encounter.get_status()
        width = 40
        max_depth = status.get('max_depth', 10)
        current_depth = status.get('depth', 0)
        
        filled = int((current_depth / max(max_depth, 1)) * width)
        bar = "█" * filled + "░" * (width - filled)
        
        console.print(Panel(
            f"[bold]{status.get('source', 'Unknown')} → {status.get('target', 'Unknown')}[/bold]\n"
            f"Глубина: |{bar}| {current_depth:.1f}/{max_depth:.1f}cm",
            title="Проникновение",
            border_style="green"
        ))
    
    def _show_depth_bar(self, encounter):
        status = encounter.get_status()
        width = 30
        pct = status.get('depth_percent', 0) / 100
        filled = int(width * pct)
        bar = "█" * filled + "░" * (width - filled)
        color = "red" if pct > 0.9 else "green"
        console.print(f"[{color}]|{bar}| {status.get('depth', 0):.1f}см[/{color}]")
    
    def _show_status(self, encounter):
        status = encounter.get_status()
        table = Table(title="Статус")
        table.add_column("Параметр", style="cyan")
        table.add_column("Значение", style="green")
        
        table.add_row("Глубина", f"{status.get('depth', 0):.1f} / {status.get('max_depth', 0):.1f} см")
        table.add_row("Процент", f"{status.get('depth_percent', 0):.0f}%")
        table.add_row("Узел", "Да" if status.get('knotted') else "Нет")
        table.add_row("Сперма", f"{status.get('cum_ready', 0):.1f}мл")
        
        console.print(table)


# Глобальный обработчик
_sex_handler = SexCommandHandler()

# Функции для CommandRegistry
def cmd_penetrate(args, ctx):
    _sex_handler.cmd_penetrate(args, ctx)

def cmd_thrust(args, ctx):
    _sex_handler.cmd_thrust(args, ctx)

def cmd_cum_inside(args, ctx):
    _sex_handler.cmd_cum(args, ctx)

def cmd_pullout(args, ctx):
    _sex_handler.cmd_pullout(args, ctx)

def cmd_sex_status(args, ctx):
    _sex_handler.cmd_sex_status(args, ctx)

def cmd_stimulate_self(args, ctx):
    _sex_handler.cmd_stimulate_self(args, ctx)

def register_sex_commands(registry):
    from body_sim.ui.commands import Command
    
    registry.register(Command("penetrate", ["pen"], "Начать проникновение", "penetrate <target> [organ] [organ_idx] [penis_idx] [force]", cmd_penetrate, "sex"))
    registry.register(Command("thrust", ["move"], "Толчок", "thrust <amount> [force]", cmd_thrust, "sex"))
    registry.register(Command("cum", ["ejaculate"], "Эякуляция", "cum", cmd_cum_inside, "sex"))
    registry.register(Command("pullout", ["withdraw"], "Извлечь", "pullout", cmd_pullout, "sex"))
    registry.register(Command("sex_status", ["sexstat"], "Статус", "sex_status", cmd_sex_status, "sex"))
    registry.register(Command("stimulate_self", ["masturbate"], "Стимуляция", "stimulate_self [penis_idx] [amount]", cmd_stimulate_self, "sex"))
    
    return _sex_handler
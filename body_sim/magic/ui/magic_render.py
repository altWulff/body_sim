"""
Rich Renderer для магической системы.
"""
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from rich.layout import Layout
from rich.console import Group
from rich import box

class MagicRenderer:
    """Рендерер для отображения магических способностей"""
    
    def __init__(self, body):
        self.body = body
    
    def render_mana_status(self) -> Panel:
        """Отображение статуса маны (жидкостей)"""
        if not hasattr(self.body, 'get_mana_status'):
            return Panel("Нет магической системы", title="Мана")
        
        status = self.body.get_mana_status()
        
        # Создаём прогресс-бары для каждого источника
        progress_bars = []
        for source in status['sources']:
            color = source['color']
            bar = Progress(
                TextColumn(f"[bold {color}]{source['name'].upper():<12}[/]"),
                BarColumn(bar_width=20, complete_style=color, finished_style=color),
                TextColumn(f"[{color}]{source['current']:.0f}/{source['max']:.0f}ml {source['type']}[/]"),
                expand=False
            )
            bar.add_task("", total=source['max'], completed=source['current'])
            progress_bars.append(bar)
        
        # Общий статус
        total_color = "green" if status['total_fullness'] < 0.5 else ("yellow" if status['total_fullness'] < 0.9 else "red")
        total_bar = Progress(
            TextColumn(f"[bold {total_color}]TOTAL MANA  [/]"),
            BarColumn(bar_width=25, complete_style=total_color),
            TextColumn(f"[{total_color}]{status['total_mana']:.0f}/{status['max_mana']:.0f}ml ({status['total_fullness']*100:.0f}%)[/]"),
            expand=False
        )
        total_bar.add_task("", total=status['max_mana'], completed=status['total_mana'])
        
        content = Group(total_bar, *progress_bars)
        
        return Panel(
            content,
            title=f"[bold cyan]✨ МАГИЧЕСКАЯ ЭНЕРГИЯ: {self.body.name}[/]",
            border_style="cyan",
            box=box.ROUNDED
        )
    
    def render_skill_book(self) -> Panel:
        """Отображение книги скиллов"""
        if not hasattr(self.body, 'skill_book'):
            return Panel("Нет скиллов", title="Скиллы")
        
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
        table.add_column("🔢", style="cyan", width=4, justify="center")
        table.add_column("Название", style="green", width=20)
        table.add_column("Школа", style="white", width=10)
        table.add_column("Стоимость", style="yellow", width=25)
        table.add_column("КД", style="red", width=4, justify="center")
        table.add_column("Статус", style="bold", width=15)
        
        for idx, (name, skill) in enumerate(self.body.skill_book.skills.items(), 1):
            can_use, reason = skill.can_use(self.body)
            
            school_colors = {"MILK": "white", "CUM": "yellow", "HYBRID": "purple"}
            school_color = school_colors.get(skill.school.name, "white")
            
            costs = []
            for cost in skill.costs:
                organ = cost._get_organ(self.body)
                current = organ.current_volume if organ else 0
                costs.append(f"{cost.fluid_type.name}:{current:.0f}/{cost.amount:.0f}")
            cost_str = " | ".join(costs) if costs else "Free"
            
            if skill.current_cooldown > 0:
                status = f"[red]⌛ {skill.current_cooldown}[/]"
            elif can_use:
                status = "[green]✓ Ready[/]"
            else:
                status = f"[red]✗ {reason[:10]}...[/]"
            
            table.add_row(str(idx), name, f"[{school_color}]{skill.school.name}[/{school_color}]", cost_str, str(skill.cooldown), status)
        
        return Panel(table, title="[bold yellow]📖 КНИГА СКИЛЛОВ[/]", border_style="yellow", box=box.ROUNDED)
    
    def render_perks(self) -> Panel:
        """Отображение перков"""
        if not hasattr(self.body, 'skill_book') or not self.body.skill_book.passive_perks:
            return Panel("[dim]Нет активных перков[/]", title="Перки")
        
        perk_panels = []
        for perk in self.body.skill_book.passive_perks:
            type_colors = {"anatomical": "green", "fluid": "blue", "combat": "red", "magic": "purple"}
            color = type_colors.get(perk.perk_type.value, "white")
            rank_str = "★" * perk.current_rank + "☆" * (perk.max_rank - perk.current_rank)
            
            text = Text()
            text.append(f"{perk.name}\\n", style=f"bold {color}")
            text.append(f"{perk.description}\\n", style="dim")
            text.append(f"Ранг: {rank_str}", style="yellow")
            
            perk_panels.append(Panel(text, border_style=color, box=box.SIMPLE, width=35))
        
        return Panel(Columns(perk_panels, equal=True, expand=True), title="[bold green]💎 АКТИВНЫЕ ПЕРКИ[/]", border_style="green")
    
    def render_casting_result(self, result: dict) -> Panel:
        """Отображение результата каста"""
        if not result.get("success"):
            return Panel(f"[red]✗ {result.get('message', 'Ошибка')}[/]", title="[red]Провал[/]", border_style="red")
        
        text = Text()
        text.append(f"✨ {result['message']}\\n\\n", style="bold cyan")
        
        for res in result.get("results", []):
            if res.get("type") == "damage":
                crit = " [red]CRITICAL![/]" if res.get("critical") else ""
                text.append(f"💥 Урон: ", style="bold")
                text.append(f"{res.get('value', 0):.1f}{crit}\\n", style="red")
            elif res.get("type") == "heal":
                text.append(f"💚 Лечение: ", style="bold")
                text.append(f"{res.get('amount', 0):.1f}\\n", style="green")
            elif res.get("type") == "fill":
                text.append(f"💧 Наполнение ", style="bold")
                text.append(f"{res.get('organ', 'organ')}: ", style="cyan")
                text.append(f"+{res.get('amount', 0):.1f}ml\\n", style="blue")
        
        if result.get("duplicated"):
            text.append(f"\\n[bold yellow]⚡ Двойное применение![/]", style="yellow")
        
        return Panel(text, title="[green]✓ Успех[/]", border_style="green")

def render_magic_comparison(body1, body2) -> Table:
    """Сравнение магических способностей"""
    table = Table(title="Сравнение магических сил", box=box.DOUBLE_EDGE)
    table.add_column("Параметр", style="bold cyan")
    table.add_column(f"{body1.name}", style="green")
    table.add_column(f"{body2.name}", style="yellow")
    
    mana1 = body1.get_mana_status() if hasattr(body1, 'get_mana_status') else {'total_mana': 0, 'max_mana': 1}
    mana2 = body2.get_mana_status() if hasattr(body2, 'get_mana_status') else {'total_mana': 0, 'max_mana': 1}
    
    table.add_row("Общая мана", f"{mana1['total_mana']:.0f}/{mana1['max_mana']:.0f}", f"{mana2['total_mana']:.0f}/{mana2['max_mana']:.0f}")
    table.add_row("Заполненность", f"{mana1.get('total_fullness', 0)*100:.1f}%", f"{mana2.get('total_fullness', 0)*100:.1f}%")
    
    skills1 = len(body1.skill_book.skills) if hasattr(body1, 'skill_book') else 0
    skills2 = len(body2.skill_book.skills) if hasattr(body2, 'skill_book') else 0
    table.add_row("Количество скиллов", str(skills1), str(skills2))
    
    perks1 = len(body1.skill_book.passive_perks) if hasattr(body1, 'skill_book') else 0
    perks2 = len(body2.skill_book.passive_perks) if hasattr(body2, 'skill_book') else 0
    table.add_row("Активные перки", str(perks1), str(perks2))
    
    return table


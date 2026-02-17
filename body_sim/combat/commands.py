"""
Интеграция боевой системы в командный интерфейс body_sim
"""

from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box

from body_sim.ui.commands import Command, CommandContext
from .core import Combatant, CombatManager

console = Console()

# Глобальный менеджер боя (singleton для сессии)
_combat_manager: Optional[CombatManager] = None

def get_combat_manager() -> CombatManager:
    global _combat_manager
    if _combat_manager is None:
        _combat_manager = CombatManager()
    return _combat_manager

def reset_combat_manager():
    global _combat_manager
    _combat_manager = CombatManager()

# ============ КОМАНДЫ БОЯ ============

def cmd_combat_start(args: List[str], ctx: CommandContext):
    """Начать бой между выбранными телами."""
    global _combat_manager
    _combat_manager = CombatManager()
    manager = _combat_manager
    
    if len(ctx.bodies) < 2:
        console.print("[red]Нужно минимум 2 тела для боя![/red]")
        console.print("[dim]Используйте 'create' или 'roxy' для создания дополнительных тел[/dim]")
        return
    
    # Выбор режима
    if len(args) >= 2:
        # Конкретные индексы: combat 0 1
        try:
            idx1, idx2 = int(args[0]), int(args[1])
            body1, body2 = ctx.bodies[idx1], ctx.bodies[idx2]
        except (ValueError, IndexError):
            console.print("[red]Неверные индексы тел[/red]")
            return
    else:
        # Интерактивный выбор
        console.print("[bold cyan]Выберите бойцов:[/bold cyan]")
        for i, body in enumerate(ctx.bodies):
            name = getattr(body, 'name', f"Body_{i}")
            console.print(f"  [{i}] {name}")
        
        try:
            idx1 = int(input("Первый боец (индекс): "))
            idx2 = int(input("Второй боец (индекс): "))
            body1, body2 = ctx.bodies[idx1], ctx.bodies[idx2]
        except (ValueError, IndexError):
            console.print("[red]Неверный выбор[/red]")
            return
    
    # Создание бойцов
    name1 = getattr(body1, 'name', f"Fighter_{idx1}")
    name2 = getattr(body2, 'name', f"Fighter_{idx2}")
    
    c1 = Combatant(body1, name1)
    c2 = Combatant(body2, name2)
    
    manager.add_combatant(c1, "A")
    manager.add_combatant(c2, "B")
    manager.active = True
    
    console.print(f"\n[bold red]⚔️ БОЙ НАЧАЛСЯ![/bold red]")
    console.print(f"[blue]{name1}[/] VS [red]{name2}[/]")
    console.print("[dim]Используйте 'combat_status' для просмотра боя[/dim]")
    console.print("[dim]Используйте 'combat_turn' для хода[/dim]")

def cmd_combat_status(args: List[str], ctx: CommandContext):
    """Показать статус текущего боя."""
    manager = get_combat_manager()
    
    if not manager.active:
        console.print("[yellow]Нет активного боя. Используйте 'combat_start'[/yellow]")
        return
    
    # Создаем layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="fighters"),
        Layout(name="log", size=10)
    )
    
    # Header
    current = manager.get_current()
    turn_text = f"Раунд {manager.round} | Ход: {current.name if current else 'None'} (AP: {current.stats.ap if current else 0})"
    layout["header"].update(Panel(turn_text, style="bold red"))
    
    # Fighters
    fighter_layout = Layout()
    fighter_panels = []
    for p in manager.participants:
        fighter_panels.append(Layout(p.get_status_panel()))
    fighter_layout.split_row(*fighter_panels)
    layout["fighters"].update(fighter_layout)
    
    # Log
    log_text = "\n".join(manager.combat_log[-6:])
    layout["log"].update(Panel(log_text, title="Журнал боя", style="dim"))
    
    console.print(layout)
    
    # Таблица скиллов текущего бойца
    if current:
        table = Table(title=f"Скиллы {current.name}", box=box.ROUNDED)
        table.add_column("#", style="cyan", width=3)
        table.add_column("Название", style="green")
        table.add_column("AP", style="yellow", width=3)
        table.add_column("CD", style="red", width=3)
        table.add_column("Описание", style="dim")
        
        for i, skill in enumerate(current.skills):
            can_use = skill.can_use(current) and skill.current_cooldown == 0 and current.stats.ap >= skill.ap_cost
            style = "green" if can_use else "dim"
            cd = str(skill.current_cooldown) if skill.current_cooldown > 0 else "✓"
            table.add_row(str(i+1), skill.name, str(skill.ap_cost), cd, skill.description, style=style)
        
        console.print(table)
        console.print("[dim]Используйте: combat_use <номер_скилла> <цель>[/dim]")

def cmd_combat_use(args: List[str], ctx: CommandContext):
    """Использовать скилл в бою."""
    manager = get_combat_manager()
    
    if not manager.active:
        console.print("[red]Нет активного боя![/red]")
        return
    
    if len(args) < 1:
        console.print("[red]Usage: combat_use <skill_num> <target_name>[/red]")
        console.print("[dim]Пример: combat_use 1 Roxy[/dim]")
        console.print("[dim]Пример: combat_use 1 \"Roxy Migurdia\"[/dim]")
        return
    
    try:
        skill_idx = int(args[0]) - 1  # 1-based для пользователя
    except ValueError:
        console.print("[red]Неверный номер скила[/red]")
        return
    
    # Склеиваем все оставшиеся аргументы и убираем кавычки
    if len(args) > 1:
        target_name = " ".join(args[1:]).strip('"\'')
    else:
        # Интерактивный выбор если имя не указано
        current = manager.get_current()
        targets = [p for p in manager.participants 
                  if p != current and p.is_alive()]
        if not targets:
            console.print("[red]Нет доступных целей![/red]")
            return
        
        console.print("Доступные цели:")
        for i, t in enumerate(targets):
            console.print(f"  {i+1}. {t.name}")
        
        try:
            choice = int(input("Выберите цель (номер): ")) - 1
            target_name = targets[choice].name
        except (ValueError, IndexError):
            console.print("[red]Неверный выбор[/red]")
            return
    
    user = manager.get_current()
    if not user:
        console.print("[red]Нет активного бойца![/red]")
        return
    
    target = next((p for p in manager.participants if p.name == target_name), None)
    if not target:
        console.print(f"[red]Цель '{target_name}' не найдена![/red]")
        available = ", ".join([p.name for p in manager.participants])
        console.print(f"[dim]Доступные: {available}[/dim]")
        return
    
    result = manager.execute_skill(user, skill_idx, target)
    console.print(f"[italic]{result}[/italic]")
    
    # Автопереход хода если AP закончились
    if user.stats.ap <= 0:
        manager.next_turn()
        next_fighter = manager.get_current()
        if next_fighter:
            console.print(f"[dim]Ход завершен. Следующий: {next_fighter.name}[/dim]")
    
    # Проверка конца боя
    if manager.is_combat_end():
        winner = manager.get_winner()
        if winner:
            console.print(f"\n[bold green]🏆 Победитель: {winner}![/bold green]")
        else:
            console.print(f"\n[bold yellow]💀 Ничья![/bold yellow]")
        manager.active = False

def cmd_combat_skip(args: List[str], ctx: CommandContext):
    """Пропустить ход."""
    manager = get_combat_manager()
    if not manager.active:
        console.print("[red]Нет активного боя![/red]")
        return
    
    current = manager.get_current()
    manager.next_turn()
    manager.log(f"{current.name} пропускает ход")
    console.print(f"[dim]{current.name} пропускает ход[/dim]")

def cmd_combat_end(args: List[str], ctx: CommandContext):
    """Завершить бой досрочно."""
    manager = get_combat_manager()
    if manager.active:
        manager.active = False
        console.print("[yellow]Бой завершен досрочно[/yellow]")
    else:
        console.print("[dim]Нет активного боя[/dim]")

def register_combat_commands(registry):
    """Регистрация всех боевых команд в реестре."""
    
    registry.register(Command(
        "combat_start", ["cstart", "battle"],
        "Начать бой между телами",
        "combat_start [idx1] [idx2]",
        cmd_combat_start,
        "combat"
    ))
    
    registry.register(Command(
        "combat_status", ["cstat", "cs"],
        "Показать статус боя",
        "combat_status",
        cmd_combat_status,
        "combat"
    ))
    
    registry.register(Command(
        "combat_use", ["cuse", "atk"],
        "Использовать скилл",
        "combat_use <skill_num> <target>",
        cmd_combat_use,
        "combat"
    ))
    
    registry.register(Command(
        "combat_skip", ["cskip", "pass"],
        "Пропустить ход",
        "combat_skip",
        cmd_combat_skip,
        "combat"
    ))
    
    registry.register(Command(
        "combat_end", ["cend", "surrender"],
        "Завершить бой",
        "combat_end",
        cmd_combat_end,
        "combat"
    ))
    
    console.print("[dim]Combat commands loaded: combat_start, combat_status, combat_use, combat_skip, combat_end[/dim]")
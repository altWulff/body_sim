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
        return
    
    try:
        skill_idx = int(args[0]) - 1
    except ValueError:
        console.print("[red]Неверный номер скила[/red]")
        return
    
    # Имя цели
    if len(args) > 1:
        target_name = " ".join(args[1:]).strip('"\'')
    else:
        console.print("[red]Укажите цель: combat_use <num> <target>[/red]")
        return
    
    user = manager.get_current()
    if not user:
        console.print("[red]Нет активного бойца![/red]")
        return
    
    target = next((p for p in manager.participants if p.name == target_name), None)
    if not target:
        console.print(f"[red]Цель '{target_name}' не найдена![/red]")
        return
    
    # Проверка индекса скила
    if skill_idx < 0 or skill_idx >= len(user.skills):
        console.print(f"[red]Скилл #{skill_idx+1} не существует. Доступно: {len(user.skills)}[/red]")
        return
    
    skill = user.skills[skill_idx]
    
    # Детальная диагностика
    console.print(f"[dim]Проверка скилла '{skill.name}'...[/dim]")
    console.print(f"  AP: {user.stats.ap}/{skill.ap_cost} {'✓' if user.stats.ap >= skill.ap_cost else '✗'}")
    console.print(f"  Cooldown: {skill.current_cooldown} {'✓' if skill.current_cooldown == 0 else '✗'}")
    
    # Проверка can_use с деталями
    can_use_result = skill.can_use(user, target)
    console.print(f"  Can use: {'✓' if can_use_result else '✗'}")
    
    if not can_use_result:
        # Диагностика для конкретных скиллов
        if hasattr(skill, 'description'):
            console.print(f"[yellow]Требования: {skill.description}[/yellow]")
        
        # Проверяем анатомию для MilkSpray
        if "Milk" in skill.name:
            if not hasattr(user.body, 'breast_grid') or not user.body.breast_grid:
                console.print("[red]  Причина: Нет груди![/red]")
            else:
                try:
                    breast = user.body.breast_grid.get(0, 0)
                    fill = getattr(breast, 'fill_percentage', 0)
                    lact = getattr(breast.lactation, 'state', 'DRY') if hasattr(breast, 'lactation') else 'DRY'
                    console.print(f"  Fill: {fill}% (нужно >20%)")
                    console.print(f"  Lactation: {lact} (нужно ACTIVE или не DRY)")
                except Exception as e:
                    console.print(f"[red]  Ошибка доступа к груди: {e}[/red]")
        
        # Проверка для UterusSlam
        elif "Uterus" in skill.name:
            if not hasattr(user.body, 'uterus_system'):
                console.print("[red]  Причина: Нет матки![/red]")
            else:
                try:
                    u = user.body.uterus_system.uteri[0]
                    fill = getattr(u, 'fill_percentage', 0)
                    prolapse = getattr(u, 'prolapse_state', False)
                    console.print(f"  Fill: {fill}% (нужно >60%)")
                    console.print(f"  Prolapse: {prolapse} (если True - ОК)")
                except Exception as e:
                    console.print(f"[red]  Ошибка доступа к матке: {e}[/red]")
        
        return
    
    # Выполнение
    result = manager.execute_skill(user, skill_idx, target)
    console.print(f"[italic]{result}[/italic]")
    
    if user.stats.ap <= 0:
        manager.next_turn()
        next_f = manager.get_current()
        if next_f:
            console.print(f"[dim]Следующий ход: {next_f.name}[/dim]")
    
    if manager.is_combat_end():
        winner = manager.get_winner()
        console.print(f"\n[bold green]🏆 Победитель: {winner}![/bold green]" if winner else "\n[bold yellow]💀 Ничья![/bold yellow]")
        manager.active = False

def cmd_combat_skills_list(args: List[str], ctx: CommandContext):
    """Показать все доступные скиллы в игре."""
    from .skills import (
        MilkSpraySkill, BreastCrushSkill, UterusSlamSkill,
        ProlapseWhipSkill, EjaculationBlastSkill, OvaryBurstSkill,
        DeepPierceAttack
    )
    
    table = Table(title="Доступные скиллы для добавления", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Название", style="green")
    table.add_column("AP", style="yellow")
    table.add_column("CD", style="red")
    table.add_column("Требования", style="dim")
    
    all_skills = [
        ("milk_spray", MilkSpraySkill()),
        ("breast_crush", BreastCrushSkill()),
        ("uterus_slam", UterusSlamSkill()),
        ("prolapse_whip", ProlapseWhipSkill()),
        ("cum_blast", EjaculationBlastSkill()),
        ("ovary_burst", OvaryBurstSkill()),
        ("deep_pierce", DeepPierceAttack()),
    ]
    
    for skill_id, skill in all_skills:
        table.add_row(
            skill_id,
            skill.name,
            str(skill.ap_cost),
            str(skill.cooldown),
            skill.description[:50] + "..." if len(skill.description) > 50 else skill.description
        )
    
    console.print(table)
    console.print("[dim]Использование: combat_add_skill <fighter_name> <skill_id>[/dim]")
    console.print("[dim]Пример: combat_add_skill Alex milk_spray[/dim]")


def cmd_combat_add_skill(args: List[str], ctx: CommandContext):
    """Добавить скилл бойцу."""
    manager = get_combat_manager()
    
    if len(args) < 2:
        console.print("[red]Usage: combat_add_skill <fighter_name> <skill_id>[/red]")
        console.print("[dim]Список скиллов: combat_skills_list[/dim]")
        return
    
    fighter_name = args[0].strip('"\'')
    skill_id = args[1].lower()
    
    # Находим бойца (в активном бою или создаем временного для тела)
    fighter = None
    if manager.active:
        fighter = next((p for p in manager.participants if p.name == fighter_name), None)
    
    if not fighter:
        # Ищем в доступных телах
        body = None
        for b in ctx.bodies:
            if getattr(b, 'name', '') == fighter_name:
                body = b
                break
        
        if not body:
            console.print(f"[red]Боец '{fighter_name}' не найден![/red]")
            console.print(f"[dim]Доступные: {', '.join([getattr(b, 'name', str(i)) for i, b in enumerate(ctx.bodies)])}[/dim]")
            return
        
        # Создаем бойца если его нет в бою
        fighter = Combatant(body, fighter_name)
        if manager.active:
            team = "A" if len(manager.participants) % 2 == 0 else "B"
            manager.add_combatant(fighter, team)
            console.print(f"[dim]Боец {fighter_name} добавлен в бой (команда {team})[/dim]")
    
    # Создаем скилл по ID
    from .skills import (
        MilkSpraySkill, BreastCrushSkill, UterusSlamSkill,
        ProlapseWhipSkill, EjaculationBlastSkill, OvaryBurstSkill,
        DeepPierceAttack
    )
    
    skill_map = {
        "milk_spray": MilkSpraySkill,
        "breast_crush": BreastCrushSkill,
        "uterus_slam": UterusSlamSkill,
        "prolapse_whip": ProlapseWhipSkill,
        "cum_blast": EjaculationBlastSkill,
        "ovary_burst": OvaryBurstSkill,
        "deep_pierce": DeepPierceAttack,
    }
    
    if skill_id not in skill_map:
        console.print(f"[red]Неизвестный скилл: {skill_id}[/red]")
        console.print(f"[dim]Доступные: {', '.join(skill_map.keys())}[/dim]")
        return
    
    # Проверяем, есть ли уже такой скилл
    existing = [s for s in fighter.skills if s.name == skill_map[skill_id]().name]
    if existing:
        console.print(f"[yellow]У бойца уже есть {skill_map[skill_id]().name}[/yellow]")
        return
    
    # Добавляем скилл
    new_skill = skill_map[skill_id]()
    fighter.skills.append(new_skill)
    console.print(f"[green]✓ {fighter_name} получил скилл: {new_skill.name}[/green]")
    console.print(f"[dim]{new_skill.description}[/dim]")


def cmd_combat_remove_skill(args: List[str], ctx: CommandContext):
    """Удалить скилл у бойца."""
    manager = get_combat_manager()
    
    if len(args) < 2:
        console.print("[red]Usage: combat_remove_skill <fighter_name> <skill_num>[/red]")
        return
    
    fighter_name = args[0].strip('"\'')
    try:
        skill_idx = int(args[1]) - 1
    except ValueError:
        console.print("[red]Номер скила должен быть числом[/red]")
        return
    
    fighter = None
    if manager.active:
        fighter = next((p for p in manager.participants if p.name == fighter_name), None)
    else:
        # Ищем среди тел
        for b in ctx.bodies:
            if getattr(b, 'name', '') == fighter_name:
                # Создаем временного бойца для просмотра скиллов
                fighter = Combatant(b, fighter_name)
                break
    
    if not fighter:
        console.print(f"[red]Боец '{fighter_name}' не найден![/red]")
        return
    
    if skill_idx < 0 or skill_idx >= len(fighter.skills):
        console.print(f"[red]Неверный номер скила. У бойца {len(fighter.skills)} скиллов[/red]")
        return
    
    removed = fighter.skills.pop(skill_idx)
    console.print(f"[yellow]✗ Удален скилл: {removed.name} у {fighter_name}[/yellow]")


def cmd_combat_reset_skills(args: List[str], ctx: CommandContext):
    """Сбросить скиллы к стандартным (пересоздать из анатомии)."""
    manager = get_combat_manager()
    
    if not args:
        console.print("[red]Usage: combat_reset_skills <fighter_name>[/red]")
        return
    
    fighter_name = args[0].strip('"\'')
    
    fighter = None
    if manager.active:
        fighter = next((p for p in manager.participants if p.name == fighter_name), None)
    
    if not fighter:
        console.print(f"[red]Боец '{fighter_name}' не найден в активном бою![/red]")
        return
    
    # Пересоздаем скиллы
    old_count = len(fighter.skills)
    fighter.skills = []
    fighter._init_skills()
    console.print(f"[green]Скиллы {fighter_name} сброшены: {old_count} → {len(fighter.skills)}[/green]")
    console.print("[dim]Скиллы пересозданы на основе текущей анатомии[/dim]")


def cmd_combat_give_all_skills(args: List[str], ctx: CommandContext):
    """Дать бойцу ВСЕ скиллы (debug/cheat)."""
    manager = get_combat_manager()
    
    if not args:
        console.print("[red]Usage: combat_give_all <fighter_name>[/red]")
        return
    
    fighter_name = args[0].strip('"\'')
    
    fighter = None
    if manager.active:
        fighter = next((p for p in manager.participants if p.name == fighter_name), None)
    else:
        for b in ctx.bodies:
            if getattr(b, 'name', '') == fighter_name:
                fighter = Combatant(b, fighter_name)
                break
    
    if not fighter:
        console.print(f"[red]Боец '{fighter_name}' не найден![/red]")
        return
    
    from .skills import (
        MilkSpraySkill, BreastCrushSkill, UterusSlamSkill,
        ProlapseWhipSkill, EjaculationBlastSkill, OvaryBurstSkill,
        DeepPierceAttack
    )
    
    all_skills = [
        MilkSpraySkill(), BreastCrushSkill(), UterusSlamSkill(),
        ProlapseWhipSkill(), EjaculationBlastSkill(), OvaryBurstSkill(),
        DeepPierceAttack()
    ]
    
    added = 0
    for skill in all_skills:
        exists = [s for s in fighter.skills if s.name == skill.name]
        if not exists:
            fighter.skills.append(skill)
            added += 1
    
    console.print(f"[bold magenta]🎁 {fighter_name} получил {added} новых скиллов![/bold magenta]")
    console.print(f"[dim]Всего скиллов: {len(fighter.skills)}[/dim]")


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

    registry.register(Command(
        "combat_skills", ["cskills", "skill_list"],
        "Список всех доступных скиллов",
        "combat_skills",
        cmd_combat_skills_list,
        "combat"
    ))
    
    registry.register(Command(
        "combat_add_skill", ["cadd", "add_skill"],
        "Добавить скилл бойцу",
        "combat_add_skill <fighter_name> <skill_id>",
        cmd_combat_add_skill,
        "combat"
    ))
    
    registry.register(Command(
        "combat_remove_skill", ["crem", "remove_skill"],
        "Удалить скилл у бойца",
        "combat_remove_skill <fighter_name> <skill_num>",
        cmd_combat_remove_skill,
        "combat"
    ))
    
    registry.register(Command(
        "combat_reset_skills", ["creset"],
        "Сбросить скиллы к стандартным",
        "combat_reset_skills <fighter_name>",
        cmd_combat_reset_skills,
        "combat"
    ))
    
    registry.register(Command(
        "combat_give_all", ["call", "godmode"],
        "Дать все скиллы (debug)",
        "combat_give_all <fighter_name>",
        cmd_combat_give_all_skills,
        "combat"
    ))
    
    console.print("[dim]Combat commands loaded: combat_start, combat_status, combat_use, combat_skip, combat_end[/dim]")
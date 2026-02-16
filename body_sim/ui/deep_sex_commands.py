# body_sim/ui/deep_sex_commands.py
"""
Команды для глубокого проникновения с рисками пролапса.
Интеграция с AdvancedPenetrationEncounter.
"""

from typing import List, Dict, Any
from rich.panel import Panel
from rich.console import Console
from rich.table import Table

from body_sim.systems.ejaculation import EjaculationController

console = Console()

# Глобальный реестр сессий глубокого проникновения
_deep_sessions: Dict[int, Any] = {}  # id(body) -> AdvancedPenetrationEncounter


class DeepSexCommandHandler:
    """Обработчик команд для глубокого проникновения."""
    
    def __init__(self):
        self.active_sessions = _deep_sessions
        self.ejaculation_controllers: Dict[int, EjaculationController] = {}  # id(body) -> controller
    def cmd_deep_penetration_start(self, args: List[str], ctx):
        """
        Начать глубокое проникновение: 
        dpenetrate <target> <organ> [organ_idx] [penis_idx]
        
        Органы: vagina, anus, urethra, nipple
        """
        if not ctx.active_body:
            console.print("[red]Нет активного тела[/red]")
            return
        
        if len(args) < 2:
            console.print("[red]Usage: dpenetrate <target> <organ> [organ_idx] [penis_idx][/red]")
            console.print("Органы: vagina, anus, urethra, nipple")
            console.print("Примеры:")
            console.print("  dpenetrate roxy vagina        - vaginas[0], penises[0]")
            console.print("  dpenetrate roxy vagina 1      - vaginas[1], penises[0]")
            console.print("  dpenetrate roxy vagina 0 2    - vaginas[0], penises[2]")
            console.print("  dpenetrate roxy nipple 3      - nipple[3] (4-й сосок)")
            return
        
        target_name = args[0]
        organ_type = args[1].lower()
        
        # Безопасный парсинг индексов
        organ_idx = 0
        penis_idx = 0
        
        # Проверяем что organ_type - не число (защита от перепутанных аргументов)
        if organ_type.isdigit():
            console.print(f"[red]Ошибка: тип органа не может быть числом ('{organ_type}')[/red]")
            console.print("[dim]Правильно: dpenetrate <target> <organ> [organ_idx] [penis_idx][/dim]")
            return
        
        # Парсим индексы
        if len(args) == 3:
            # dpenetrate target organ organ_idx
            try:
                organ_idx = int(args[2])
            except ValueError:
                console.print(f"[red]Ошибка: organ_idx должен быть числом, получено '{args[2]}'[/red]")
                return
        elif len(args) >= 4:
            # dpenetrate target organ organ_idx penis_idx
            try:
                organ_idx = int(args[2])
            except ValueError:
                console.print(f"[red]Ошибка: organ_idx должен быть числом, получено '{args[2]}'[/red]")
                return
            try:
                penis_idx = int(args[3])
            except ValueError:
                console.print(f"[red]Ошибка: penis_idx должен быть числом, получено '{args[3]}'[/red]")
                return
        
        # Находим цель
        target = self._get_target(ctx, target_name)
        if not target:
            console.print(f"[red]Цель '{target_name}' не найдена[/red]")
            return
        
        # Получаем пенис (из penises)
        penis = self._get_penis(ctx.active_body, penis_idx)
        if not penis:
            console.print(f"[red]Нет пениса с индексом {penis_idx}[/red]")
            if hasattr(ctx.active_body, 'penises'):
                count = len(ctx.active_body.penises)
                console.print(f"[dim]Доступно penises: {count}[/dim]")
            return
        
        if not penis.is_erect:
            console.print("[yellow]Пенис не эрегирован! Используйте stimulate_self[/yellow]")
            return
        
        # Проверяем/создаём уретру если нужно
        if organ_type == "urethra":
            if not hasattr(target, 'urethra'):
                from body_sim.systems.advanced_penetration import create_urethra_for_body
                target.urethra = create_urethra_for_body(target)
        
        # Проверяем канал соска
        if organ_type == "nipple":
            if not self._check_nipple_access(target, organ_idx):
                return
        
        # Создаём сессию
        from body_sim.systems.advanced_penetration import AdvancedPenetrationEncounter
        
        encounter = AdvancedPenetrationEncounter(
            source_body=ctx.active_body,
            target_body=target,
            penetrating_object=penis,
            entry_organ=organ_type,
            entry_organ_idx=organ_idx
        )
        
        # === УСТАНОВКА ССЫЛОК НА ОРГАНЫ ДЛЯ ЭЯКУЛЯЦИИ ===
        if organ_type == "vagina":
            if hasattr(target, 'vaginas') and organ_idx < len(target.vaginas):
                encounter.vagina_ref = target.vaginas[organ_idx]
                # Связываем влагалище с маткой если есть
                if hasattr(target, 'uterus'):
                    encounter.uterus_ref = target.uterus
                    # Устанавливаем обратную связь для автоматического перетекания
                    encounter.vagina_ref.connected_uterus = target.uterus
            elif hasattr(target, 'vagina') and organ_idx == 0:
                encounter.vagina_ref = target.vagina
                if hasattr(target, 'uterus'):
                    encounter.uterus_ref = target.uterus
                    encounter.vagina_ref.connected_uterus = target.uterus
                    
        elif organ_type == "anus":
            if hasattr(target, 'anuses') and organ_idx < len(target.anuses):
                encounter.anus_ref = target.anuses[organ_idx]
            elif hasattr(target, 'anus') and organ_idx == 0:
                encounter.anus_ref = target.anus
                
        elif organ_type == "urethra":
            if hasattr(target, 'urethra'):
                encounter.urethra_ref = target.urethra
                
        elif organ_type == "nipple":
            # Находим сосок и связанную грудь
            nipple = self._get_nipple(target, organ_idx)
            if nipple and nipple.areola:
                # Находим Breast объект через areola
                if hasattr(target, 'breast_grid'):
                    for row in target.breast_grid.rows:
                        for breast in row:
                            if breast.areola == nipple.areola:
                                encounter.breast_ref = breast
                                encounter.nipple_ref = nipple
                                break
        
        # Стартуем базовое проникновение
        success, msg = self._start_basic_penetration(encounter, organ_type, target, organ_idx, penis)
        if not success:
            console.print(f"[red]{msg}[/red]")
            return
        
        encounter.is_active = True
        self.active_sessions[id(ctx.active_body)] = encounter
        
        # Создаем контроллер эякуляции сразу
        from body_sim.systems.ejaculation import EjaculationController
        self.ejaculation_controllers[id(ctx.active_body)] = EjaculationController(encounter)
        
        console.print(f"[green]✓ Глубокое проникновение начато: {organ_type}[{organ_idx}][/green]")
        console.print(f"[dim]{msg}[/dim]")
        console.print(encounter.get_status_display())
    
    def cmd_advance_deep(self, args: List[str], ctx):
        """Продвинуться глубже: dadvance <cm> [force]"""
        session = self._get_session(ctx)
        if not session:
            return
        
        if not args:
            console.print("[red]Usage: dadvance <cm> [force][/red]")
            return
        
        try:
            amount = float(args[0])
            force = float(args[1]) if len(args) > 1 else 60.0
        except ValueError as e:
            console.print(f"[red]Ошибка: аргумент должен быть числом ({e})[/red]")
            return
        
        success, msg = session.advance(amount, force)
        
        color = "green" if success else "yellow"
        console.print(f"[{color}]{msg}[/{color}]")
        
        if success:
            console.print(session.get_status_display())
    
    def cmd_withdraw_deep(self, args: List[str], ctx):
        """
        Извлечь с риском пролапса: dpullout [cm] [force]
        
        force: 0-1, чем выше - тем больше риск пролапса
        """
        session = self._get_session(ctx)
        if not session:
            return
        
        try:
            amount = float(args[0]) if args else 5.0
            force = float(args[1]) if len(args) > 1 else 0.3
        except ValueError:
            console.print("[red]Ошибка: аргументы должны быть числами[/red]")
            return
        
        if force > 0.8:
            console.print("[bold red]⚠ СИЛЬНОЕ ТЯГОВОЕ УСИЛИЕ! Высокий риск травмы![/bold red]")
        
        success, msg = session.withdraw(amount, force)
        console.print(msg)
        
        if not session.is_active:
            # Сессия закрыта
            if id(ctx.active_body) in self.active_sessions:
                del self.active_sessions[id(ctx.active_body)]
        else:
            console.print(session.get_status_display())

    def cmd_deep_cum(self, args: List[str], ctx):
        """Кончить в текущей глубокой зоне: dcum [volume] [force]"""
        session = self._get_session(ctx)
        if not session:
            return
        
        try:
            volume = float(args[0]) if args else None
            force = float(args[1]) if len(args) > 1 else 1.0
        except ValueError:
            console.print("[red]Аргументы должны быть числами[/red]")
            return
        
        # Получаем или создаем контроллер
        body_id = id(ctx.active_body)
        if body_id not in self.ejaculation_controllers:
            from body_sim.systems.ejaculation import EjaculationController
            self.ejaculation_controllers[body_id] = EjaculationController(session)
        
        controller = self.ejaculation_controllers[body_id]
        
        # Выполняем эякуляцию
        result = controller.ejaculate(requested_volume=volume, force=force)
        
        # Отображаем результат
        if not result.success:
            console.print(f"[red]✗ {result.messages[0] if result.messages else 'Ошибка эякуляции'}[/red]")
            return
        
        # Определяем цвета по зоне
        zone_colors = {
            'VAGINA_CANAL': 'pink',
            'CERVIX': 'red',
            'UTERUS_CAVITY': 'magenta',
            'FALLOPIAN_TUBE': 'yellow',
            'OVARY': 'bright_red',
            'BREAST_MILK_DUCT': 'cyan',
        }
        color = zone_colors.get(result.zone.name, 'white')
        
        # Создаем панель с деталями
        content = [
            f"[bold {color}]Зона:[/bold {color}] {result.zone.name.replace('_', ' ')}",
            f"[bold]Цель:[/bold] {type(result.target_organ).__name__ if result.target_organ else 'Unknown'}",
            f"[bold blue]Объем:[/bold blue] {result.volume_ejaculated:.1f} мл ({result.pulses} пульс.)",
            f"[bold green]Принято:[/bold green] {result.volume_absorbed:.1f} мл",
        ]
        
        if result.volume_overflow > 0:
            content.append(f"[bold red]Переполнение:[/bold red] {result.volume_overflow:.1f} мл")
        
        if result.special_effect:
            content.append(f"\n[italic yellow]{result.special_effect}[/italic yellow]")
        
        # Показываем остаток спермы
        if session.penetrating_object and hasattr(session.penetrating_object, 'get_available_volume'):
            remaining = session.penetrating_object.get_available_volume()
            content.append(f"\n[dim]Остаток спермы: {remaining:.1f} мл[/dim]")
        
        console.print(Panel(
            "\n".join(content),
            title=f"[bold magenta]✦ ЭЯКУЛЯЦИЯ ✦[/bold magenta]",
            border_style="magenta"
        ))
        
        # Показываем предупреждения если есть (с защитой от не-строк)
        for msg in result.messages:
            msg_str = str(msg)  # Защита: конвертируем в строку
            if "Ошибка" in msg_str or "error" in msg_str.lower():
                console.print(f"[red]{msg_str}[/red]")
            else:
                console.print(f"[dim]{msg_str}[/dim]")
        
        # Если переполнение - показываем визуальный эффект
        if result.volume_overflow > result.volume_ejaculated * 0.3:
            console.print("[bold red]💦 Жидкость вытекает наружу с силой![/bold red]")


    def cmd_deep_status(self, args: List[str], ctx):
        """Статус глубокого проникновения: dstatus"""
        session = self._get_session(ctx)
        if not session:
            console.print("[dim]Нет активного глубокого проникновения[/dim]")
            return
        
        # Показываем статус
        console.print(session.get_status_display())
        
        # Показываем ближайшие landmarks для отладки
        if session.landmarks:
            next_lm = None
            for lm in sorted(session.landmarks, key=lambda x: x.depth_cm):
                if lm.depth_cm > session.state.current_depth:
                    next_lm = lm
                    break
            
            if next_lm:
                console.print(f"\n[dim]Следующая точка: {next_lm.description} на глубине {next_lm.depth_cm}см[/dim]")
                console.print(f"[dim]Требуется сила: {next_lm.resistance_factor * 100:.0f}[/dim]")
        else:
            console.print("[red]Нет landmarks![/red]")
        # Дополнительная информация о рисках
        if session.state.is_in_uterus and session.uterus_ref:
            from body_sim.systems.advanced_penetration import ProlapseRiskCalculator
            risk, factors = ProlapseRiskCalculator.calculate_uterine_prolapse_risk(
                session.state, session.uterus_ref, force_withdrawal=0.5
            )
            if risk > 0.2:
                console.print(f"\n[yellow]⚠ Риск пролапса при выходе: {risk:.0%}[/yellow]")
                console.print(f"[dim]{factors}[/dim]")
    
    def _get_session(self, ctx):
        """Получить активную сессию."""
        session = self.active_sessions.get(id(ctx.active_body))
        if not session:
            console.print("[red]Нет активного глубокого проникновения[/red]")
            return None
        return session
    
    def _get_target(self, ctx, name: str):
        """Найти целевое тело."""
        # Сначала проверяем по имени
        for body in ctx.bodies:
            if hasattr(body, 'name') and body.name.lower() == name.lower():
                return body
        
        # Пробуем как индекс
        if name.isdigit():
            idx = int(name)
            if 0 <= idx < len(ctx.bodies):
                return ctx.bodies[idx]
        
        return None
    
    def _get_penis(self, body, idx: int):
        """Получить пенис из списка penises."""
        if hasattr(body, 'penises'):
            penises = body.penises
            if isinstance(penises, list) and idx < len(penises):
                return penises[idx]
            elif not isinstance(penises, list) and idx == 0:
                # Одиночный пенис обернутый не в список
                return penises
        # Fallback на singular
        if hasattr(body, 'penis') and idx == 0:
            return body.penis
        return None
    
    def _check_nipple_access(self, body, idx: int) -> bool:
        """Проверить доступ к соску по индексу."""
        if not hasattr(body, 'breast_grid'):
            console.print("[red]У цели нет груди[/red]")
            return False
        
        # Собираем все соски со всех грудей
        all_nipples = []
        for row in body.breast_grid.rows:
            for breast in row:
                if breast.areola and breast.areola.nipples:
                    for nipple in breast.areola.nipples:
                        all_nipples.append(nipple)
        
        if idx >= len(all_nipples):
            console.print(f"[red]Сосок с индексом {idx} не найден (всего {len(all_nipples)})[/red]")
            return False
        
        nipple = all_nipples[idx]
        if nipple.gape_diameter < 0.3:
            console.print(
                f"[red]Сосок {idx} слишком закрыт! "
                f"Gape: {nipple.gape_diameter:.2f}см. Раскройте сначала.[/red]"
            )
            return False
        
        return True
    
    def _start_basic_penetration(self, encounter, organ_type, target, organ_idx, penis_obj) -> tuple:
        """Начать базовое проникновение перед глубоким."""
        from body_sim.systems.penetration import InsertableObject
        
        # Создаём InsertableObject из пениса
        ins_obj = InsertableObject(
            name=f"penis_{encounter.source_body.name}",
            length=getattr(penis_obj, 'current_length', getattr(penis_obj, 'base_length', 15.0)),
            diameter=getattr(penis_obj, 'current_diameter', getattr(penis_obj, 'base_girth', 12.0) / 3.14),
            rigidity=0.9 if penis_obj.is_erect else 0.5
        )
        
        # Для вагины используем существующую логику
        if organ_type == "vagina":
            if hasattr(target, 'vaginas') and organ_idx < len(target.vaginas):
                vagina = target.vaginas[organ_idx]
                success, msg = vagina.insert_object(ins_obj, 60.0)
                return success, msg
            else:
                return False, f"Нет vaginas[{organ_idx}]"
        
        # Для ануса
        elif organ_type == "anus":
            if hasattr(target, 'anuses') and organ_idx < len(target.anuses):
                anus = target.anuses[organ_idx]
                success, msg = anus.insert_object(ins_obj, 60.0)
                return success, msg
            elif hasattr(target, 'anus') and organ_idx == 0:
                success, msg = target.anus.insert_object(ins_obj, 60.0)
                return success, msg
            else:
                return False, f"Нет anuses[{organ_idx}]"
        
        # Для уретры
        elif organ_type == "urethra":
            if hasattr(target, 'urethra'):
                success, msg = target.urethra.insert_object(ins_obj, 60.0)
                if success:
                    target.urethra.has_been_penetrated = True
                return success, msg
            else:
                return False, "Нет уретры"
        
        # Для nipple
        elif organ_type == "nipple":
            # Находим сосок
            nipple = self._get_nipple(target, organ_idx)
            if nipple:
                from body_sim.systems.advanced_penetration import create_nipple_canal
                canal = create_nipple_canal(nipple)
                success, msg = canal.insert_object(ins_obj, 60.0)
                return success, msg
            else:
                return False, f"Нет nipple[{organ_idx}]"
        
        return True, "Начало проникновения"
    
    def _get_nipple(self, body, idx: int):
        """Получить сосок по глобальному индексу."""
        if not hasattr(body, 'breast_grid'):
            return None
        
        all_nipples = []
        for row in body.breast_grid.rows:
            for breast in row:
                if breast.areola and breast.areola.nipples:
                    for nipple in breast.areola.nipples:
                        all_nipples.append(nipple)
        
        if idx < len(all_nipples):
            return all_nipples[idx]
        return None


# Функции для регистрации в CommandRegistry
def register_deep_sex_commands(registry):
    """Зарегистрировать команды глубокого проникновения."""
    from body_sim.ui.commands import Command
    
    handler = DeepSexCommandHandler()
    
    commands = [
        Command(
            "dpenetrate", ["dp", "deeppen"],
            "Начать глубокое проникновение",
            "dpenetrate <target> <organ> [organ_idx] [penis_idx]",
            handler.cmd_deep_penetration_start,
            "deep_sex"
        ),
        Command(
            "dadvance", ["da", "deepadv"],
            "Продвинуться глубже",
            "dadvance <cm> [force]",
            handler.cmd_advance_deep,
            "deep_sex"
        ),
        Command(
            "dpullout", ["dpo", "deepout"],
            "Извлечь (с риском пролапса)",
            "dpullout [cm] [force]",
            handler.cmd_withdraw_deep,
            "deep_sex"
        ),
        Command(
            "dcum", ["d ejaculate"],
            "Кончить в текущей глубокой зоне",
            "dcum [volume]",
            handler.cmd_deep_cum,
            "deep_sex"
        ),
        Command(
            "dstatus", ["ds"],
            "Статус глубокого проникновения",
            "dstatus",
            handler.cmd_deep_status,
            "deep_sex"
        ),
    ]
    
    for cmd in commands:
        registry.register(cmd)
    
    return handler

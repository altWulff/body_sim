# body_sim/ui/sex_commands.py
from typing import Dict, Optional, List, Any
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

try:
    from body_sim.ui.commands import console
except ImportError:
    console = Console()

from body_sim.systems.penetration import CrossBodyPenetration, EjaculationResult, IndexedOrganRef, InsertableObject


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
        """Стимуляция органа: stimulate_self [organ_type] [index] [amount]"""
        source = self._get_player_body(ctx)
        if not source:
            return
        
        if not args:
            console.print("[red]Usage: stimulate_self [organ_type] [index] [amount][/red]")
            console.print("[dim]Органы: penis, vagina, clit, anus, breast[/dim]")
            return
        
        organ_type = args[0].lower()
        index = 0
        amount = 0.2
        
        # Парсинг аргументов
        if organ_type.isdigit():
            # Старая сигнатура: stimulate_self 0 0.5 (только для пениса)
            organ_type = "penis"
            index = int(args[0])
            if len(args) > 1:
                amount = float(args[1])
        else:
            if len(args) > 1:
                try:
                    index = int(args[1])
                except ValueError:
                    pass
            if len(args) > 2:
                try:
                    amount = float(args[2])
                except ValueError:
                    pass
        
        # === СПЕЦИАЛЬНАЯ ОБРАБОТКА ГРУДИ ===
        if organ_type in ["breast", "breasts", "tit", "tits", "boob", "boobs"]:
            if not hasattr(source, 'breast_grid') or source.breast_grid is None:
                console.print(f"[red]У персонажа нет груди[/red]")
                return
            
            # Получаем все груди из сетки
            all_breasts = source.breast_grid.all()
            if not all_breasts:
                console.print(f"[red]Грудная сетка пуста[/red]")
                return
            
            if index >= len(all_breasts):
                console.print(f"[red]Нет груди [{index}]. Доступно: {len(all_breasts)}[/red]")
                return
            
            breast = all_breasts[index]
            
            if not hasattr(breast, 'stimulate'):
                console.print(f"[red]Эта грудь не поддерживает стимуляцию[/red]")
                return
            
            # Стимуляция
            breast.stimulate(amount)
            
            console.print(f"\n[magenta]Стимуляция breasts[{index}] (+{amount:.1f})[/magenta]")
            console.print(f"  Возбуждение: [cyan]{breast.arousal:.0%}[/cyan]")
            console.print(f"  Удовольствие: [green]{breast.pleasure:.1f}[/green]")
            
            # Специфично для груди
            if hasattr(breast, 'lactation') and breast.lactation.state.value >= 2:
                console.print(f"  [blue]↳ Молочные железы активированы[/blue]")
            if hasattr(breast, 'areola') and breast.areola.nipples:
                erect_count = sum(1 for n in breast.areola.nipples if getattr(n, 'is_erect', False))
                if erect_count > 0:
                    console.print(f"  [yellow]↳ Соски эрегированы ({erect_count}/{len(breast.areola.nipples)})[/yellow]")
            return
        
        # === ОСТАЛЬНЫЕ ОРГАНЫ (как было) ===
        organ_map = {
            "vagina": "vaginas", "vaginas": "vaginas", "pussy": "vaginas", 
            "clit": "clitorises", "clitoris": "clitorises",
            "penis": "penises", "penises": "penises", "cock": "penises", "dick": "penises",
            "anus": "anuses", "anuses": "anuses", "ass": "anuses", "butt": "anuses"
        }
        
        attr_name = organ_map.get(organ_type)
        if not attr_name:
            console.print(f"[red]Неизвестный орган: {organ_type}[/red]")
            return
        
        if not hasattr(source, attr_name):
            console.print(f"[red]У персонажа нет {attr_name}[/red]")
            return
        
        organs = getattr(source, attr_name)
        if not isinstance(organs, list) or not organs:
            console.print(f"[red]{attr_name} пуст или не является списком[/red]")
            return
        
        if index >= len(organs):
            console.print(f"[red]Нет {attr_name}[{index}]. Доступно: {len(organs)}[/red]")
            return
        
        organ = organs[index]
        
        if not hasattr(organ, 'stimulate'):
            console.print(f"[red]Этот орган не поддерживает стимуляцию[/red]")
            return
        
        # Стимуляция
        organ.stimulate(amount)
        
        # Вывод
        console.print(f"\n[magenta]Стимуляция {attr_name}[{index}] (+{amount:.1f})[/magenta]")
        console.print(f"  Возбуждение: [cyan]{organ.arousal:.0%}[/cyan]")
        console.print(f"  Удовольствие: [green]{organ.pleasure:.1f}[/green]")
        
        # Специфичные эффекты
        if attr_name == "penises":
            if hasattr(organ, 'is_erect') and organ.is_erect:
                console.print(f"  [green]↳ Эрекция: {organ.current_diameter:.1f}см[/green]")
        elif attr_name == "vaginas":
            if hasattr(organ, 'lubrication'):
                lub_color = "green" if organ.lubrication > 0.6 else "yellow" if organ.lubrication > 0.3 else "red"
                console.print(f"  [{lub_color}]↳ Смазка: {organ.lubrication:.0%}[/{lub_color}]")
        elif attr_name == "clitorises":
            if hasattr(organ, 'is_erect') and organ.is_erect:
                console.print(f"  [magenta]↳ Клитор эрегирован: {organ.current_length:.1f}см[/magenta]")
        elif attr_name == "anuses":
            if hasattr(organ, 'sphincter_tone'):
                tone = organ.sphincter_tone
                state = "расслаблен" if tone < 0.3 else "напряжен" if tone > 0.7 else "норма"
                console.print(f"  [dim]↳ Тонус: {state} ({tone:.0%})[/dim]")

    def cmd_insert_toy(self, args: List[str], ctx):
        """Вставить игрушку/дилдо: insert_toy <target> <organ_idx> [type/size] [length] [diameter]"""
        source = self._get_player_body(ctx)
        if not source:
            console.print("[red]Нет активного тела[/red]")
            return
        
        if len(args) < 2:
            console.print("[red]Usage: insert_toy <target_name|index> <organ_idx> [type|length] [diameter] [force][/red]")
            console.print("[dim]Примеры:[/dim]")
            console.print("  insert_toy roxy 0           - вставить стандартное дилдо в vagina[0]")
            console.print("  insert_toy roxy 0 horse     - предустановленный тип 'horse'")
            console.print("  insert_toy roxy 0 20 4      - длина 20см, диаметр 4см")
            return
        
        # Парсинг цели (как в penetrate)
        target = self._get_target_body(ctx, args[0])
        if not target:
            console.print(f"[red]Цель '{args[0]}' не найдена[/red]")
            return
        
        organ_idx = int(args[1])
        
        # Получаем вагину
        if not hasattr(target, 'vaginas') or organ_idx >= len(target.vaginas):
            console.print(f"[red]Нет vaginas[{organ_idx}][/red]")
            return
        
        vagina = target.vaginas[organ_idx]
        
        # Параметры дилдо
        length = 15.0
        diameter = 3.0
        rigidity = 0.9
        toy_type = "dildo"
        force = 50.0
        
        # Предустановленные типы
        presets = {
            "small": (10, 2.5, 0.8),
            "medium": (15, 3.5, 0.9),
            "large": (20, 4.5, 0.95),
            "huge": (25, 6.0, 1.0),
            "horse": (25, 5.0, 0.9),
            "canine": (18, 4.0, 0.85),  # с узлом можно добавить логику
            "slim": (20, 2.0, 0.7),
            "inflatable": (15, 3.0, 0.5)  # можно накачивать
        }
        
        arg_idx = 2
        if arg_idx < len(args):
            preset = args[arg_idx].lower()
            if preset in presets:
                length, diameter, rigidity = presets[preset]
                toy_type = preset
                arg_idx += 1
            else:
                # Парсим как числа
                try:
                    length = float(args[arg_idx])
                    if arg_idx + 1 < len(args):
                        diameter = float(args[arg_idx + 1])
                        arg_idx += 2
                    else:
                        arg_idx += 1
                except ValueError:
                    console.print(f"[red]Неизвестный тип '{preset}'. Доступные: {', '.join(presets.keys())}[/red]")
                    return
        
        # Сила вставки
        if arg_idx < len(args):
            force = float(args[arg_idx])
        
        # Создаем InsertableObject
        toy = InsertableObject(
            name=f"{toy_type}_dildo",
            length=length,
            diameter=diameter,
            rigidity=rigidity,
            texture="silicone"
        )
        
        # Проверка размера vs растяжение вагины
        max_diameter = vagina.rest_diameter * vagina.max_stretch_ratio
        if diameter > max_diameter:
            console.print(f"[red]Слишком большое! Макс диаметр для этой вагины: {max_diameter:.1f}см[/red]")
            console.print(f"[dim]Текущий диаметр вагины: {vagina.rest_diameter:.1f}см, "
                         f"растяжимость: {vagina.max_stretch_ratio:.1f}x[/dim]")
            return
        
        # Попытка вставки
        success, msg = vagina.insert_object(toy, force)
        
        if success:
            console.print(f"[green]✓ {msg}[/green]")
            console.print(f"[cyan]Вставлено {toy_type}: {length}см × {diameter}см[/cyan]")
            
            # Обновляем растяжение вагины если нужно
            if diameter > vagina.rest_diameter:
                vagina.current_dilation = max(vagina.current_dilation, diameter)
                stretch_ratio = diameter / vagina.rest_diameter
                console.print(f"[yellow]Вагина растянута до {stretch_ratio:.1f}x[/yellow]")
        else:
            console.print(f"[red]Не удалось: {msg}[/red]")

    def cmd_advance_toy(self, args: List[str], ctx):
        """Продвинуть/вытащить игрушку: advance_toy <target> <organ_idx> <amount> [force]"""
        if len(args) < 3:
            console.print("[red]Usage: advance_toy <target> <organ_idx> <amount> [force][/red]")
            console.print("[dim]amount > 0 - вглубь, amount < 0 - наружу[/dim]")
            return
        
        target = self._get_target_body(ctx, args[0])
        if not target:
            return
        
        organ_idx = int(args[1])
        amount = float(args[2])
        force = float(args[3]) if len(args) > 3 else 60.0
        
        if not hasattr(target, 'vaginas') or organ_idx >= len(target.vaginas):
            return
        
        vagina = target.vaginas[organ_idx]
        
        if not vagina.is_penetrated:
            console.print("[red]Вагина пуста[/red]")
            return
        
        # Находим последний вставленный объект (или по имени)
        last_obj = vagina.inserted_objects[-1].object if vagina.inserted_objects else None
        if not last_obj:
            return
        
        if amount > 0:
            success, msg = vagina.advance_object(last_obj.name, amount, force)
        else:
            success, msg = vagina.withdraw_object(last_obj.name, abs(amount), speed=abs(amount))
            if success and last_obj.inserted_depth <= 0:
                console.print(f"[green]Дилдо полностью извлечено[/green]")
                return
        
        color = "green" if success else "yellow"
        console.print(f"[{color}]{msg}[/{color}]")
        if success:
            pct = (last_obj.inserted_depth / vagina.canal_length) * 100
            console.print(f"[dim]Глубина: {last_obj.inserted_depth:.1f}см ({pct:.0f}%)[/dim]")
    
    
    def cmd_remove_toy(self, args: List[str], ctx):
        """Быстрое извлечение игрушки"""
        if len(args) < 2:
            console.print("[red]Usage: remove_toy <target> <organ_idx>[/red]")
            return
        
        target = self._get_target_body(ctx, args[0])
        organ_idx = int(args[1])
        
        if not hasattr(target, 'vaginas') or organ_idx >= len(target.vaginas):
            return
        
        vagina = target.vaginas[organ_idx]
        
        # Извлекаем все объекты
        removed = []
        for data in list(vagina.inserted_objects):
            vagina.withdraw_object(data.object.name, 999, speed=10)  # 999 чтобы точно вытащить
            removed.append(data.object.name)
        
        if removed:
            console.print(f"[green]Извлечено: {', '.join(removed)}[/green]")
        else:
            console.print("[dim]Нечего извлекать[/dim]")
    
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

def cmd_insert_toy(args, ctx):
    _sex_handler.cmd_insert_toy(args, ctx)

def cmd_advance_toy(args, ctx):
    _sex_handler.cmd_advance_toy(args, ctx)

def cmd_remove_toy(args, ctx):
    _sex_handler.cmd_remove_toy(args, ctx)

def register_sex_commands(registry):
    from body_sim.ui.commands import Command
    
    registry.register(Command("penetrate", ["pen"], "Начать проникновение", "penetrate <target> [organ] [organ_idx] [penis_idx] [force]", cmd_penetrate, "sex"))
    registry.register(Command("thrust", ["move"], "Толчок", "thrust <amount> [force]", cmd_thrust, "sex"))
    registry.register(Command("cum", ["ejaculate"], "Эякуляция", "cum", cmd_cum_inside, "sex"))
    registry.register(Command("pullout", ["withdraw"], "Извлечь", "pullout", cmd_pullout, "sex"))
    registry.register(Command("sex_status", ["sexstat"], "Статус", "sex_status", cmd_sex_status, "sex"))
    registry.register(Command(
        "stimulate_self", 
        ["masturbate", "stim", "touch"], 
        "Стимуляция своего органа", 
        "stimulate_self [organ_type] [index] [amount]",
        cmd_stimulate_self, 
        "sex"
    ))
    registry.register(Command(
        "insert_toy", ["toy", "dildo"], 
        "Вставить игрушку/дилдо", 
        "insert_toy <target> <idx> [type|length] [diam] [force]",
        cmd_insert_toy,
        "sex"
    ))
    registry.register(Command(
        "advance_toy", ["move_toy", "push"], 
        "Продвинуть/вытащить игрушку", 
        "advance_toy <target> <idx> <amount>",
        cmd_advance_toy,
        "sex"
    ))
    registry.register(Command(
        "remove_toy", ["pullout_toy"], 
        "Извлечь игрушку", 
        "remove_toy <target> <idx>",
        cmd_remove_toy,
        "sex"
    ))
    
    return _sex_handler
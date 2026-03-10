# === commands/breasts.py (исправленный) ===
"""
Команды для управления грудью BodySim 2.0
"""

from typing import Optional
from rich.table import Table
from rich.panel import Panel

from body_sim.commands.base import CommandRegistry, CommandContext
from body_sim.commands.fluids import find_component_by_path
from body_sim.core.fluids import Fluid, FluidType
from body_sim.anatomy.chest import CupSize, Breasts

def get_breast(ctx: CommandContext, side: str = "left"):
    """Получить грудь по стороне."""
    if not hasattr(ctx.body, 'breasts') or ctx.body.breasts is None:
        ctx.console.print("[red]No breasts[/red]")
        return None
    
    if side.lower() in ("left", "l", "0"):
        return ctx.body.breasts.left
    elif side.lower() in ("right", "r", "1"):
        return ctx.body.breasts.right
    elif side.lower() in ("both", "b"):
        return None
    else:
        ctx.console.print(f"[red]Invalid side: {side} (use left/right/both)[/red]")
        return None

def register_breast_commands(registry: CommandRegistry):
    
    def cmd_breasts_show(ctx: CommandContext, side: str = "left"):
        """Показать состояние груди: breasts.show [left/right/both]"""
        if side.lower() in ("both", "b"):
            left = ctx.body.breasts.left if ctx.body.breasts else None
            right = ctx.body.breasts.right if ctx.body.breasts else None
            
            if not left or not right:
                ctx.console.print("[red]No breasts[/red]")
                return
            
            table = Table(title="Breasts Status")
            table.add_column("Parameter", style="cyan")
            table.add_column("Left", style="green")
            table.add_column("Right", style="yellow")
            
            # ИСПРАВЛЕНО: используем .state.name вместо ._state
            left_state = left.state.name if hasattr(left.state, 'name') else str(left.state)
            right_state = right.state.name if hasattr(right.state, 'name') else str(right.state)
            
            left_lact = "Unknown"
            right_lact = "Unknown"
            try:
                if hasattr(left.lactation, 'profile') and hasattr(left.lactation.profile, 'state'):
                    left_lact = left.lactation.profile.state.name if hasattr(left.lactation.profile.state, 'name') else str(left.lactation.profile.state)
                if hasattr(right.lactation, 'profile') and hasattr(right.lactation.profile, 'state'):
                    right_lact = right.lactation.profile.state.name if hasattr(right.lactation.profile.state, 'name') else str(right.lactation.profile.state)
            except:
                pass
            
            table.add_row("Cup", left.current_cup.name, right.current_cup.name)
            table.add_row("State", left_state, right_state)
            table.add_row("Filled", f"{left.filled:.1f}ml", f"{right.filled:.1f}ml")
            table.add_row("Pressure", f"{left.pressure:.2f}", f"{right.pressure:.2f}")
            table.add_row("Lactation", left_lact, right_lact)
            table.add_row("Stretch", f"{left.inflation.profile.stretch_ratio:.2f}x", f"{right.inflation.profile.stretch_ratio:.2f}x")
            
            ctx.console.print(table)
        else:
            breast = get_breast(ctx, side)
            if not breast:
                return
            
            # Детальная информация по одной груди
            table = Table(title=f"Breast ({side.title()}) - {breast.current_cup.name}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            # ИСПРАВЛЕНО: state как строка
            state_str = breast.state.name if hasattr(breast.state, 'name') else str(breast.state)
            
            table.add_row("Base Cup", breast.cup_size.name)
            table.add_row("Volume", f"{breast.volume:.1f}ml")  # ИСПРАВЛЕНО: убрано current_volume
            table.add_row("Filled", f"{breast.filled:.1f}ml / {breast._max_volume:.1f}ml")
            table.add_row("Fill Ratio", f"{breast.fill_ratio*100:.1f}%")
            table.add_row("State", state_str)
            table.add_row("Pressure", f"{breast.pressure:.2f}")
            table.add_row("Sag", f"{breast.sag:.3f}")
            table.add_row("Elasticity", f"{breast.elasticity:.2f}")
            
            # Nipple
            nipple = breast.areola.nipples[0] if breast.areola.nipples else None
            if nipple:
                table.add_row("Nipple Gape", f"{nipple.gape_diameter:.2f}cm")
                table.add_row("Nipple Erect", "Yes" if nipple.is_erect else "No")
            
            # Lactation
            lact_state = "Unknown"
            try:
                if hasattr(breast.lactation, 'profile') and hasattr(breast.lactation.profile, 'state'):
                    lact_state = breast.lactation.profile.state.name if hasattr(breast.lactation.profile.state, 'name') else str(breast.lactation.profile.state)
            except:
                pass
            
            table.add_row("Lactation State", lact_state)
            
            if hasattr(breast.lactation, 'profile'):
                try:
                    hormone = getattr(breast.lactation.profile, 'hormone_level', 0)
                    table.add_row("Hormone Level", f"{hormone:.2f}")
                except:
                    pass
            
            if hasattr(breast.lactation, '_total_produced'):
                try:
                    table.add_row("Milk Produced", f"{breast.lactation._total_produced:.1f}ml")
                except:
                    pass
            
            # Inflation
            if hasattr(breast.inflation, 'profile'):
                table.add_row("Stretch Ratio", f"{breast.inflation.profile.stretch_ratio:.2f}x")
                if hasattr(breast.inflation, 'get_skin_tension'):
                    table.add_row("Skin Tension", f"{breast.inflation.get_skin_tension():.1%}")
                if hasattr(breast.inflation.profile, 'stretch_marks'):
                    table.add_row("Stretch Marks", f"{breast.inflation.profile.stretch_marks:.1%}")
            
            # Fluids
            total_fluid = breast.mixture.total()
            if total_fluid > 0:
                try:
                    contents = breast.mixture.composition()
                    comp_parts = []
                    for ft, vol in contents.items():
                        name = ft.name if hasattr(ft, 'name') else str(ft)
                        # Проверяем что объемы совпадают
                        if vol > 0:
                            comp_parts.append(f"{name}:{vol:.1f}ml")
                    
                    if comp_parts:
                        comp = ", ".join(comp_parts)
                        # Добавляем общий объем для проверки
                        comp += f" [dim](total: {total_fluid:.1f}ml)[/dim]"
                    else:
                        comp = f"{total_fluid:.1f}ml"
                        
                except Exception as e:
                    comp = f"{total_fluid:.1f}ml"
                
                table.add_row("Contents", comp)
            ctx.console.print(table)
    
    def cmd_breasts_add(ctx: CommandContext, amount: str, fluid_type: str = "milk", side: str = "left"):
        """Добавить жидкость в грудь: breasts.add <amount> [type] [side]"""
        breast = get_breast(ctx, side)
        if not breast:
            return
        
        ftype = FluidType.MILK
        try:
            ftype = FluidType[fluid_type.upper()]
        except KeyError:
            ctx.console.print(f"[yellow]Unknown fluid type {fluid_type}, using MILK[/yellow]")
        
        actual = breast.add_fluid_by_type(ftype, float(amount))
        
        if actual > 0:
            ctx.console.print(f"[green]Added {actual:.1f}ml {ftype.name} to {side} breast[/green]")
            if breast.inflation.profile.stretch_ratio > 1.1:
                ctx.console.print(f"[dim]Stretch: {breast.inflation.profile.stretch_ratio:.2f}x[/dim]")
        else:
            ctx.console.print(f"[red]Could not add fluid (full or error)[/red]")
    
    def cmd_breasts_express(ctx: CommandContext, amount: str = "50", side: str = "left"):
        """Выдаить молоко: breasts.express [amount] [side]"""
        breast = get_breast(ctx, side)
        if not breast:
            return
        
        removed = breast.express(float(amount))
        
        if removed > 0:
            ctx.console.print(f"[green]Expressed {removed:.1f}ml from {side} breast[/green]")
            # Стимуляция лактации
            try:
                if breast.lactation.is_active:
                    ctx.console.print(f"[dim]Lactation stimulated[/dim]")
            except:
                pass
        else:
            ctx.console.print(f"[yellow]Nothing to express[/yellow]")
    
    def cmd_breasts_lactation(ctx: CommandContext, action: str = "start", side: str = "left"):
        """Управление лактацией: breasts.lactation <start/stop> [side]"""
        if side.lower() in ("both", "b"):
            left = ctx.body.breasts.left if ctx.body.breasts else None
            right = ctx.body.breasts.right if ctx.body.breasts else None
            
            if action.lower() == "start":
                if left: left.start_lactation()
                if right: right.start_lactation()
                ctx.console.print("[green]Lactation started for both breasts[/green]")
            elif action.lower() == "stop":
                if left: left.stop_lactation()
                if right: right.stop_lactation()
                ctx.console.print("[yellow]Lactation stopped for both breasts[/yellow]")
        else:
            breast = get_breast(ctx, side)
            if not breast:
                return
            
            if action.lower() == "start":
                breast.start_lactation()
                ctx.console.print(f"[green]Lactation started for {side} breast[/green]")
            elif action.lower() == "stop":
                breast.stop_lactation()
                ctx.console.print(f"[yellow]Lactation stopped for {side} breast[/yellow]")
            else:
                ctx.console.print(f"[red]Unknown action: {action} (use start/stop)[/red]")
    
    def cmd_breasts_stimulate(ctx: CommandContext, intensity: str = "1.0", side: str = "left"):
        """Стимулировать грудь: breasts.stimulate [intensity] [side]"""
        if side.lower() in ("both", "b"):
            left = ctx.body.breasts.left if ctx.body.breasts else None
            right = ctx.body.breasts.right if ctx.body.breasts else None
            
            l_pleasure = left.stimulate(float(intensity)) if left else {}
            r_pleasure = right.stimulate(float(intensity)) if right else {}
            
            ctx.console.print(f"[green]Stimulated both breasts (intensity: {intensity})[/green]")
            total = (l_pleasure.get('pleasure', 0) if isinstance(l_pleasure, dict) else 0) + \
                   (r_pleasure.get('pleasure', 0) if isinstance(r_pleasure, dict) else 0)
            if total > 0:
                ctx.console.print(f"[dim]Pleasure gain: {total:.2f}[/dim]")
        else:
            breast = get_breast(ctx, side)
            if not breast:
                return
            
            result = breast.stimulate(float(intensity))
            ctx.console.print(f"[green]Stimulated {side} breast[/green]")
            if isinstance(result, dict) and result.get('pleasure', 0) > 0:
                ctx.console.print(f"[dim]Pleasure: +{result['pleasure']:.2f}[/dim]")
    
    def cmd_breasts_tick(ctx: CommandContext, dt: str = "1.0", side: str = "left"):
        """Обновить грудь (тик): breasts.tick [dt] [side]"""
        if side.lower() in ("both", "b"):
            left = ctx.body.breasts.left if ctx.body.breasts else None
            right = ctx.body.breasts.right if ctx.body.breasts else None
            
            if left:
                result = left.tick(float(dt), ctx.body.event_bus)
                ctx.console.print(f"[dim]Left: state={result.get('state')}, filled={result.get('filled', 0):.1f}ml[/dim]")
            if right:
                result = right.tick(float(dt), ctx.body.event_bus)
                ctx.console.print(f"[dim]Right: state={result.get('state')}, filled={result.get('filled', 0):.1f}ml[/dim]")
        else:
            breast = get_breast(ctx, side)
            if not breast:
                return
            
            result = breast.tick(float(dt), ctx.body.event_bus)
            
            # ИСПРАВЛЕНО: безопасная работа с результатом (там уже строки)
            panel = Panel(
                f"State: {result.get('state', 'N/A')}\n"
                f"Cup: {result.get('cup', 'N/A')}\n"
                f"Filled: {result.get('filled', 0):.1f}ml\n"
                f"Pressure: {result.get('pressure', 0):.2f}\n"
                f"Leaked: {result.get('leaked', 0):.2f}ml",
                title=f"Tick Result ({side})",
                border_style="blue"
            )
            ctx.console.print(panel)
    
    def cmd_breasts_insert(ctx: CommandContext, object_name: str, volume: str, side: str = "left"):
        """Вставить объект в грудь: breasts.insert <name> <volume> [side]"""
        breast = get_breast(ctx, side)
        if not breast:
            return
        
        # ИСПРАВЛЕНО: передаем dict вместо объекта
        obj_data = {
            'name': object_name,
            'volume': float(volume),
            'length': 5.0,
            'diameter': 1.0,
            'insertion_type': 'foreign'
        }
        
        if breast.insert_object(obj_data):
            ctx.console.print(f"[green]Inserted {object_name} ({volume}ml) into {side} breast[/green]")
            # Давление обновляется автоматически в tick
        else:
            ctx.console.print(f"[red]Cannot insert (too large or blocked)[/red]")
    
    def cmd_breasts_remove_object(ctx: CommandContext, object_name: str, side: str = "left"):
        """Удалить объект из груди: breasts.remove_object <name> [side]"""
        breast = get_breast(ctx, side)
        if not breast:
            return
        
        obj = breast.remove_object(object_name)
        if obj:
            ctx.console.print(f"[green]Removed {obj.get('name', object_name)} from {side} breast[/green]")
        else:
            ctx.console.print(f"[yellow]Object {object_name} not found[/yellow]")
    
    def cmd_breasts_nipple(ctx: CommandContext, action: str = "open", amount: str = "0.5", side: str = "left"):
        """Управление соском: breasts.nipple <open/close> [amount] [side]"""
        breast = get_breast(ctx, side)
        if not breast:
            return
        
        nipple = breast.areola.nipples[0] if breast.areola.nipples else None
        if not nipple:
            ctx.console.print("[red]No nipple found[/red]")
            return
        
        if action.lower() == "open":
            nipple.open(float(amount))
            ctx.console.print(f"[green]Nipple opened to {nipple.gape_diameter:.2f}cm[/green]")
        elif action.lower() == "close":
            nipple.close()
            ctx.console.print("[yellow]Nipple closed[/yellow]")
        elif action.lower() == "stretch":
            nipple.gape_diameter = float(amount)
            nipple.is_open = nipple.gape_diameter > 0.01
            ctx.console.print(f"[green]Nipple stretched to {amount}cm[/green]")

    def cmd_breasts_fullness(ctx: CommandContext, side: str = "left"):
        """Показать заполненность груди: breasts.fullness [left/right/both]"""
        if side.lower() in ("both", "b"):
            left = ctx.body.breasts.left if ctx.body.breasts else None
            right = ctx.body.breasts.right if ctx.body.breasts else None
            
            if not left or not right:
                ctx.console.print("[red]Грудь не инициализирована[/red]")
                return
            
            table = Table(title="Заполненность груди")
            table.add_column("Сторона", style="cyan")
            table.add_column("Текущий объем", style="green")
            table.add_column("Максимум", style="yellow")
            table.add_column("Процент", style="magenta")
            table.add_column("Бар", style="white")
            
            for breast, name in [(left, "Left"), (right, "Right")]:
                filled = breast.filled
                max_vol = breast._max_volume
                ratio = breast.fill_ratio
                percent = ratio * 100
                
                # Визуальный бар (20 символов)
                filled_len = int(ratio * 20)
                bar = "█" * filled_len + "░" * (20 - filled_len)
                
                color = "green" if ratio < 0.5 else "yellow" if ratio < 0.8 else "red"
                table.add_row(
                    name,
                    f"{filled:.1f} ml",
                    f"{max_vol:.1f} ml",
                    f"[{color}]{percent:.1f}%[/{color}]",
                    f"[{color}]{bar}[/{color}]"
                )
            
            ctx.console.print(table)
            
            # Дополнительная информация о состоянии
            if left.state.name == "LEAKING" or right.state.name == "LEAKING":
                ctx.console.print("[yellow]⚠ Одна или обе груди протекают![/yellow]")
            if left.state.name == "OVERPRESSURED" or right.state.name == "OVERPRESSURED":
                ctx.console.print("[red]⚠ Критическое давление![/red]")
        else:
            breast = get_breast(ctx, side)
            if not breast:
                return
            
            filled = breast.filled
            max_vol = breast._max_volume
            ratio = breast.fill_ratio
            percent = ratio * 100
            
            # Детальный вывод для одной груди
            panel = Panel(
                f"[bold]Объем:[/bold] {filled:.1f} / {max_vol:.1f} ml\n"
                f"[bold]Заполнение:[/bold] {percent:.1f}%\n"
                f"[bold]Состояние:[/bold] {breast.state.name if hasattr(breast.state, 'name') else str(breast.state)}\n"
                f"[bold]Давление:[/bold] {breast.pressure:.2f}\n"
                f"[bold]Растяжение:[/bold] {breast.inflation.profile.stretch_ratio:.2f}x\n"
                f"\n[{'green' if ratio < 0.5 else 'yellow' if ratio < 0.8 else 'red'}]"
                f"{'█' * int(ratio * 30)}{'░' * (30 - int(ratio * 30))}[/]"
                f" {percent:.0f}%",
                title=f"Заполненность ({side.title()}) - {breast.current_cup.name}",
                border_style="blue" if ratio < 0.8 else "red"
            )
            ctx.console.print(panel)
    
    # Регистрация команд
    registry.register("breasts.show", cmd_breasts_show, "Show breast status [left/right/both]", 
                     aliases=["bs"], category="Грудь")
    registry.register("breasts.add", cmd_breasts_add, "Add fluid: <amount> [type] [side]", 
                     aliases=["ba"], category="Грудь")
    registry.register("breasts.express", cmd_breasts_express, "Express milk [amount] [side]", 
                     aliases=["be"], category="Грудь")
    registry.register("breasts.lactation", cmd_breasts_lactation, "Lactation control: <start/stop> [side]", 
                     aliases=["bl"], category="Грудь")
    registry.register("breasts.stimulate", cmd_breasts_stimulate, "Stimulate [intensity] [side]", 
                     aliases=["bst"], category="Грудь")
    registry.register("breasts.tick", cmd_breasts_tick, "Update breast [dt] [side]", 
                     aliases=["bt"], category="Грудь")
    registry.register("breasts.insert", cmd_breasts_insert, "Insert object: <name> <volume> [side]", 
                     aliases=["bi"], category="Грудь")
    registry.register("breasts.remove_object", cmd_breasts_remove_object, "Remove object: <name> [side]", 
                     aliases=["bro"], category="Грудь")
    registry.register("breasts.nipple", cmd_breasts_nipple, "Nipple control: <open/close> [amount] [side]", 
                     aliases=["bn"], category="Грудь")
    registry.register("breasts.fullness", cmd_breasts_fullness, 
                     "Показать заполненность груди [left/right/both]", 
                     aliases=["bf", "bfullness"], category="Грудь")

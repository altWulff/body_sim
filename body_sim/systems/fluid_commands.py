# body_sim/systems/fluid_commands.py
from typing import Dict, List, Callable
from rich.table import Table

from body_sim.systems.commands import CommandRegistry, CommandContext
from body_sim.core.fluids import Fluid, FluidType
from body_sim.anatomy.base import AnatomicalComponent

def find_component_by_path(body, path: str) -> AnatomicalComponent:
    """Найти компонент по пути: reproductive.uteri.0 или digestive.stomach"""
    path = path.replace('reproductive.', 'reproductive_system.')
    path = path.replace('digestive.', 'digestive_system.')
    
    parts = path.split('.')
    current = body
    
    for i, part in enumerate(parts):
        if part.isdigit():
            idx = int(part)
            if isinstance(current, (list, tuple)) and 0 <= idx < len(current):
                current = current[idx]
            else:
                return None
        elif hasattr(current, part):
            current = getattr(current, part)
        elif hasattr(current, f"{part}s"):
            collection = getattr(current, f"{part}s")
            if isinstance(collection, list):
                if i + 1 < len(parts) and parts[i + 1].isdigit():
                    current = collection
                else:
                    current = collection[0] if collection else None
            else:
                current = collection
        else:
            if isinstance(current, list):
                for item in current:
                    if hasattr(item, 'name') and getattr(item, 'name') == part:
                        current = item
                        break
                else:
                    return None
            else:
                return None
                
        if current is None:
            return None
            
    return current if isinstance(current, AnatomicalComponent) else None

def get_fluid_type(type_name: str) -> FluidType:
    """Преобразовать строку в FluidType."""
    try:
        return FluidType[type_name.upper()]
    except KeyError:
        return FluidType.CUSTOM

def register_fluid_commands(registry: CommandRegistry):
    
    def cmd_fluid_add(ctx: CommandContext, path: str, fluid_type: str, amount: str, source: str = "command"):
        """Добавить жидкость в компонент"""
        component = find_component_by_path(ctx.body, path)
        if not component:
            ctx.console.print(f"[red]Component not found: {path}[/red]")
            return
            
        fluid = Fluid(
            fluid_type=get_fluid_type(fluid_type),
            volume=float(amount),
            source_component=source
        )
        
        overflow = component.add_fluid(fluid)
        actual_added = float(amount) - overflow
        
        if overflow > 0:
            ctx.console.print(f"[yellow]Added {actual_added:.1f}ml (overflow: {overflow:.1f}ml)[/yellow]")
        else:
            ctx.console.print(f"[green]Added {actual_added:.1f}ml {fluid_type}[/green]")
            
    def cmd_fluid_remove(ctx: CommandContext, path: str, amount: str, fluid_type: str = None):
        """Удалить жидкость"""
        component = find_component_by_path(ctx.body, path)
        if not component:
            ctx.console.print(f"[red]Component not found: {path}[/red]")
            return
            
        ftype = get_fluid_type(fluid_type) if fluid_type else None
        removed = component.remove_fluid(float(amount), ftype)
        
        total_removed = sum(f.volume for f in removed)
        ctx.console.print(f"[green]Removed {total_removed:.1f}ml[/green]")
        
    def cmd_fluid_clear(ctx: CommandContext, path: str):
        """Полностью очистить компонент"""
        component = find_component_by_path(ctx.body, path)
        if not component:
            ctx.console.print(f"[red]Component not found: {path}[/red]")
            return
            
        total = sum(f.volume for f in component.fluids)
        component.fluids.clear()
        ctx.console.print(f"[yellow]Cleared {total:.1f}ml[/yellow]")
        
    def cmd_fluid_show(ctx: CommandContext, path: str):
        """Показать содержимое"""
        component = find_component_by_path(ctx.body, path)
        if not component:
            ctx.console.print(f"[red]Component not found: {path}[/red]")
            return
            
        if not component.fluids:
            ctx.console.print("[dim]Empty[/dim]")
            return
            
        table = Table(title=f"Fluids in {path}")
        table.add_column("Type", style="cyan")
        table.add_column("Volume", style="green")
        table.add_column("Source", style="dim")
        
        for fluid in component.fluids:
            table.add_row(
                fluid.fluid_type.value,
                f"{fluid.volume:.1f}ml",
                fluid.source_component
            )
            
        table.add_row("", "", "")
        table.add_row("TOTAL", f"{sum(f.volume for f in component.fluids):.1f}ml", 
                     f"{component.get_fullness()*100:.0f}% full")
        ctx.console.print(table)
        
    def cmd_fluid_transfer(ctx: CommandContext, from_path: str, to_path: str, amount: str, fluid_type: str = None):
        """Перенести жидкость"""
        source = find_component_by_path(ctx.body, from_path)
        target = find_component_by_path(ctx.body, to_path)
        
        if not source or not target:
            ctx.console.print(f"[red]Component not found[/red]")
            return
            
        ftype = get_fluid_type(fluid_type) if fluid_type else None
        
        source.transfer_to(target, float(amount), ftype, ctx.body.event_bus)
        
        ctx.console.print(f"[green]Transferred {amount}ml from {from_path} to {to_path}[/green]")
        
    def cmd_fluid_list_types(ctx: CommandContext):
        """Список доступных типов жидкостей"""
        table = Table(title="Fluid Types")
        table.add_column("Name", style="cyan")
        table.add_column("Value", style="green")
        for ft in FluidType:
            table.add_row(ft.name, ft.value)
        ctx.console.print(table)
        
    def cmd_fluid_fill(ctx: CommandContext, path: str, fluid_type: str):
        """Заполнить компонент до максимума"""
        component = find_component_by_path(ctx.body, path)
        if not component:
            ctx.console.print(f"[red]Component not found: {path}[/red]")
            return
            
        available = component.max_capacity - sum(f.volume for f in component.fluids)
        if available <= 0:
            ctx.console.print("[yellow]Already full[/yellow]")
            return
            
        fluid = Fluid(
            fluid_type=get_fluid_type(fluid_type),
            volume=available,
            source_component="fill_command"
        )
        
        component.add_fluid(fluid)
        ctx.console.print(f"[green]Filled with {available:.1f}ml {fluid_type}[/green]")
        
    def cmd_fluid_mix(ctx: CommandContext, path: str):
        """Смешать все жидкости в компоненте"""
        component = find_component_by_path(ctx.body, path)
        if not component or len(component.fluids) < 2:
            ctx.console.print("[red]Nothing to mix[/red]")
            return
            
        base = component.fluids[0]
        for fluid in component.fluids[1:]:
            base = base.merge(fluid)
            
        component.fluids = [base]
        ctx.console.print(f"[green]Mixed into {base.fluid_type.value}, "
                         f"total: {base.volume:.1f}ml[/green]")

    # Удобные алиасы для частых операций
    def cmd_fill_uterus(ctx: CommandContext, amount: str = "100", fluid_type: str = "water"):
        """Заполнить матку"""
        if not ctx.body.reproductive_system or not ctx.body.reproductive_system.uteri:
            ctx.console.print("[red]No uterus[/red]")
            return
        uterus = ctx.body.reproductive_system.uteri[0]
        fluid = Fluid(
            fluid_type=get_fluid_type(fluid_type),
            volume=float(amount),
            source_component="fill_command"
        )
        overflow = uterus.add_fluid(fluid)
        actual = float(amount) - overflow
        ctx.console.print(f"[green]Uterus filled: {actual:.1f}ml {fluid_type}[/green]")
        
    def cmd_fill_stomach(ctx: CommandContext, amount: str = "500", fluid_type: str = "water"):
        """Заполнить желудок"""
        if not ctx.body.digestive_system:
            ctx.console.print("[red]No digestive system[/red]")
            return
        stomach = ctx.body.digestive_system.stomach
        fluid = Fluid(
            fluid_type=get_fluid_type(fluid_type),
            volume=float(amount),
            source_component="fill_command"
        )
        stomach.add_fluid(fluid)
        ctx.console.print(f"[green]Stomach filled: {amount}ml {fluid_type}[/green]")

    # Регистрация с категориями и алиасами
    registry.register("fluid.add", cmd_fluid_add, "Add fluid: <path> <type> <ml>", 
                     aliases=["fa"], category="Жидкости")
    registry.register("fluid.remove", cmd_fluid_remove, "Remove fluid: <path> <ml> [type]", 
                     aliases=["fr"], category="Жидкости")
    registry.register("fluid.clear", cmd_fluid_clear, "Clear all fluids: <path>", 
                     aliases=["fc"], category="Жидкости")
    registry.register("fluid.show", cmd_fluid_show, "Show fluids: <path>", 
                     aliases=["fs"], category="Жидкости")
    registry.register("fluid.transfer", cmd_fluid_transfer, "Transfer: <from> <to> <ml> [type]", 
                     aliases=["ft"], category="Жидкости")
    registry.register("fluid.types", cmd_fluid_list_types, "List fluid types", 
                     aliases=["flt"], category="Жидкости")
    registry.register("fluid.fill", cmd_fluid_fill, "Fill to max: <path> <type>", 
                     aliases=["ff"], category="Жидкости")
    registry.register("fluid.mix", cmd_fluid_mix, "Mix all fluids: <path>", 
                     aliases=["fm"], category="Жидкости")
    
    # Быстрые команды заполнения
    registry.register("fill.uterus", cmd_fill_uterus, "Quick fill uterus [amount] [type]", 
                     aliases=["fu"], category="Жидкости")
    registry.register("fill.stomach", cmd_fill_stomach, "Quick fill stomach [amount] [type]", 
                     aliases=["fst"], category="Жидкости")

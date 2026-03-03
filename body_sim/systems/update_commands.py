# body_sim/systems/update_commands.py
from typing import Dict, Any

from body_sim.systems.commands import CommandRegistry, CommandContext
from body_sim.systems.fluid_commands import find_component_by_path

def register_update_commands(registry: CommandRegistry):
    
    def cmd_update(ctx: CommandContext, arg1: str = None, arg2: str = None):
        """Обновить компонент: update [path] [dt] или update [dt]"""
        path = None
        dt = 1.0
        
        if arg1 is not None:
            try:
                float(arg1)
                dt = float(arg1)
                path = None
            except ValueError:
                path = arg1
                if arg2 is not None:
                    dt = float(arg2)
        
        if path is None:
            ctx.body.update(dt)
            ctx.console.print(f"[green]Body updated: +{dt}s[/green]")
            return
            
        component = find_component_by_path(ctx.body, path)
        if not component:
            ctx.console.print(f"[red]Component not found: {path}[/red]")
            return
            
        if hasattr(component, 'update'):
            component.update(dt, ctx.body.event_bus)
            ctx.console.print(f"[green]Updated {path}: +{dt}s[/green]")
        else:
            ctx.console.print(f"[red]Component has no update method[/red]")
            
    def cmd_update_reproductive(ctx: CommandContext, dt: str = "1.0"):
        """Обновить репродуктивную систему"""
        if ctx.body.reproductive_system:
            ctx.body.reproductive_system.update(float(dt), ctx.body.event_bus)
            ctx.console.print(f"[green]Reproductive system updated: +{dt}s[/green]")
        else:
            ctx.console.print("[red]No reproductive system[/red]")
            
    def cmd_update_digestive(ctx: CommandContext, dt: str = "1.0"):
        """Обновить пищеварительную систему"""
        if ctx.body.digestive_system:
            ctx.body.digestive_system.update(float(dt), ctx.body.event_bus)
            ctx.console.print(f"[green]Digestive system updated: +{dt}s[/green]")
        else:
            ctx.console.print("[red]No digestive system[/red]")
            
    def cmd_tick(ctx: CommandContext, count: str = "1"):
        """Быстрый тик (0.1s * count)"""
        n = int(count)
        for _ in range(n):
            ctx.body.update(0.1)
        ctx.console.print(f"[green]Advanced {n} ticks ({n*0.1}s)[/green]")

    # Регистрация с категориями
    registry.register("update", cmd_update, "Update component: [path] [dt]", 
                     aliases=["u"], category="Время")
    registry.register("update.reproductive", cmd_update_reproductive, "Update reproductive [dt]", 
                     aliases=["ur"], category="Время")
    registry.register("update.digestive", cmd_update_digestive, "Update digestive [dt]", 
                     aliases=["ud"], category="Время")
    registry.register("tick", cmd_tick, "Quick tick [count]", 
                     aliases=["t"], category="Время")

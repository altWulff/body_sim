# body_sim/commands/update.py
from typing import Dict, Any

from body_sim.commands.base import CommandRegistry, CommandContext
from body_sim.commands.fluids import find_component_by_path

def register_update_commands(registry: CommandRegistry):
    
    def cmd_update(ctx: CommandContext, arg1: str = None, arg2: str = None):
        """Обновить компонент: update [path] [dt] или update [dt]"""
        path = None
        dt = 1.0
        
        # Разбор аргументов
        if arg1 is not None:
            # Проверяем, является ли arg1 числом (dt) или путем
            try:
                float(arg1)  # Пробуем как число
                # Это dt, путь не указан
                dt = float(arg1)
                path = None
            except ValueError:
                # Это путь, не число
                path = arg1
                if arg2 is not None:
                    dt = float(arg2)
        
        if path is None:
            # Обновить всё тело
            ctx.body.update(dt)
            ctx.console.print(f"[green]Body updated: +{dt}s[/green]")
            return
            
        # Обновить конкретный компонент
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
        """Обновить репродуктивную систему: update.reproductive [dt]"""
        if ctx.body.reproductive_system:
            ctx.body.reproductive_system.update(float(dt), ctx.body.event_bus)
            ctx.console.print(f"[green]Reproductive system updated: +{dt}s[/green]")
        else:
            ctx.console.print("[red]No reproductive system[/red]")
            
    def cmd_update_digestive(ctx: CommandContext, dt: str = "1.0"):
        """Обновить пищеварительную систему: update.digestive [dt]"""
        if ctx.body.digestive_system:
            ctx.body.digestive_system.update(float(dt), ctx.body.event_bus)
            ctx.console.print(f"[green]Digestive system updated: +{dt}s[/green]")
        else:
            ctx.console.print("[red]No digestive system[/red]")
            
    def cmd_tick(ctx: CommandContext, count: str = "1"):
        """Быстрый тик (0.1s * count): tick [count]"""
        n = int(count)
        for _ in range(n):
            ctx.body.update(0.1)
        ctx.console.print(f"[green]Advanced {n} ticks ({n*0.1}s)[/green]")

    # Регистрация с категориями и алиасами
    registry.register("update", cmd_update, "Update body or component: update [path] [dt]", 
                     aliases=["u"], category="Обновление")
    registry.register("update.reproductive", cmd_update_reproductive, "Update reproductive system [dt]", 
                     aliases=["ur"], category="Обновление")
    registry.register("update.digestive", cmd_update_digestive, "Update digestive system [dt]", 
                     aliases=["ud"], category="Обновление")
    registry.register("tick", cmd_tick, "Quick tick (0.1s * count): tick [count]", 
                     aliases=["t"], category="Обновление")

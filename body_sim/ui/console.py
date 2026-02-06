# body_sim/ui/console.py
"""
Интерактивная консоль для управления симуляцией.
"""

import sys
from typing import List, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.prompt import Prompt
from rich.text import Text

from body_sim.ui.commands import CommandContext, create_registry

console = Console()


def run_console(bodies: List):
    """Запустить интерактивную консоль."""
    registry = create_registry()
    ctx = CommandContext(bodies=bodies, registry=registry)  # Передаём registry здесь

    console.print(Panel.fit(
        "[bold cyan]Breast & Body Simulation Console[/bold cyan]\n"
        "Type [yellow]help[/yellow] for commands, [yellow]quit[/yellow] to exit",
        border_style="cyan"
    ))

    if bodies:
        console.print(f"[green]Loaded {len(bodies)} bodies[/green]")
        from body_sim.ui.rich_render import render_body_list
        console.print(render_body_list(bodies, ctx.active_body_idx))

    while ctx.running:
        try:
            # Показываем приглашение
            body_name = ctx.active_body.name if ctx.active_body else "none"
            prompt_text = f"[cyan]{body_name}[/cyan] > "

            # Используем input для совместимости
            console.print(prompt_text, end="")
            line = input().strip()

            if not line:
                continue

            # Выполняем команду
            handled = registry.execute(line, ctx)

            if not handled:
                console.print(f"[red]Unknown command: {line.split()[0]}[/red]")
                console.print("Type [yellow]help[/yellow] for available commands")

        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'quit' to exit[/yellow]")
        except EOFError:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")

    console.print("[dim]Console closed[/dim]")


def run_live_console(bodies: List, refresh_rate: float = 1.0):
    """Запустить консоль с live-обновлением экрана."""
    registry = create_registry()
    ctx = CommandContext(bodies=bodies, registry=registry)  # Передаём registry здесь

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="input", size=1)
    )

    def update_layout():
        from body_sim.ui.rich_render import render_body_list, render_full_body
        
        header = Text("Breast & Body Simulation", justify="center", style="bold cyan")
        layout["header"].update(Panel(header, border_style="cyan"))

        if ctx.active_body:
            layout["main"].update(render_full_body(ctx.active_body))
        else:
            layout["main"].update(Panel("No body selected", border_style="red"))

        body_name = ctx.active_body.name if ctx.active_body else "none"
        layout["input"].update(Text(f"{body_name} > ", style="cyan"))

    console.print("[yellow]Live mode - press Ctrl+C to enter command mode[/yellow]")

    try:
        with Live(layout, console=console, refresh_per_second=1/refresh_rate) as live:
            import time
            import select

            while ctx.running:
                update_layout()

                # Проверяем ввод (non-blocking)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = input().strip()
                    if line:
                        registry.execute(line, ctx)

                time.sleep(refresh_rate)
    except KeyboardInterrupt:
        pass

    # Переходим в обычный режим
    run_console(bodies)
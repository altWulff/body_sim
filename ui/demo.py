# body_sim/ui/demo.py
"""
Демонстрационный режим с автоматической симуляцией.
"""

import time
import random
from typing import List

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn

from body_sim.core.enums import FluidType, LactationState
from body_sim.ui.rich_render import (
    render_body_list, render_full_body, 
    render_breasts, render_genitals, render_stats
)

console = Console()


def run_demo(bodies: List, duration: int = 60, auto_tick: bool = True):
    """
    Запустить демонстрацию симуляции.

    Args:
        bodies: Список тел для демонстрации
        duration: Длительность в секундах
        auto_tick: Автоматически обновлять симуляцию
    """
    console.print(Panel.fit(
        "[bold magenta]🎪 Breast & Body Simulation Demo[/bold magenta]\n"
        f"Running with {len(bodies)} bodies for {duration}s\n"
        "Press [yellow]Ctrl+C[/yellow] to stop",
        border_style="magenta"
    ))

    start_time = time.time()
    tick_count = 0

    try:
        with Live(console=console, refresh_per_second=4) as live:
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                remaining = duration - elapsed

                # Создаём layout
                layout = Layout()

                # Header
                header_text = f"Demo Mode | Tick: {tick_count} | Time: {elapsed:.1f}s / {duration}s"
                layout.split_column(
                    Layout(name="header", size=3),
                    Layout(name="content")
                )
                layout["header"].update(Panel(
                    header_text, 
                    border_style="magenta",
                    title="[bold]Simulation Status[/bold]"
                ))

                # Content - показываем первое тело детально + список всех
                layout["content"].split_row(
                    Layout(name="list", ratio=1),
                    Layout(name="detail", ratio=2)
                )

                layout["list"].update(render_body_list(bodies, 0))

                if bodies:
                    active_body = bodies[0]

                    # Случайные действия каждые 5 тиков
                    if tick_count % 5 == 0 and auto_tick:
                        _random_action(active_body)

                    # Обновляем симуляцию
                    if auto_tick:
                        for body in bodies:
                            body.tick(0.25)

                    layout["detail"].update(render_full_body(active_body))

                live.update(layout)

                tick_count += 1
                time.sleep(0.25)

    except KeyboardInterrupt:
        console.print("\n[yellow]Demo stopped by user[/yellow]")

    console.print(f"[green]Demo completed: {tick_count} ticks[/green]")

    # Финальная статистика
    _show_final_stats(bodies)


def _random_action(body):
    """Выполнить случайное действие с телом."""
    actions = []

    if body.has_breasts:
        actions.extend(['add_milk', 'stimulate_breasts', 'toggle_lactation'])

    if body.has_penis:
        actions.extend(['stimulate_penis', 'ejaculate'])

    if body.has_vagina:
        actions.extend(['stimulate_vagina'])

    if not actions:
        return

    action = random.choice(actions)

    try:
        if action == 'add_milk' and body.has_breasts:
            grid = body.breast_grid
            row = random.randint(0, len(grid.rows) - 1)
            col = random.randint(0, len(grid.rows[row]) - 1)
            breast = grid.get(row, col)
            amount = random.uniform(10, 50)
            breast.add_fluid(FluidType.MILK, amount)

        elif action == 'stimulate_breasts':
            body.stimulate("breasts", intensity=random.uniform(0.1, 0.3))

        elif action == 'toggle_lactation' and body.has_breasts:
            grid = body.breast_grid
            row = random.randint(0, len(grid.rows) - 1)
            col = random.randint(0, len(grid.rows[row]) - 1)
            breast = grid.get(row, col)
            if breast.lactation.state == LactationState.OFF:
                breast.lactation.start()
            else:
                breast.lactation.stimulate()

        elif action == 'stimulate_penis':
            if body.penises:
                idx = random.randint(0, len(body.penises) - 1)
                body.stimulate("penis", idx, random.uniform(0.2, 0.5))

        elif action == 'ejaculate' and body.has_penis:
            if body.penises and body.penises[0].is_erect:
                body.ejaculate(0, random.uniform(0.5, 1.0))

        elif action == 'stimulate_vagina':
            if body.vaginas:
                idx = random.randint(0, len(body.vaginas) - 1)
                body.stimulate("vagina", idx, random.uniform(0.2, 0.4))

    except Exception as e:
        pass  # Игнорируем ошибки в демо-режиме


def _show_final_stats(bodies):
    """Показать финальную статистику."""
    table = Table(title="Final Statistics", box="round")
    table.add_column("Body", style="bold")
    table.add_column("Sex", width=8)
    table.add_column("Arousal")
    table.add_column("Pleasure")
    table.add_column("Breast Fill")
    table.add_column("Genitals")

    for body in bodies:
        sex_emoji = {"MALE": "♂️", "FEMALE": "♀️", "FUTANARI": "⚧"}.get(body.sex.name, "?")

        arousal = f"{body.stats.arousal:.0%}"
        pleasure = f"{body.stats.pleasure:.2f}"

        breast_fill = "—"
        if body.has_breasts:
            total = body.breast_grid.stats().get('total_filled', 0)
            breast_fill = f"{total:.0f}ml"

        genitals = []
        if body.has_penis:
            genitals.append(f"🍆×{len(body.penises)}")
        if body.has_vagina:
            genitals.append(f"🌸×{len(body.vaginas)}")

        table.add_row(
            body.name,
            sex_emoji,
            arousal,
            pleasure,
            breast_fill,
            " ".join(genitals) if genitals else "—"
        )

    console.print(table)


def run_interactive_demo():
    """Интерактивная демонстрация с меню."""
    from body_sim.body.factory import BodyFactory
    from body_sim.core.enums import BodyType, TesticleSize

    console.print(Panel.fit(
        "[bold]Interactive Demo Setup[/bold]\n"
        "Create your bodies:",
        border_style="cyan"
    ))

    bodies = []

    # Предустановленные демо-тела
    presets = [
        ("Maria", "female", {"breast_cup": "E", "body_type": BodyType.CURVY}),
        ("Alex", "male", {"penis_size": 18.0, "body_type": BodyType.MUSCULAR}),
        ("Rin", "futa", {"penis_size": 20.0, "breast_cup": "G", "has_scrotum": True}),
    ]

    for name, sex_type, kwargs in presets:
        try:
            body = BodyFactory.quick_create(sex_type, name)
            for key, value in kwargs.items():
                if hasattr(body, key):
                    setattr(body, key, value)
            bodies.append(body)
            console.print(f"[green]✓ Created {name} ({sex_type})[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to create {name}: {e}[/red]")

    if not bodies:
        console.print("[red]No bodies created![/red]")
        return

    # Запускаем демо
    run_demo(bodies, duration=30)

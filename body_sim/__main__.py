# body_sim/__main__.py (улучшенная версия)
from body_sim.commands import (
    CommandRegistry,
    CommandContext,
    register_all_commands,
    register_fluid_commands,
    register_update_commands,
    register_breast_commands,
)

from body_sim.body.body import Body, Sex
from body_sim.appearance.core import Race
from rich.console import Console
import inspect


def main():
    console = Console()

    # Создание тела
    body = Body(name="Test", sex=Sex.FEMALE, race=Race.SUCCUBUS)

    # Регистрация команд
    registry = CommandRegistry()
    register_all_commands(registry)
    register_fluid_commands(registry)
    register_update_commands(registry)
    register_breast_commands(registry)

    # Добавляем команду help
    def cmd_help(ctx: CommandContext):
        """Показать справку по командам"""
        help_content = registry.get_help()
        ctx.console.print(help_content)

    registry.register(
        "help", cmd_help, "Показать справку", aliases=["h", "?"], category="Системная"
    )

    # Добавляем команду exit с алиасами
    def cmd_exit(ctx: CommandContext):
        """Выйти из программы"""
        pass

    registry.register(
        "exit",
        cmd_exit,
        "Выйти из программы",
        aliases=["quit", "q"],
        category="Системная",
    )

    console.print(
        f"[bold green]BodySim initialized: {body.name} ({body.race.value})[/]"
    )
    console.print("[dim]Type 'help' for commands, 'exit' to quit[/]\n")

    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            parts = user_input.split()
            cmd = parts[0]
            args = parts[1:]

            # Проверяем, является ли команда командой выхода (с учётом алиасов)
            resolved_cmd = registry.get(cmd)
            if resolved_cmd == cmd_exit:
                break

            # Создаем контекст
            ctx = CommandContext(body=body, console=console, args=args)

            # Проверяем существование команды
            command = registry.get(cmd)
            if command is None:
                console.print(f"[red]Unknown command: {cmd}[/]")
                continue

            # Проверяем сигнатуру функции
            sig = inspect.signature(command)
            params = list(sig.parameters.values())

            # Проверяем обязательные аргументы (кроме ctx)
            required_count = 0
            for param in params[1:]:  # Пропускаем ctx
                if param.default == inspect.Parameter.empty:
                    required_count += 1

            if len(args) < required_count:
                ctx.console.print(
                    f"[yellow]Usage: {registry._help_text.get(cmd, cmd)}[/yellow]"
                )
                continue

            # Вызываем команду с аргументами
            result = command(ctx, *args)

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")

    console.print("[bold cyan]Goodbye![/]")


if __name__ == "__main__":
    main()

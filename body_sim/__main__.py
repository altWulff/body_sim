# === __main__.py ===
from rich.console import Console
from rich.prompt import Prompt

from body_sim.body.body import Body, Sex
from body_sim.appearance.core import Race
from body_sim.systems.commands import CommandContext, CommandRegistry
from body_sim.systems.impl import register_all_commands

def main():
    console = Console()
    console.print("[blue]BodySim 2.0 - Modular[/blue]")
    
    body = Body(name="Test", sex=Sex.FEMALE, race=Race.SUCCUBUS)
    
    if body.reproductive_system and body.reproductive_system.clitorises:
        body.reproductive_system.clitorises[0].can_transform = True
    
    ctx = CommandContext(body, console)
    registry = CommandRegistry()
    register_all_commands(registry)
    
    console.print(f"Created: {body.name} ({body.sex.name}, {body.race.value})")
    
    while True:
        try:
            cmd = Prompt.ask(f"[{body.name}]")
            if cmd in ["exit", "quit"]:
                break
            if cmd == "help":
                console.print(registry.get_help())
            else:
                registry.execute(ctx, cmd)
                body.update(0.1)
        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    main()
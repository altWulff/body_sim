# main.py

from rich.console import Console
from rich.prompt import Prompt


from body_sim.appearance.core import Race
from body_sim.core.body import Body
from body_sim.systems.commands import CommandRegistry, CommandContext
from body_sim.systems.impl import register_all_commands
from body_sim.appearance.core import AppearanceConfig, AppearanceComponent
from body_sim.anatomy.reproductive.system import ReproductiveSystem
from body_sim.anatomy.breasts import Breasts
from body_sim.anatomy.digestive import DigestiveSystem



def create_character(name: str, race: Race, gender: str = "female") -> Body:
    body = Body(name, gender)
    
    # Appearance
    config = AppearanceConfig(
        race=race,
        height_cm=160,
        weight_kg=55,
        skin_tone="fair",
        eye_color="blue",
        eye_shape="almond",
        ear_type="human",
        ear_length=1.0
    )
    
    if race == Race.DRAGON:
        config.height_cm = 120
        config.eye_shape = "reptilian"
        config.special_traits = ["horns", "tail"]
    elif race == Race.WOLF:
        config.ear_type = "furry"
        config.ear_length = 2.0
        config.special_traits = ["tail", "fur"]
    elif race == Race.ELF:
        config.ear_type = "pointed"
        config.ear_length = 1.8
        config.eye_color = "purple"
        
    body.appearance = AppearanceComponent(config)
    body.add_system("appearance", body.appearance)
    
    # Reproductive
    repro = ReproductiveSystem()
    repro.breasts = Breasts()
    
    if race == Race.WOLF:
        repro.breasts.add_row(2.0)  # Вторая пара для волка
        
    body.reproductive = repro
    body.add_system("reproductive", repro)
    
    # Digestive
    digestive = DigestiveSystem()
    body.digestive = digestive
    body.add_system("digestive", digestive)
    
    return body

def main():
    console = Console()
    
    # Setup
    registry = CommandRegistry()
    register_all_commands(registry)
    
    # Character creation
    console.print("[blue]BodySim 2.0 - Architecture Demo[/blue]")
    name = Prompt.ask("Name", default="Test")
    race_choice = Prompt.ask("Race", choices=["human", "elf", "wolf", "dragon"], default="human")
    
    body = create_character(name, Race[race_choice.upper()])
    ctx = CommandContext(body, console)
    
    console.print(f"\n[green]Created {race_choice} character: {name}[/green]")
    console.print("Type 'help' for commands, 'exit' to quit\n")
    
    # Main loop
    while True:
        try:
            cmd = Prompt.ask(f"[{body.name}]")
            if cmd in ["exit", "quit"]:
                break
            if cmd == "help":
                console.print(registry.get_help())
            else:
                registry.execute(ctx, cmd)
                body.update(0.1)  # Advance time
        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    main()

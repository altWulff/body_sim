# body_sim/commands/__init__.py
from body_sim.commands.base import CommandRegistry, CommandContext
from body_sim.commands.core import register_all_commands
from body_sim.commands.fluids import register_fluid_commands, find_component_by_path
from body_sim.commands.breasts import register_breast_commands
from body_sim.commands.update import register_update_commands

__all__ = [
    'CommandRegistry',
    'CommandContext', 
    'register_all_commands',
    'register_fluid_commands',
    'register_breast_commands',
    'register_update_commands',
    'find_component_by_path',
]

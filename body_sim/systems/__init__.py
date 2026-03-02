# === systems/__init__.py ===
from body_sim.systems.commands import CommandRegistry, CommandContext
from body_sim.systems.impl import register_all_commands

__all__ = ['CommandRegistry', 'CommandContext', 'register_all_commands']

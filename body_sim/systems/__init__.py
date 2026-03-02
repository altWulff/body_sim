# === systems/__init__.py ===
from body_sim.systems.commands import CommandRegistry, CommandContext, register_commands

__all__ = ['CommandRegistry', 'CommandContext', 'register_commands']

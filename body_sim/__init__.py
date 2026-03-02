# === __init__.py (корневой) ===
"""BodySim 2.0 - Modular Architecture"""
__version__ = "2.0.0"

from body_sim.core.events import EventBus, Event, EventType
from body_sim.core.fluids import Fluid, FluidType, FluidContainer
from body_sim.core.components import BaseComponent, ComponentInterface

from body_sim.appearance.core import Race, AppearanceComponent, AppearanceConfig
from body_sim.body.body import Body, Sex

__all__ = [
    'EventBus', 'Event', 'EventType',
    'Fluid', 'FluidType', 'FluidContainer',
    'BaseComponent', 'ComponentInterface',
    'Race', 'AppearanceComponent', 'AppearanceConfig',
    'Body', 'Sex'
]

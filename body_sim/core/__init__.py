# === core/__init__.py ===
from body_sim.core.events import EventBus, Event, EventType
from body_sim.core.fluids import Fluid, FluidType, FluidContainer
from body_sim.core.components import BaseComponent, ComponentInterface

__all__ = [
    "EventBus",
    "Event",
    "EventType",
    "Fluid",
    "FluidType",
    "FluidContainer",
    "BaseComponent",
    "ComponentInterface",
]

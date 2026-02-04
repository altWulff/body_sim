# body_sim/systems/__init__.py
"""
Подсистемы - физика, лактация, события, сетка.
"""

from body_sim.systems.physics import calc_pressure, calc_sag_target
from body_sim.systems.lactation import LactationSystem
from body_sim.systems.inflation import InflationSystem
from body_sim.systems.insertion import InsertableObject, InsertionManager
from body_sim.systems.grid import BreastGrid
from body_sim.systems.events import (
    EventBus, EventType, Event, 
    EventHandler, ReactionSystem
)
from body_sim.systems.pressure import PressureSystem, get_pressure_tier

__all__ = [
    "calc_pressure", "calc_sag_target",
    "LactationSystem",
    "InflationSystem",
    "InsertableObject", "InsertionManager",
    "BreastGrid",
    "EventBus", "EventType", "Event", "EventHandler", "ReactionSystem",
    "PressureSystem", "get_pressure_tier",
]

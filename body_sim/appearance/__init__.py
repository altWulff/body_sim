# body_sim/appearance/__init__.py
"""
Система внешности для body_sim.
"""

from .enums import *
from .features import (
    Eye, Ear, Hair, Horn, Tail, Wings, FacialStructure, Skin
)
from .body_integration import AppearanceMixin, get_race_preset, get_random_race_size
from .appearance import Appearance

__all__ = [
    # Enums
    "EyeType", "EyeColor", "EarType", "HairType", "HairStyle", "HairColor",
    "HornType", "TailType", "WingType", "SkinTexture", "Race", 
    "FacialFeature", "BodyMarking",
    # Classes
    "Eye", "Ear", "Hair", "Horn", "Tail", "Wings", "FacialStructure", "Skin",
    "Appearance", "AppearanceMixin", "EyeAppearance", "EarAppearance", "RACE_ANATOMY_PRESETS", 
    "get_race_preset", "get_random_race_size",
]
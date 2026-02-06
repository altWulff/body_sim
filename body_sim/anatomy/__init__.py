# body_sim/anatomy/__init__.py
"""
Анатомические структуры - грудь, гениталии, репродуктивная система.
"""

from body_sim.anatomy.base import Genital
from body_sim.anatomy.nipple import Nipple, Areola
from body_sim.anatomy.breast import Breast
from body_sim.anatomy.genitals import (
    Penis, Clitoris, Vagina, Anus,
    Testicle, Scrotum
)
from body_sim.anatomy.uterus import (
    # Enums
    UterusState, CervixState, OvaryState, FallopianTubeState,
    # Classes
    UterineWall, Cervix, Ovary, FallopianTube, Uterus, UterusSystem
)

__all__ = [
    "Genital",
    "Nipple", "Areola",
    "Breast",
    "Penis", "Clitoris", "Vagina", "Anus",
    "Testicle", "Scrotum",
    # Uterus System
    "UterusState", "CervixState", "OvaryState", "FallopianTubeState",
    "UterineWall", "Cervix", "Ovary", "FallopianTube", "Uterus", "UterusSystem",
]

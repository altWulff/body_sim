# body_sim/anatomy/__init__.py
"""
Анатомические структуры - грудь, гениталии, репродуктивная система.
"""

from body_sim.anatomy.base import Genital
from body_sim.anatomy.stomach import StomachSystem
from body_sim.anatomy.mouth import MouthSystem
from body_sim.anatomy.esophagus import Esophagus
from body_sim.anatomy.nipple import Nipple, Areola
from body_sim.anatomy.breast import Breast
from body_sim.anatomy.testicle import Testicle
from body_sim.anatomy.scrotum import Scrotum
from body_sim.anatomy.penis import Penis
from body_sim.anatomy.clitoris import Clitoris
from body_sim.anatomy.vagina import Vagina
from body_sim.anatomy.anus import Anus
from body_sim.anatomy.uterus import (
    # Enums
    UterusState, CervixState, OvaryState, FallopianTubeState,
    # Classes
    UterineWall, Cervix, Ovary, FallopianTube, Uterus, UterusSystem
)

from body_sim.anatomy.factories import create_penis, create_vagina, create_scrotum

__all__ = [
    "Genital",
    "Nipple", "Areola",
    "Breast",
    "Penis", 
    "Clitoris", 
    "Vagina", 
    "Anus",
    "Testicle", 
    "Scrotum",
    "create_penis", 
    "create_vagina", 
    "create_scrotum",
    # Uterus System
    "UterusState", "CervixState", "OvaryState", "FallopianTubeState",
    "UterineWall", "Cervix", "Ovary", "FallopianTube", "Uterus", "UterusSystem",
    "StomachSystem", "MouthSystem", "Esophagus",
]

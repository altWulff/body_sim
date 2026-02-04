# body_sim/body/__init__.py
"""
Тело как целое - статистика, базовый класс, фабрика.
"""

from body_sim.body.stats import BodyStats
from body_sim.body.body import Body, MaleBody, FemaleBody, FutanariBody
from body_sim.body.factory import BodyFactory

__all__ = [
    "BodyStats",
    "Body", "MaleBody", "FemaleBody", "FutanariBody",
    "BodyFactory",
]


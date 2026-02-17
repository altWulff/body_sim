"""
Combat system for body_sim
"""
from .core import Combatant, CombatManager, DamageType, StatusEffect
from .skills import (
    MilkSpraySkill, BreastCrushSkill, UterusSlamSkill,
    ProlapseWhipSkill, EjaculationBlastSkill, OvaryBurstSkill,
    DeepPierceAttack
)

__all__ = [
    'Combatant', 'CombatManager', 'DamageType', 'StatusEffect',
    'MilkSpraySkill', 'BreastCrushSkill', 'UterusSlamSkill',
    'ProlapseWhipSkill', 'EjaculationBlastSkill', 'OvaryBurstSkill',
    'DeepPierceAttack'
]

"""
Magic System for body_sim.
Модуль магии жидкостей - каждый орган с ёмкостью является источником маны.
"""

# Базовые классы
from .fluid_magic import (
    BaseSkill, SkillBook, ManaCost, SkillEffect,
    MagicSchool, SkillTarget, milk_cost, cum_cost
)

# Перки
from .perks.base_perks import (
    BasePerk, PerkType,
    FluidRegenerationPerk, OverfillCapacityPerk,
    PressureMasteryPerk, SensitiveOrgansPerk,
    RapidRefillPerk, OverflowMasteryPerk, DualCastingPerk
)

# Скиллы
from .skills.milk_skills import (
    MilkSkill, MilkSpray, LactationHeal, BreastShield,
    UterinePulse, NippleSnare, ColostrumBoost, MilkFlood,
    VaginalDrain, get_female_skills
)

from .skills.cum_skills import (
    CumSkill, CumShot, VirilityBoost, ProstateStrike,
    SpermClone, TesticularFortitude, EjaculationStorm,
    SemenWeb, VasectomyBlade, ImpregnationIntent,
    get_male_skills
)

from .skills.hybrid_skills import (
    HybridSkill, DualRelease, GenderFusion, WombCannon,
    BreedingFrenzy, HermaphroditeAura, MilkCumTransmutation,
    ProlapseExploit, get_futanari_skills
)

# UI
from .ui.magic_render import MagicRenderer, render_magic_comparison

# Интеграция
from .magic_integration import (
    MagicMixin, register_magic_to_body, MagicalBody
)

__all__ = [
    # База
    'BaseSkill', 'SkillBook', 'ManaCost', 'SkillEffect',
    'MagicSchool', 'SkillTarget', 'milk_cost', 'cum_cost',
    
    # Перки
    'BasePerk', 'PerkType',
    'FluidRegenerationPerk', 'OverfillCapacityPerk',
    'PressureMasteryPerk', 'SensitiveOrgansPerk',
    'RapidRefillPerk', 'OverflowMasteryPerk', 'DualCastingPerk',
    
    # Скиллы
    'MilkSpray', 'LactationHeal', 'BreastShield',
    'UterinePulse', 'NippleSnare', 'ColostrumBoost',
    'MilkFlood', 'VaginalDrain', 'get_female_skills',
    
    'CumShot', 'VirilityBoost', 'ProstateStrike',
    'SpermClone', 'TesticularFortitude', 'EjaculationStorm',
    'SemenWeb', 'VasectomyBlade', 'ImpregnationIntent',
    'get_male_skills',
    
    'DualRelease', 'GenderFusion', 'WombCannon',
    'BreedingFrenzy', 'HermaphroditeAura', 'MilkCumTransmutation',
    'ProlapseExploit', 'get_futanari_skills',
    
    # UI
    'MagicRenderer', 'render_magic_comparison',
    
    # Интеграция
    'MagicMixin', 'register_magic_to_body', 'MagicalBody'
]



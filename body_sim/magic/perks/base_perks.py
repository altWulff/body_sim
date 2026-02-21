"""
Базовая система перков (пассивных умений).
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from fluid_magic import BaseSkill
    from body_system import Body

class PerkType(Enum):
    ANATOMICAL = "anatomical"  # Зависит от строения тела
    FLUID = "fluid"              # Зависит от жидкостей
    COMBAT = "combat"            # Боевые перки
    MAGIC = "magic"              # Магические перки

class BasePerk(ABC):
    """Базовый класс перка"""
    
    def __init__(
        self,
        name: str,
        description: str,
        perk_type: PerkType,
        max_rank: int = 1
    ):
        self.name = name
        self.description = description
        self.perk_type = perk_type
        self.max_rank = max_rank
        self.current_rank = 1
        self.body: Optional['Body'] = None
    
    def apply_to(self, body: 'Body'):
        """Применение перка к телу"""
        self.body = body
        self.on_apply()
    
    @abstractmethod
    def on_apply(self):
        """Вызывается при получении перка"""
        pass
    
    def on_skill_use(self, skill: 'BaseSkill', result: Dict):
        """Вызывается при использовании скилла"""
        pass
    
    def on_organ_fill(self, organ_name: str, amount: float, fluid_type):
        """Вызывается при заполнении органа"""
        pass
    
    def tick(self):
        """Обновление каждый ход"""
        pass
    
    def upgrade(self) -> bool:
        """Улучшение перка"""
        if self.current_rank < self.max_rank:
            self.current_rank += 1
            return True
        return False


class FluidRegenerationPerk(BasePerk):
    """Регенерация жидкостей"""
    
    def __init__(self, organ_name: str, fluid_type, amount_per_tick: float):
        super().__init__(
            name=f"{organ_name.title()} Regeneration",
            description=f"Пассивно восстанавливает {fluid_type.name} в {organ_name}.",
            perk_type=PerkType.FLUID,
            max_rank=5
        )
        self.organ_name = organ_name
        self.fluid_type = fluid_type
        self.amount_per_tick = amount_per_tick
    
    def tick(self):
        if not self.body:
            return
        if hasattr(self.body, self.organ_name):
            organ = getattr(self.body, self.organ_name)
            if hasattr(organ, 'add_fluid'):
                organ.add_fluid(self.amount_per_tick * self.current_rank, self.fluid_type)


class OverfillCapacityPerk(BasePerk):
    """Увеличение максимальной ёмкости органа"""
    
    def __init__(self, organ_name: str, bonus_percent: float = 0.2):
        super().__init__(
            name=f"Expanded {organ_name}",
            description=f"Увеличивает максимальный объём {organ_name} на {int(bonus_percent*100)}%.",
            perk_type=PerkType.ANATOMICAL,
            max_rank=3
        )
        self.organ_name = organ_name
        self.bonus_percent = bonus_percent
        self.applied = False
    
    def on_apply(self):
        if self.applied:
            return
        if hasattr(self.body, self.organ_name):
            organ = getattr(self.body, self.organ_name)
            if hasattr(organ, 'max_volume'):
                bonus = organ.max_volume * self.bonus_percent * self.current_rank
                organ.max_volume += bonus
                self.applied = True


class PressureMasteryPerk(BasePerk):
    """Мастерство давления - скиллы требуют меньше жидкости"""
    
    def __init__(self):
        super().__init__(
            name="Pressure Mastery",
            description="Снижает стоимость скиллов на 20% за ранг.",
            perk_type=PerkType.MAGIC,
            max_rank=3
        )
    
    def on_skill_use(self, skill, result):
        if result.get("success") and hasattr(skill, 'costs'):
            # Возвращаем часть ресурса
            for cost in skill.costs:
                refund = cost.amount * (0.2 * self.current_rank)
                organ = cost._get_organ(self.body)
                if organ:
                    organ.add_fluid(refund, cost.fluid_type)


class SensitiveOrgansPerk(BasePerk):
    """Чувствительные органы - больше магической силы при наполнении"""
    
    def __init__(self, organ_name: str):
        super().__init__(
            name=f"Sensitive {organ_name}",
            description=f"Увеличивает силу магии когда {organ_name} заполнен более чем на 50%.",
            perk_type=PerkType.ANATOMICAL,
            max_rank=3
        )
        self.organ_name = organ_name
        self.active = False
    
    def tick(self):
        if not self.body:
            return
        if hasattr(self.body, self.organ_name):
            organ = getattr(self.body, self.organ_name)
            if hasattr(organ, 'current_volume') and hasattr(organ, 'max_volume'):
                fullness = organ.current_volume / organ.max_volume
                self.active = fullness > 0.5


class RapidRefillPerk(BasePerk):
    """Быстрое наполнение - увеличивает скорость производства жидкости"""
    
    def __init__(self, organ_name: str):
        super().__init__(
            name=f"Rapid {organ_name} Production",
            description=f"Увеличивает скорость производства жидкости в {organ_name}.",
            perk_type=PerkType.FLUID,
            max_rank=5
        )
        self.organ_name = organ_name
    
    def on_apply(self):
        if hasattr(self.body, self.organ_name):
            organ = getattr(self.body, self.organ_name)
            if hasattr(organ, 'production_rate'):
                organ.production_rate *= (1 + 0.3 * self.current_rank)


class OverflowMasteryPerk(BasePerk):
    """Мастерство переполнения - переполненные органы дают бонусы"""
    
    def __init__(self):
        super().__init__(
            name="Overflow Mastery",
            description="Переполненные органы не вызывают штрафов, а дают бонусы к силе.",
            perk_type=PerkType.MAGIC,
            max_rank=1
        )
    
    def on_organ_fill(self, organ_name: str, amount: float, fluid_type):
        if not self.body:
            return
        if hasattr(self.body, organ_name):
            organ = getattr(self.body, organ_name)
            if hasattr(organ, 'current_volume') and hasattr(organ, 'max_volume'):
                if organ.current_volume > organ.max_volume:
                    # Вместо штрафа - бонус
                    if hasattr(self.body, 'magic_power'):
                        self.body.magic_power += 10


class DualCastingPerk(BasePerk):
    """Двойное чтение - шанс использовать скилл дважды"""
    
    def __init__(self):
        super().__init__(
            name="Dual Casting",
            description="20% шанс использовать скилл второй раз бесплатно.",
            perk_type=PerkType.MAGIC,
            max_rank=1
        )
    
    def on_skill_use(self, skill, result):
        import random
        if result.get("success") and random.random() < 0.2:
            # Дублируем эффект
            result["duplicated"] = True
            result["message"] += " (Двойное применение!)"



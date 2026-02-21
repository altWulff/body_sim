
"""
Базовая система магии жидкостей для body_sim.
Каждый орган с ёмкостью является источником маны.
"""
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from abc import ABC, abstractmethod
import random

if TYPE_CHECKING:
    from body_system import Body
    from fluid_system import FluidType

class MagicSchool(Enum):
    """Школы магии"""
    MILK = auto()      # Молочная магия (лечение, защита, контроль)
    CUM = auto()       # Спермная магия (урон, усиление, создание)
    HYBRID = auto()    # Гибридная (для футанари, комбинированные эффекты)
    BLOOD = auto()     # Кровавая (если добавишь кровь)
    HOLY = auto()      # Святая (очищение от состояний)

class SkillTarget(Enum):
    """Цели скиллов"""
    SELF = auto()
    ENEMY = auto()
    ALLY = auto()
    AREA = auto()      # Область
    ORGAN = auto()     # Конкретный орган цели

@dataclass
class ManaCost:
    """Стоимость маны в виде жидкостей"""
    fluid_type: 'FluidType'
    source_organ: str  # Название органа или тип (breasts, uterus, testicles)
    amount: float      # мл
    min_required: float = 0.0  # Минимум для использования
    
    def can_pay(self, body: 'Body') -> bool:
        """Проверка возможности оплаты"""
        organ = self._get_organ(body)
        if not organ:
            return False
        return organ.current_volume >= self.min_required
    
    def pay(self, body: 'Body') -> bool:
        """Списание ресурса"""
        organ = self._get_organ(body)
        if not organ or organ.current_volume < self.amount:
            return False
        organ.remove_fluid(self.amount)
        return True
    
    def _get_organ(self, body: 'Body'):
        """Получение органа по названию"""
        if hasattr(body, self.source_organ):
            return getattr(body, self.source_organ)
        return None

@dataclass  
class SkillEffect:
    """Эффект скилла"""
    type: str  # damage, heal, buff, debuff, fill, drain, transform
    value: float
    duration: int = 0  # 0 = мгновенно
    target_organ: Optional[str] = None
    condition: Optional[Callable] = None

class BaseSkill(ABC):
    """Базовый класс скилла"""
    
    def __init__(
        self,
        name: str,
        description: str,
        school: MagicSchool,
        costs: List[ManaCost],
        effects: List[SkillEffect],
        target: SkillTarget = SkillTarget.ENEMY,
        cooldown: int = 0,
        requires_form: Optional[str] = None  # male/female/futanari
    ):
        self.name = name
        self.description = description
        self.school = school
        self.costs = costs
        self.effects = effects
        self.target = target
        self.cooldown = cooldown
        self.requires_form = requires_form
        self.current_cooldown = 0
    
    def can_use(self, caster: 'Body', target: Optional['Body'] = None) -> tuple[bool, str]:
        """Проверка возможности использования"""
        if self.current_cooldown > 0:
            return False, f"Перезарядка: {self.current_cooldown} ходов"
        
        if self.requires_form and caster.body_form.value != self.requires_form:
            return False, f"Требуется форма: {self.requires_form}"
        
        for cost in self.costs:
            if not cost.can_pay(caster):
                organ = cost._get_organ(caster)
                current = organ.current_volume if organ else 0
                return False, f"Недостаточно {cost.fluid_type.name} в {cost.source_organ} ({current:.1f}/{cost.amount:.1f}ml)"
        
        return True, "OK"
    
    def use(self, caster: 'Body', target: Optional['Body'] = None, target_organ: Optional[str] = None) -> Dict[str, Any]:
        """Использование скилла"""
        can_use, msg = self.can_use(caster, target)
        if not can_use:
            return {"success": False, "message": msg}
        
        # Оплата ресурсов
        for cost in self.costs:
            if not cost.pay(caster):
                return {"success": False, "message": f"Ошибка списания ресурса: {cost.source_organ}"}
        
        # Применение эффектов
        results = []
        for effect in self.effects:
            result = self._apply_effect(effect, caster, target, target_organ)
            results.append(result)
        
        self.current_cooldown = self.cooldown
        
        return {
            "success": True,
            "skill": self.name,
            "results": results,
            "message": f"{caster.name} использует {self.name}"
        }
    
    def _apply_effect(self, effect: SkillEffect, caster: 'Body', target: Optional['Body'], target_organ: Optional[str]):
        """Применение конкретного эффекта"""
        if effect.type == "damage":
            return self._apply_damage(effect, caster, target)
        elif effect.type == "heal":
            return self._apply_heal(effect, caster, target)
        elif effect.type == "fill":
            return self._apply_fill(effect, caster, target)
        elif effect.type == "drain":
            return self._apply_drain(effect, caster, target)
        elif effect.type == "buff":
            return self._apply_buff(effect, caster, target)
        return {"type": "unknown", "success": False}
    
    def _apply_damage(self, effect: SkillEffect, caster: 'Body', target: 'Body'):
        """Нанесение урона (стресс/боль органу)"""
        if not target:
            return {"type": "damage", "success": False, "error": "Нет цели"}
        
        # Урон = заполненность органов цели (чем полнее, тем больнее)
        multiplier = 1.0
        if target_organ := effect.target_organ:
            if hasattr(target, target_organ):
                organ = getattr(target, target_organ)
                multiplier = 1 + (organ.current_volume / organ.max_volume)
        
        damage = effect.value * multiplier
        target.stress += damage
        return {
            "type": "damage",
            "value": damage,
            "target": target.name,
            "organ": target_organ
        }
    
    def _apply_fill(self, effect: SkillEffect, caster: 'Body', target: 'Body'):
        """Заполнение органа жидкостью"""
        if not target and effect.target_organ:
            target = caster
        
        if organ_name := effect.target_organ:
            if hasattr(target, organ_name):
                organ = getattr(target, organ_name)
                organ.add_fluid(effect.value, caster.get_dominant_fluid())
                return {
                    "type": "fill",
                    "organ": organ_name,
                    "amount": effect.value,
                    "target": target.name
                }
        return {"type": "fill", "success": False}
    
    @abstractmethod
    def get_power_scaling(self, caster: 'Body') -> float:
        """Масштабирование силы от статов"""
        pass
    
    def tick_cooldown(self):
        """Уменьшение кулдауна"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


class SkillBook:
    """Книга скиллов персонажа"""
    
    def __init__(self, body: 'Body'):
        self.body = body
        self.skills: Dict[str, BaseSkill] = {}
        self.passive_perks: List['BasePerk'] = []
        self.skill_history: List[str] = []
    
    def add_skill(self, skill: BaseSkill):
        """Добавление скилла"""
        self.skills[skill.name] = skill
    
    def remove_skill(self, skill_name: str):
        """Удаление скилла"""
        if skill_name in self.skills:
            del self.skills[skill_name]
    
    def use_skill(self, skill_name: str, target: Optional['Body'] = None, **kwargs) -> Dict:
        """Использование скилла по имени"""
        if skill_name not in self.skills:
            return {"success": False, "message": f"Скилл '{skill_name}' не известен"}
        
        skill = self.skills[skill_name]
        result = skill.use(self.body, target, **kwargs)
        
        if result["success"]:
            self.skill_history.append(skill_name)
            # Применение перков
            for perk in self.passive_perks:
                perk.on_skill_use(skill, result)
        
        return result
    
    def get_available_skills(self) -> List[BaseSkill]:
        """Получение доступных для использования скиллов"""
        available = []
        for skill in self.skills.values():
            can_use, _ = skill.can_use(self.body)
            if can_use:
                available.append(skill)
        return available
    
    def tick(self):
        """Обновление на ход"""
        for skill in self.skills.values():
            skill.tick_cooldown()
        for perk in self.passive_perks:
            perk.tick()


# Помощники для создания стоимости
def milk_cost(organ: str, amount: float, min_required: float = 0.0):
    """Стоимость в молоке"""
    from fluid_system import FluidType
    return ManaCost(FluidType.MILK, organ, amount, min_required)

def cum_cost(organ: str, amount: float, min_required: float = 0.0):
    """Стоимость в сперме"""
    from fluid_system import FluidType
    return ManaCost(FluidType.CUM, organ, amount, min_required)


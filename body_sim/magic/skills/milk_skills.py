"""
Молочная магия - защита, лечение, контроль.
Источник: грудь (breasts), матка (uterus) - если заполнена молоком.
"""
from typing import List, Dict, Any
from body_sim.magic.fluid_magic import BaseSkill, SkillEffect, SkillTarget, MagicSchool, milk_cost, SkillBook

class MilkSkill(BaseSkill):
    """Базовый класс молочных скиллов"""
    
    def get_power_scaling(self, body) -> float:
        """Сила зависит от заполненности груди и размера"""
        power = 1.0
        if hasattr(body, 'breasts'):
            breast = body.breasts
            # Чем полнее грудь, тем сильнее
            fullness = breast.current_volume / breast.max_volume
            power += fullness * 0.5
            # Больший размер = больше молока = сильнее магия
            if hasattr(breast, 'cup_size'):
                cup_bonus = {"AA": 0, "A": 0.1, "B": 0.2, "C": 0.3, "D": 0.4, "DD": 0.5, 
                           "E": 0.6, "F": 0.7, "G": 0.8, "H": 1.0, "I": 1.2, "J": 1.5,
                           "K": 2.0, "L": 2.5, "M": 3.0}
                power += cup_bonus.get(breast.cup_size.value, 0)
        return power


class MilkSpray(MilkSkill):
    """
    Молочный заряд - базовая атака.
    Выстреливает струёй молока под давлением.
    """
    def __init__(self):
        super().__init__(
            name="Milk Spray",
            description="Выстреливает молоком под высоким давлением, нанося урон.",
            school=MagicSchool.MILK,
            costs=[milk_cost("breasts", 50, 20)],
            effects=[SkillEffect("damage", 25, target_organ=None)],
            target=SkillTarget.ENEMY,
            cooldown=0
        )
    
    def use(self, caster, target=None, target_organ=None):
        # Бонусный урон если грудь переполнена
        if hasattr(caster, 'breasts'):
            breast = caster.breasts
            if breast.current_volume > breast.max_volume * 0.9:
                self.effects[0].value = 40  # Критический урон
            else:
                self.effects[0].value = 25
        return super().use(caster, target, target_organ)


class LactationHeal(MilkSkill):
    """
    Исцеляющая лактация - лечение союзника.
    Передаёт молоко с целебными свойствами.
    """
    def __init__(self):
        super().__init__(
            name="Healing Lactation",
            description="Исцеляет цель, передавая питательное молоко.",
            school=MagicSchool.MILK,
            costs=[milk_cost("breasts", 100, 50)],
            effects=[SkillEffect("heal", 50)],
            target=SkillTarget.ALLY,
            cooldown=2
        )
    
    def _apply_heal(self, effect, caster, target):
        if not target:
            return {"type": "heal", "success": False}
        
        heal_amount = effect.value * self.get_power_scaling(caster)
        target.heal(heal_amount)
        
        # Также снимаем стресс
        stress_relief = heal_amount * 0.3
        target.stress -= stress_relief
        
        return {
            "type": "heal",
            "amount": heal_amount,
            "stress_relief": stress_relief,
            "target": target.name
        }


class BreastShield(MilkSkill):
    """
    Молочный щит - защита.
    Создаёт барьер из конденсированного молока.
    """
    def __init__(self):
        super().__init__(
            name="Breast Shield",
            description="Создаёт защитный барьер из молочной мембраны.",
            school=MagicSchool.MILK,
            costs=[milk_cost("breasts", 80, 30)],
            effects=[SkillEffect("buff", 30, duration=3)],
            target=SkillTarget.SELF,
            cooldown=4
        )


class UterinePulse(MilkSkill):
    """
    Пульс матки - массовый контроль.
    Требует матку, заполненную молоком.
    Вызывает волну давления, оглушающую врагов.
    """
    def __init__(self):
        super().__init__(
            name="Womb Pulse",
            description="Массовая атака через резкое сокращение матки.",
            school=MagicSchool.MILK,
            costs=[
                milk_cost("uterus", 150, 50),
                milk_cost("breasts", 50, 0)
            ],
            effects=[SkillEffect("damage", 40), SkillEffect("debuff", 0, duration=2)],
            target=SkillTarget.AREA,
            cooldown=5
        )
    
    def can_use(self, caster, target=None):
        # Проверка что матка существует и в ней есть молоко
        if not hasattr(caster, 'uterus'):
            return False, "Требуется матка"
        return super().can_use(caster, target)


class NippleSnare(MilkSkill):
    """
    Ловушка сосков - контроль.
    Закрепляет врага молочными нитями.
    """
    def __init__(self):
        super().__init__(
            name="Nipple Snare",
            description="Связывает противника молочными нитями, ограничивая движение.",
            school=MagicSchool.MILK,
            costs=[milk_cost("breasts", 40, 20)],
            effects=[SkillEffect("debuff", 0, duration=3)],
            target=SkillTarget.ENEMY,
            cooldown=3
        )


class ColostrumBoost(MilkSkill):
    """
    Колостровый импульс - усиление.
    Временно усиливает качество молока.
    """
    def __init__(self):
        super().__init__(
            name="Colostrum Surge",
            description="Усиливает питательность молока, повышая эффективность следующих скиллов.",
            school=MagicSchool.MILK,
            costs=[milk_cost("breasts", 60, 20)],
            effects=[SkillEffect("buff", 1.5, duration=3)],
            target=SkillTarget.SELF,
            cooldown=5
        )


class MilkFlood(MilkSkill):
    """
    Молочный потоп - ультимативное заклинание.
    Требует полной груди и высокого давления.
    """
    def __init__(self):
        super().__init__(
            name="Milk Flood",
            description="Выпускает всё молоко мощным потоком, нанося огромный урон.",
            school=MagicSchool.MILK,
            costs=[milk_cost("breasts", 500, 300)],
            effects=[SkillEffect("damage", 150), SkillEffect("fill", 0)],
            target=SkillTarget.ENEMY,
            cooldown=8
        )
    
    def can_use(self, caster, target=None):
        if hasattr(caster, 'breasts'):
            breast = caster.breasts
            if breast.current_volume < breast.max_volume * 0.8:
                return False, f"Требуется минимум 80% заполненности груди ({breast.current_volume:.0f}/{breast.max_volume*0.8:.0f}ml)"
        return super().can_use(caster, target)


# Скиллы для вагинальной магии (если в вагине есть молоко/сперма)
class VaginalDrain(MilkSkill):
    """
   ысасывание через вагину - крадёт жидкость у врага.
    """
    def __init__(self):
        super().__init__(
            name="Vaginal Siphon",
            description="Высасывает жидкость из органа врага в свою вагину.",
            school=MagicSchool.MILK,
            costs=[milk_cost("vagina", 20, 0)],  # Нужно немного для инициации
            effects=[SkillEffect("drain", 100)],
            target=SkillTarget.ENEMY,
            cooldown=3
        )
    
    def _apply_drain(self, effect, caster, target):
        """Кража жидкости"""
        if not target or not hasattr(target, 'breasts'):
            return {"type": "drain", "success": False}
        
        # Крадём из груди цели
        target_breast = target.breasts
        stolen = min(effect.value, target_breast.current_volume)
        fluid = target_breast.get_fluid_type()
        
        target_breast.remove_fluid(stolen)
        
        # Перемещаем в свою вагину
        if hasattr(caster, 'vagina'):
            caster.vagina.add_fluid(stolen, fluid)
        
        return {
            "type": "drain",
            "amount": stolen,
            "fluid": fluid.name if fluid else "unknown",
            "from": target.name,
            "to": caster.name
        }


def get_female_skills() -> List[BaseSkill]:
    """Возвращает стартовые скиллы для женского персонажа"""
    return [
        MilkSpray(),
        LactationHeal(),
        BreastShield(),
        NippleSnare(),
        ColostrumBoost()
    ]



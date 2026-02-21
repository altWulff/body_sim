"""
Гибридная магия для футанари - комбинирует молочную и спермную магию.
Источники: грудь, матка, пенис, яичники.
"""
from typing import List
from body_sim.magic.fluid_magic import BaseSkill, SkillEffect, SkillTarget, MagicSchool, milk_cost, cum_cost

class HybridSkill(BaseSkill):
    """Базовый класс гибридных скиллов"""
    
    def get_power_scaling(self, body) -> float:
        """Сила зависит от обоих ресурсов"""
        power = 1.5  # Базовый бонус за разнообразие
        
        # Молочная составляющая
        if hasattr(body, 'breasts'):
            breast = body.breasts
            power += (breast.current_volume / breast.max_volume) * 0.5
        
        # Спермная составляющая
        if hasattr(body, 'penises') and body.penises:
            penis = body.penises[0]
            if hasattr(penis, 'fluid_container'):
                fc = penis.fluid_container
                power += (fc.current_volume / fc.max_volume) * 0.5
        
        # Синергия - если оба ресурса высокие
        milk_full = body.breasts.current_volume / body.breasts.max_volume if hasattr(body, 'breasts') else 0
        cum_full = body.penises[0].fluid_container.current_volume / body.penises[0].fluid_container.max_volume if (hasattr(body, 'penises') and body.penises) else 0
        
        if milk_full > 0.7 and cum_full > 0.7:
            power *= 1.5  # Синергия +50%
        
        return power


class DualRelease(HybridSkill):
    """
Двойной выстрел - атака обоими ресурсами одновременно.
    """
    def __init__(self):
        super().__init__(
            name="Dual Release",
            description="Одновременно выстреливает молоком из груди и спермой из члена.",
            school=MagicSchool.HYBRID,
            costs=[
                milk_cost("breasts", 80, 30),
                cum_cost("penis", 80, 30)
            ],
            effects=[SkillEffect("damage", 60)],
            target=SkillTarget.ENEMY,
            cooldown=2,
            requires_form="futanari"
        )


class GenderFusion(HybridSkill):
    """
    Слияние полов - трансформация.
    Временно усиливает все параметры.
    """
    def __init__(self):
        super().__init__(
            name="Gender Fusion",
            description="Объединяет энергии обоих полов для временного усиления всех характеристик.",
            school=MagicSchool.HYBRID,
            costs=[
                milk_cost("uterus", 100, 50),
                cum_cost("scrotum", 100, 50)
            ],
            effects=[
                SkillEffect("buff", 2.0, duration=5),
                SkillEffect("heal", 100)
            ],
            target=SkillTarget.SELF,
            cooldown=8,
            requires_form="futanari"
        )


class WombCannon(HybridSkill):
    """
    Маточная пушка - мощная атака через матку.
    Использует давление в матке + сперму.
    """
    def __init__(self):
        super().__init__(
            name="Womb Cannon",
            description="Накапливает сперму в матке и выпускает мощнейший заряд.",
            school=MagicSchool.HYBRID,
            costs=[
                cum_cost("penis", 200, 100),
                milk_cost("uterus", 50, 0)  # Инициатор
            ],
            effects=[SkillEffect("damage", 150), SkillEffect("fill", 200, target_organ="uterus")],
            target=SkillTarget.ENEMY,
            cooldown=6,
            requires_form="futanari"
        )
    
    def use(self, caster, target=None, target_organ=None):
        # Сначала наполняем матку спермой (трансформация ресурса)
        if hasattr(caster, 'uterus') and hasattr(caster, 'penises'):
            penis = caster.penises[0]
            if penis.fluid_container.current_volume >= 200:
                # Перемещаем сперму из пениса в матку
                fluid = penis.fluid_container.get_fluid_type()
                penis.fluid_container.remove_fluid(200)
                caster.uterus.add_fluid(200, fluid)
        
        return super().use(caster, target, target_organ)


class BreedingFrenzy(HybridSkill):
    """
    Буяние размножения - усиление атаки и скорости.
    """
    def __init__(self):
        super().__init__(
            name="Breeding Frenzy",
            description="Впадает в состояние неконтролируемого возбуждения, повышая скорость атаки.",
            school=MagicSchool.HYBRID,
            costs=[
                milk_cost("breasts", 60, 20),
                cum_cost("scrotum", 60, 20)
            ],
            effects=[SkillEffect("buff", 3.0, duration=3)],
            target=SkillTarget.SELF,
            cooldown=7,
            requires_form="futanari"
        )


class HermaphroditeAura(HybridSkill):
    """
    Аура гермафродита - пассивное влияние на врагов.
    Сбивает с толку, ослабляя сопротивление.
    """
    def __init__(self):
        super().__init__(
            name="Hermaphrodite Aura",
            description="Излучает ауру, снижающую защиту врагов против магии жидкостей.",
            school=MagicSchool.HYBRID,
            costs=[
                milk_cost("breasts", 40, 10),
                cum_cost("penis", 40, 10)
            ],
            effects=[SkillEffect("debuff", 0.5, duration=5)],
            target=SkillTarget.AREA,
            cooldown=6,
            requires_form="futanari"
        )


class MilkCumTransmutation(HybridSkill):
    """
    Трансмутация молока в сперму и наоборот.
    Конвертация ресурсов.
    """
    def __init__(self):
        super().__init__(
            name="Fluid Transmutation",
            description="Превращает молоко в сперму или наоборот с эффективностью 80%.",
            school=MagicSchool.HYBRID,
            costs=[],  # Бесплатно, но требует ресурсов для конвертации
            effects=[SkillEffect("transform", 0.8)],
            target=SkillTarget.SELF,
            cooldown=2,
            requires_form="futanari"
        )
    
    def use(self, caster, target=None, target_organ=None):
        # Конвертация из груди в пенис
        if hasattr(caster, 'breasts') and hasattr(caster, 'penises'):
            breast = caster.breasts
            penis = caster.penises[0]
            
            # Если грудь полнее чем член - конвертируем в сперму
            if breast.current_volume / breast.max_volume > penis.fluid_container.current_volume / penis.fluid_container.max_volume:
                amount = min(100, breast.current_volume)
                breast.remove_fluid(amount)
                from fluid_system import FluidType
                penis.fluid_container.add_fluid(amount * 0.8, FluidType.CUM)
                return {"success": True, "message": f"Превращено {amount}ml молока в сперму"}
            else:
                # Иначе конвертируем в молоко
                amount = min(100, penis.fluid_container.current_volume)
                penis.fluid_container.remove_fluid(amount)
                from fluid_system import FluidType
                breast.add_fluid(amount * 0.8, FluidType.MILK)
                return {"success": True, "message": f"Превращено {amount}ml спермы в молоко"}
        
        return {"success": False, "message": "Недостаточно органов для трансмутации"}


class ProlapseExploit(HybridSkill):
    """
    Эксплуатация пролапса - опасная атака.
    Использует состояние выпадения органов для максимального урона.
    """
    def __init__(self):
        super().__init__(
            name="Prolapse Exploit",
            description="Использует выпавшие органы для максимального высвобождения жидкостей.",
            school=MagicSchool.HYBRID,
            costs=[
                milk_cost("uterus", 300, 100),
                cum_cost("penis", 300, 100)
            ],
            effects=[SkillEffect("damage", 300)],
            target=SkillTarget.ENEMY,
            cooldown=10,
            requires_form="futanari"
        )
    
    def can_use(self, caster, target=None):
        # Можно использовать только при пролапсе матки
        if hasattr(caster, 'uterus'):
            if hasattr(caster.uterus, 'state'):
                if caster.uterus.state.name == "PROLAPSED":
                    return super().can_use(caster, target)
        return False, "Требуется состояние пролапса матки"


def get_futanari_skills() -> List[BaseSkill]:
    """Стартовые скиллы для футанари"""
    return [
        DualRelease(),
        GenderFusion(),
        MilkCumTransmutation(),
        BreedingFrenzy()
    ]



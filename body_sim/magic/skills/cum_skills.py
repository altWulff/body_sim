"""
Спермная магия - атака, усиление, создание.
Источник: яички (testicles), пенис (penis), простата (prostate).
"""
from typing import List
from body_sim.magic.fluid_magic import BaseSkill, SkillEffect, SkillTarget, MagicSchool, cum_cost

class CumSkill(BaseSkill):
    """Базовый класс спермной магии"""
    
    def get_power_scaling(self, body) -> float:
        """Сила зависит от объёма спермы и давления"""
        power = 1.0
        if hasattr(body, 'penises') and body.penises:
            penis = body.penises[0]
            # Больше спермы = сильнее
            if hasattr(penis, 'fluid_container'):
                fc = penis.fluid_container
                fullness = fc.current_volume / fc.max_volume
                power += fullness * 0.8
            # Размер члена влияет на мощь
            if hasattr(penis, 'length'):
                power += (penis.length - 15) * 0.02  # Бонус за каждый см выше 15
        
        # Яички дают регенерацию маны
        if hasattr(body, 'scrotum') and hasattr(body.scrotum, 'testicles'):
            testicles = body.scrotum.testicles
            total_sperm = sum(t.current_volume for t in testicles)
            power += total_sperm / 1000  # +0.1 за каждые 100мл
            
        return power


class CumShot(CumSkill):
    """
    Спермный выстрел - базовая атака.
    """
    def __init__(self):
        super().__init__(
            name="Cum Shot",
            description="Выстреливает зарядом спермы под высоким давлением.",
            school=MagicSchool.CUM,
            costs=[cum_cost("penis", 30, 10)],
            effects=[SkillEffect("damage", 20)],
            target=SkillTarget.ENEMY,
            cooldown=0,
            requires_form="male"
        )
    
    def use(self, caster, target=None, target_organ=None):
        # Бонус если яички полные
        if hasattr(caster, 'scrotum'):
            total_vol = caster.scrotum.get_total_volume()
            max_vol = caster.scrotum.get_total_max_volume()
            if total_vol > max_vol * 0.9:
                self.effects[0].value = 35  # Крит
            else:
                self.effects[0].value = 20
        return super().use(caster, target, target_organ)


class VirilityBoost(CumSkill):
    """
    Усиление вирильности - бафф на силу.
    Использует сперму для усиления мышц.
    """
    def __init__(self):
        super().__init__(
            name="Virility Boost",
            description="Поглощает сперму для временного усиления физических параметров.",
            school=MagicSchool.CUM,
            costs=[cum_cost("scrotum", 100, 50)],
            effects=[SkillEffect("buff", 2.0, duration=4)],
            target=SkillTarget.SELF,
            cooldown=6,
            requires_form="male"
        )


class ProstateStrike(CumSkill):
    """
    Удар простаты - точечная атака с оглушением.
    Требует простату (если добавлена).
    """
    def __init__(self):
        super().__init__(
            name="Prostate Strike",
            description="Высвобождает накопленную жидкость простаты мощным импульсом.",
            school=MagicSchool.CUM,
            costs=[cum_cost("prostate", 80, 20)],
            effects=[SkillEffect("damage", 45), SkillEffect("debuff", 0, duration=1)],
            target=SkillTarget.ENEMY,
            cooldown=4,
            requires_form="male"
        )


class SpermClone(CumSkill):
    """
   поровое клонирование - создаёт клона из спермы.
    Требует огромного количества.
    """
    def __init__(self):
        super().__init__(
            name="Sperm Clone",
            description="Создаёт временного клона из конденсированной спермы.",
            school=MagicSchool.CUM,
            costs=[
                cum_cost("scrotum", 500, 200),
                cum_cost("penis", 100, 50)
            ],
            effects=[SkillEffect("summon", 1, duration=3)],
            target=SkillTarget.SELF,
            cooldown=10,
            requires_form="male"
        )


class TesticularFortitude(CumSkill):
    """
    Яичковая стойкость - защитная реакция.
    При низком HP использует резервы спермы для защиты.
    """
    def __init__(self):
        super().__init__(
            name="Testicular Fortitude",
            description="Использует сперму как броню, поглощая урон.",
            school=MagicSchool.CUM,
            costs=[cum_cost("scrotum", 200, 100)],
            effects=[SkillEffect("buff", 50, duration=2)],
            target=SkillTarget.SELF,
            cooldown=8,
            requires_form="male"
        )
    
    def can_use(self, caster, target=None):
        # Можно использовать только при HP < 50%
        if hasattr(caster, 'health') and hasattr(caster, 'max_health'):
            if caster.health > caster.max_health * 0.5:
                return False, "Требуется здоровье ниже 50%"
        return super().can_use(caster, target)


class EjaculationStorm(CumSkill):
    """
    Эякуляционный шторм - массовая атака.
    Поражает всех врагов волной спермы.
    """
    def __init__(self):
        super().__init__(
            name="Ejaculation Storm",
            description="Выпускает сперму во все стороны, нанося урон всем врагам.",
            school=MagicSchool.CUM,
            costs=[cum_cost("penis", 300, 150)],
            effects=[SkillEffect("damage", 60)],
            target=SkillTarget.AREA,
            cooldown=6,
            requires_form="male"
        )


class SemenWeb(CumSkill):
    """
    Семенная сеть - контроль.
    Ловит врага липкой сетью.
    """
    def __init__(self):
        super().__init__(
            name="Semen Web",
            description="Создаёт липкую сеть из спермы, замедляя противника.",
            school=MagicSchool.CUM,
            costs=[cum_cost("penis", 60, 30)],
            effects=[SkillEffect("debuff", 0.5, duration=3)],
            target=SkillTarget.ENEMY,
            cooldown=3,
            requires_form="male"
        )


class VasectomyBlade(CumSkill):
    """
Вазэктомичный клинок - высокий урон, но наносит урон себе.
    Рискованная атака.
    """
    def __init__(self):
        super().__init__(
            name="Vasectomy Blade",
            description="Концентрирует сперму в острие, нанося огромный урон, но повреждая каналы.",
            school=MagicSchool.CUM,
            costs=[cum_cost("penis", 250, 100)],
            effects=[SkillEffect("damage", 120), SkillEffect("damage", 20, target_organ="penis")],
            target=SkillTarget.ENEMY,
            cooldown=5,
            requires_form="male"
        )


class ImpregnationIntent(CumSkill):
    """
    Намерение оплодотворения - дебафф.
    Увеличивает шанс крита против женских целей.
    """
    def __init__(self):
        super().__init__(
            name="Impregnation Intent",
            description="Магическое давление, ослабляющее женские цели.",
            school=MagicSchool.CUM,
            costs=[cum_cost("scrotum", 150, 50)],
            effects=[SkillEffect("debuff", 1.5, duration=4)],
            target=SkillTarget.ENEMY,
            cooldown=5,
            requires_form="male"
        )
    
    def can_use(self, caster, target=None):
        # Только против женских форм
        if target and hasattr(target, 'body_form'):
            if target.body_form.value not in ['female', 'futanari']:
                return False, "Только против женских целей"
        return super().can_use(caster, target)


def get_male_skills() -> List[BaseSkill]:
    """Стартовые скиллы для мужского персонажа"""
    return [
        CumShot(),
        VirilityBoost(),
        SemenWeb(),
        TesticularFortitude()
    ]


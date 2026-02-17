import random
from typing import TYPE_CHECKING
from .core import DamageType, StatusEffect, Stunned, Leaking

if TYPE_CHECKING:
    from .core import Combatant

class Skill:
    def __init__(self, name: str, ap_cost: int, cooldown: int = 0):
        self.name = name
        self.ap_cost = ap_cost
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.description = ""
    
    def can_use(self, user: 'Combatant', target: 'Combatant' = None) -> bool:
        return True
    
    def execute(self, user: 'Combatant', target: 'Combatant') -> str:
        raise NotImplementedError
    
    def tick_cooldown(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

class MilkSpraySkill(Skill):
    def __init__(self):
        super().__init__("Milk Spray", 2, 2)
        self.description = "Выстрел молоком под давлением. Требует >20% наполнения груди."
    
    def can_use(self, user, target=None) -> bool:
        if not hasattr(user.body, 'breast_grid') or not user.body.breast_grid:
            return False
        try:
            breast = user.body.breast_grid.get(0, 0)
            fill = getattr(breast, 'fill_percentage', 0)
            lact_active = False
            if hasattr(breast, 'lactation'):
                lact_active = getattr(breast.lactation, 'state', 'DRY') != 'DRY'
            return fill > 20 and lact_active and self.current_cooldown == 0
        except:
            return False
    
    def execute(self, user, target) -> str:
        breast = user.body.breast_grid.get(0, 0)
        pressure = getattr(breast, 'pressure', 50)
        fill = getattr(breast, 'fill_percentage', 0)
        
        damage = 15 + (pressure / 10) + (fill / 5)
        
        # Расход молока
        if hasattr(breast, 'remove_fluid'):
            milk_spent = getattr(breast, 'volume', 500) * 0.3
            breast.remove_fluid(milk_spent)
        
        # Открытие сосков
        if hasattr(breast, 'areola') and hasattr(breast.areola, 'nipples'):
            if breast.areola.nipples:
                nipple = breast.areola.nipples[0]
                if hasattr(nipple, 'gape'):
                    nipple.gape = min(getattr(nipple, 'width', 1.0), nipple.gape + 0.2)
        
        target.apply_status_effect(Leaking("milk", 5))
        target.take_damage(damage, DamageType.FLUID)
        
        self.current_cooldown = self.cooldown
        return (f"💦 {user.name} стреляет молоком с давлением {pressure:.0f}мм! "
                f"Урон: {damage:.1f}")

class BreastCrushSkill(Skill):
    def __init__(self):
        super().__init__("Breast Crush", 2, 0)
        self.description = "Давление объемом груди (>800ml). Оглушает при >2000ml."
    
    def can_use(self, user, target=None) -> bool:
        if not hasattr(user.body, 'breast_grid') or not user.body.breast_grid:
            return False
        try:
            breast = user.body.breast_grid.get(0, 0)
            return breast.volume > 800
        except:
            return False
    
    def execute(self, user, target) -> str:
        breast = user.body.breast_grid.get(0, 0)
        volume = breast.volume
        sag = getattr(breast, 'sag', 0)
        
        damage = (volume / 100) + (sag * 2) + 10
        target.take_damage(damage, DamageType.BLUNT)
        
        if volume > 2000:
            target.apply_status_effect(Stunned(1))
            return (f"🍈 {user.name} раздавливает {target.name} грудью {volume:.0f}ml! "
                    f"Урон: {damage:.1f}. Оглушение!")
        return (f"🍈 {user.name} давит грудью {volume:.0f}ml! Урон: {damage:.1f}")

class UterusSlamSkill(Skill):
    def __init__(self):
        super().__init__("Uterus Slam", 3, 3)
        self.description = "Удар маткой. Требует пролапс или >60% наполнения."
    
    def can_use(self, user, target=None) -> bool:
        if not hasattr(user.body, 'uterus_system') or not user.body.uterus_system:
            return False
        try:
            u = user.body.uterus_system.uteri[0]
            has_prolapse = getattr(u, 'prolapse_state', False)
            fill = getattr(u, 'fill_percentage', 0)
            return (has_prolapse or fill > 60) and self.current_cooldown == 0
        except:
            return False
    
    def execute(self, user, target) -> str:
        u = user.body.uterus_system.uteri[0]
        fill = getattr(u, 'fill_percentage', 0)
        has_prolapse = getattr(u, 'prolapse_state', False)
        
        damage = 25 + (fill / 4)
        if has_prolapse:
            damage *= 1.5
        
        target.take_damage(damage, DamageType.BLUNT)
        
        spill_text = ""
        if hasattr(u, 'drain_all'):
            removed = u.drain_all()
            total = sum(removed.values())
            if total > 0:
                spill_text = f" Выплеснуто {total:.0f}ml!"
        
        self.current_cooldown = self.cooldown
        return (f"🌸 {user.name} бьет маткой! Урон: {damage:.1f}.{spill_text}")

class ProlapseWhipSkill(Skill):
    def __init__(self):
        super().__init__("Prolapse Whip", 2, 1)
        self.description = "Хлестанье пролапсированной маткой. Кровотечение."
    
    def can_use(self, user, target=None) -> bool:
        if not hasattr(user.body, 'uterus_system'):
            return False
        try:
            u = user.body.uterus_system.uteri[0]
            return getattr(u, 'prolapse_state', False) and getattr(u, 'prolapse_level', 0) >= 2
        except:
            return False
    
    def execute(self, user, target) -> str:
        damage = 20
        target.take_damage(damage, DamageType.PIERCE)
        
        # Усугубление пролапса
        if hasattr(user.body, 'uterus_system'):
            u = user.body.uterus_system.uteri[0]
            if hasattr(u, 'prolapse_level'):
                u.prolapse_level += 0.5
        
        return (f"🩸 {user.name} хлещет выпавшей маткой! Рваный урон: {damage}")

class EjaculationBlastSkill(Skill):
    def __init__(self):
        super().__init__("Cum Blast", 2, 2)
        self.description = "Выстрел спермой. Урон зависит от запаса."
    
    def can_use(self, user, target=None) -> bool:
        if not hasattr(user.body, 'penises') or not user.body.penises:
            return False
        p = user.body.penises[0]
        vol = getattr(p, 'fluid_storage', None)
        return vol and vol.current_volume > 10 if vol else False
    
    def execute(self, user, target) -> str:
        p = user.body.penises[0]
        vol = getattr(p, 'fluid_storage', None)
        
        if vol:
            amount = min(vol.current_volume, 50)
            vol.current_volume -= amount
        else:
            amount = 10
        
        damage = 10 + (amount / 2)
        
        if random.random() < 0.3:
            damage *= 2
            crit = " Крит в лицо!"
        else:
            crit = ""
        
        target.apply_status_effect(StatusEffect("Липкий", 2, "debuff"))
        target.take_damage(damage, DamageType.FLUID)
        
        self.current_cooldown = self.cooldown
        return (f"🍆💦 {user.name} стреляет {amount:.0f}ml! Урон: {damage:.1f}.{crit}")

class OvaryBurstSkill(Skill):
    def __init__(self):
        super().__init__("Ovary Burst", 3, 5)
        self.description = "Жертвенный взрыв яичника. Мощный гормональный урон."
    
    def can_use(self, user, target=None) -> bool:
        return hasattr(user.body, 'uterus_system') and user.body.uterus_system
    
    def execute(self, user, target) -> str:
        user.take_damage(15, DamageType.INTERNAL)
        hormone_dmg = 40
        target.take_damage(hormone_dmg, DamageType.HORMONE)
        target.stats.arousal += 30
        
        self.current_cooldown = self.cooldown
        return (f"💥 {user.name} разрывает фолликул! Гормональный удар: {hormone_dmg}")

class DeepPierceAttack(Skill):
    def __init__(self):
        super().__init__("Deep Pierce", 3, 0)
        self.description = "Глубокое проникновение с растяжением."
    
    def can_use(self, user, target=None) -> bool:
        has_penis = hasattr(user.body, 'penises') and user.body.penises
        if not target:
            return has_penis
        has_hole = (hasattr(target.body, 'vaginas') and target.body.vaginas) or \
                   (hasattr(target.body, 'anuses') and target.body.anuses)
        return has_penis and has_hole
    
    def execute(self, user, target) -> str:
        p = user.body.penises[0]
        penis_len = getattr(p, 'length', 15)
        
        hole = None
        hole_name = ""
        if hasattr(target.body, 'vaginas') and target.body.vaginas:
            hole = target.body.vaginas[0]
            hole_name = "вагину"
        elif hasattr(target.body, 'anuses') and target.body.anuses:
            hole = target.body.anuses[0]
            hole_name = "анус"
        
        if not hole:
            return "Нет доступного отверстия!"
        
        depth = getattr(hole, 'depth', 10)
        stretch_dmg = max(0, (penis_len - depth) * 3)
        
        target.take_damage(stretch_dmg, DamageType.STRETCH)
        
        if hasattr(hole, 'stretch'):
            hole.stretch = getattr(hole, 'stretch', 0) + 0.5
        
        extra = ""
        if penis_len > depth + 5 and hasattr(target.body, 'uterus_system'):
            target.take_damage(15, DamageType.INTERNAL)
            extra = " + урон матке!"
        
        return (f"➡️ {user.name} глубоко в {hole_name} {target.name}! "
                f"Растяжение: {stretch_dmg:.1f}.{extra}")
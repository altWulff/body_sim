from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Optional, TYPE_CHECKING
from rich.panel import Panel
from rich.text import Text

if TYPE_CHECKING:
    from body_sim.systems.events import EventfulBody

class DamageType(Enum):
    BLUNT = auto()
    PIERCE = auto()
    FLUID = auto()
    STRETCH = auto()
    HORMONE = auto()
    INTERNAL = auto()

@dataclass
class CombatStats:
    hp: float = 100.0
    max_hp: float = 100.0
    ap: int = 3
    max_ap: int = 3
    arousal: float = 0.0
    pain_threshold: float = 50.0
    defense: float = 0.0
    
    def __post_init__(self):
        self.max_hp = self.hp

class StatusEffect:
    def __init__(self, name: str, duration: int, effect_type: str = "neutral"):
        self.name = name
        self.duration = duration
        self.effect_type = effect_type
    
    def on_tick(self, target: 'Combatant'):
        pass
    
    def on_apply(self, target: 'Combatant'):
        pass

class Stunned(StatusEffect):
    def __init__(self, duration: int = 1):
        super().__init__("Оглушение", duration, "debuff")
    
    def on_apply(self, target: 'Combatant'):
        target.stats.ap = 0

class Leaking(StatusEffect):
    def __init__(self, fluid_type: str, amount: float):
        super().__init__(f"Утечка {fluid_type}", 3, "debuff")
        self.fluid_type = fluid_type
        self.amount = amount
    
    def on_tick(self, target: 'Combatant'):
        if hasattr(target.body, 'remove_fluid'):
            try:
                target.body.remove_fluid(self.fluid_type, self.amount)
            except:
                pass

class Combatant:
    """Обертка над EventfulBody для боевой системы"""
    def __init__(self, body: 'EventfulBody', name: str):
        self.body = body
        self.name = name
        self.stats = CombatStats()
        self.status_effects: List[StatusEffect] = []
        self.skills: List = []
        self.team = "neutral"
        self._init_skills()
    
    def _init_skills(self):
        """Авто-добавление скиллов на основе анатомии"""
        from .skills import (
            MilkSpraySkill, BreastCrushSkill, UterusSlamSkill,
            ProlapseWhipSkill, EjaculationBlastSkill, OvaryBurstSkill,
            DeepPierceAttack
        )
        
        # Скиллы груди
        if hasattr(self.body, 'breast_grid') and self.body.breast_grid:
            self.skills.append(MilkSpraySkill())
            try:
                breast = self.body.breast_grid.get(0, 0)
                if hasattr(breast, 'volume') and breast.volume > 800:
                    self.skills.append(BreastCrushSkill())
            except:
                pass
        
        # Скиллы матки
        if hasattr(self.body, 'uterus_system') and self.body.uterus_system:
            self.skills.append(UterusSlamSkill())
            try:
                uterus = self.body.uterus_system.uteri[0]
                if hasattr(uterus, 'prolapse_state') and uterus.prolapse_state:
                    self.skills.append(ProlapseWhipSkill())
            except:
                pass
        
        # Скиллы пениса
        if hasattr(self.body, 'penises') and self.body.penises:
            self.skills.append(EjaculationBlastSkill())
            if hasattr(self.body, 'vaginas') or hasattr(self.body, 'anuses'):
                self.skills.append(DeepPierceAttack())
        
        # Скиллы яичников
        if hasattr(self.body, 'uterus_system') and self.body.uterus_system:
            try:
                if self.body.uterus_system.uteri[0].left_ovary:
                    self.skills.append(OvaryBurstSkill())
            except:
                pass
    
    def take_damage(self, amount: float, dmg_type: DamageType, target_organ: str = None):
        actual_damage = amount * (1 - self.stats.defense / 100)
        
        # Модификаторы от анатомии
        if target_organ:
            # Проверка растяжения органов
            try:
                if 'breast' in target_organ and hasattr(self.body, 'breast_grid'):
                    breast = self.body.breast_grid.get(0, 0)
                    if hasattr(breast, 'pressure'):
                        if breast.pressure > 80:
                            actual_damage *= 1.3  # Переполненная грудь уязвима
            except:
                pass
        
        self.stats.hp -= actual_damage
        
        # Критические эффекты
        if self.stats.hp < 20:
            self.apply_status_effect(StatusEffect("Критическое состояние", 999, "critical"))
        
        return actual_damage
    
    def heal(self, amount: float):
        self.stats.hp = min(self.stats.max_hp, self.stats.hp + amount)
    
    def apply_status_effect(self, effect: StatusEffect):
        effect.on_apply(self)
        self.status_effects.append(effect)
    
    def tick_status_effects(self):
        for effect in self.status_effects[:]:
            effect.on_tick(self)
            effect.duration -= 1
            if effect.duration <= 0:
                self.status_effects.remove(effect)
    
    def is_alive(self) -> bool:
        return self.stats.hp > 0
    
    def can_act(self) -> bool:
        return self.is_alive() and not any(isinstance(e, Stunned) for e in self.status_effects)
    
    def get_status_panel(self) -> Panel:
        hp_pct = self.stats.hp / self.stats.max_hp
        hp_color = "red" if hp_pct < 0.3 else "yellow" if hp_pct < 0.6 else "green"
        hp_bar = "█" * int(hp_pct * 10) + "░" * (10 - int(hp_pct * 10))
        
        effects_str = ", ".join([f"{e.name}({e.duration})" for e in self.status_effects]) or "Нет"
        
        # Анатомический статус
        anatomy_lines = []
        
        # Грудь
        if hasattr(self.body, 'breast_grid') and self.body.breast_grid:
            try:
                breast = self.body.breast_grid.get(0, 0)
                vol = getattr(breast, 'volume', 0)
                press = getattr(breast, 'pressure', 0)
                anatomy_lines.append(f"🍈 {vol:.0f}ml {press:.0f}mmHg")
            except:
                pass
        
        # Матка
        if hasattr(self.body, 'uterus_system') and self.body.uterus_system:
            try:
                u = self.body.uterus_system.uteri[0]
                fill = u.fill_percentage if hasattr(u, 'fill_percentage') else 0
                prolapse = "ВЫВОРОТ" if getattr(u, 'prolapse_state', False) else ""
                anatomy_lines.append(f"🌸 {fill:.0f}% {prolapse}")
            except:
                pass
        
        # Пенис
        if hasattr(self.body, 'penises') and self.body.penises:
            try:
                p = self.body.penises[0]
                vol = getattr(p, 'fluid_storage', None)
                vol_str = f"{vol.current_volume:.0f}ml" if vol else "сухой"
                anatomy_lines.append(f"🍆 {vol_str}")
            except:
                pass
        
        content = Text()
        content.append(f"HP: [{hp_bar}] {self.stats.hp:.0f}/{self.stats.max_hp}\n", style=hp_color)
        content.append(f"AP: {'●' * self.stats.ap}{'○' * (self.stats.max_ap - self.stats.ap)}\n")
        content.append(f"Возбуждение: {self.stats.arousal:.0f}%\n")
        content.append(f"Статусы: {effects_str}\n")
        content.append("─" * 20 + "\n")
        content.append("\n".join(anatomy_lines))
        
        border = "red" if not self.is_alive() else ("yellow" if not self.can_act() else "blue")
        return Panel(content, title=f"[bold]{self.name}[/]", border_style=border)


class CombatManager:
    """Управление боем"""
    def __init__(self):
        self.participants: List[Combatant] = []
        self.current_turn = 0
        self.round = 1
        self.combat_log: List[str] = []
        self.active = False
    
    def add_combatant(self, combatant: Combatant, team: str = "A"):
        combatant.team = team
        self.participants.append(combatant)
    
    def get_current(self) -> Optional[Combatant]:
        if not self.participants or not self.active:
            return None
        
        alive_participants = [p for p in self.participants if p.is_alive()]
        if not alive_participants:
            return None
            
        for _ in range(len(self.participants)):
            idx = self.current_turn % len(self.participants)
            candidate = self.participants[idx]
            if candidate.is_alive():
                return candidate
            self.current_turn += 1
        return None
    
    def next_turn(self):
        current = self.get_current()
        if current:
            current.tick_status_effects()
            current.stats.ap = current.stats.max_ap
            for skill in current.skills:
                if hasattr(skill, 'tick_cooldown'):
                    skill.tick_cooldown()
        
        self.current_turn += 1
        if self.current_turn >= len(self.participants):
            self.current_turn = 0
            self.round += 1
    
    def execute_skill(self, user: Combatant, skill_idx: int, target: Combatant) -> str:
        if skill_idx < 0 or skill_idx >= len(user.skills):
            return "Неверный номер скила!"
        
        skill = user.skills[skill_idx]
        
        if user.stats.ap < skill.ap_cost:
            return f"Недостаточно AP! Нужно {skill.ap_cost}, есть {user.stats.ap}."
        
        if skill.current_cooldown > 0:
            return f"Скилл на перезарядке! Осталось {skill.current_cooldown} ходов."
        
        if not skill.can_use(user, target):
            return "Невозможно использовать этот скилл сейчас!"
        
        result = skill.execute(user, target)
        user.stats.ap -= skill.ap_cost
        
        if not target.is_alive():
            result += f"\n☠️ {target.name} повержен!"
        
        self.log(result)
        return result
    
    def log(self, message: str):
        self.combat_log.append(message)
        if len(self.combat_log) > 20:
            self.combat_log.pop(0)
    
    def is_combat_end(self) -> bool:
        teams = {}
        for p in self.participants:
            if p.is_alive():
                teams[p.team] = teams.get(p.team, 0) + 1
        return len(teams) <= 1 or not self.active
    
    def get_winner(self) -> Optional[str]:
        if not self.is_combat_end():
            return None
        alive = [p for p in self.participants if p.is_alive()]
        if len(alive) == 1:
            return alive[0].name
        return None
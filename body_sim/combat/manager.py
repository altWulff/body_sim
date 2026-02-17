from typing import List, Optional
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from combat.core import Combatant, StatusEffect

class CombatManager:
    def __init__(self):
        self.participants: List[Combatant] = []
        self.current_turn = 0
        self.round = 1
        self.combat_log: List[str] = []
        self.max_log_lines = 10
    
    def add_combatant(self, combatant: Combatant, team: str = "A"):
        combatant.team = team
        self.participants.append(combatant)
    
    def get_current(self) -> Optional[Combatant]:
        if not self.participants:
            return None
        # Пропускаем мертвых
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
            # Восстановление AP
            current.stats.ap = current.stats.max_ap
            # Кулдауны скиллов
            for skill in current.skills:
                skill.tick_cooldown()
        
        self.current_turn += 1
        if self.current_turn >= len(self.participants):
            self.current_turn = 0
            self.round += 1
    
    def execute_skill(self, skill_idx: int, target_name: str) -> str:
        user = self.get_current()
        if not user:
            return "Нет активного бойца!"
        
        if not user.can_act():
            self.next_turn()
            return f"{user.name} оглушен и пропускает ход."
        
        target = next((p for p in self.participants if p.name == target_name), None)
        if not target:
            return f"Цель {target_name} не найдена!"
        
        if target == user:
            return "Нельзя атаковать себя!"
        
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
        self.log(result)
        
        if not target.is_alive():
            self.log(f"☠️ {target.name} повержен!")
        
        if user.stats.ap <= 0:
            self.next_turn()
        
        return result
    
    def log(self, message: str):
        self.combat_log.append(message)
        if len(self.combat_log) > self.max_log_lines:
            self.combat_log.pop(0)
    
    def get_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="log", size=8)
        )
        
        # Header
        current = self.get_current()
        turn_text = f"Раунд {self.round} | Ход: {current.name if current else 'None'} (AP: {current.stats.ap if current else 0})"
        layout["header"].update(Panel(turn_text, style="bold red"))
        
        # Main - бойцы
        main_layout = Layout()
        cols = []
        for i, p in enumerate(self.participants):
            cols.append(Layout(p.get_status_panel(), name=f"p{i}"))
        main_layout.split_row(*cols)
        layout["main"].update(main_layout)
        
        # Log
        log_text = "\n".join(self.combat_log[-5:])
        layout["log"].update(Panel(log_text, title="Боевой журнал", style="dim"))
        
        return layout
    
    def get_available_skills_table(self) -> Table:
        current = self.get_current()
        if not current:
            return Table(title="Нет активного бойца")
        
        table = Table(title=f"Скиллы {current.name} (AP: {current.stats.ap})")
        table.add_column("#", style="cyan")
        table.add_column("Название", style="green")
        table.add_column("AP", style="yellow")
        table.add_column("CD", style="red")
        table.add_column("Описание")
        
        for i, skill in enumerate(current.skills):
            can_use = skill.can_use(current) and skill.current_cooldown == 0 and current.stats.ap >= skill.ap_cost
            style = "green" if can_use else "dim"
            cd_text = str(skill.current_cooldown) if skill.current_cooldown > 0 else "Готов"
            table.add_row(
                str(i+1),
                skill.name,
                str(skill.ap_cost),
                cd_text,
                skill.description,
                style=style
            )
        
        return table
    
    def is_combat_end(self) -> bool:
        teams = {}
        for p in self.participants:
            if p.is_alive():
                teams[p.team] = teams.get(p.team, 0) + 1
        return len(teams) <= 1

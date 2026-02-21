"""
Интеграция магии с боевой системой body_sim.
"""
from typing import Dict, List, Optional
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

class MagicCombatSystem:
    """Расширение боевой системы для магии"""
    
    def __init__(self, combat_system):
        self.combat = combat_system
        self.active_effects: Dict[str, List[Dict]] = {}  # char_name -> effects
    
    def get_skill_book(self, character_name: str) -> Optional['SkillBook']:
        """Получение книги скиллов персонажа"""
        char = self.combat.get_character(character_name)
        if char and hasattr(char, 'skill_book'):
            return char.skill_book
        return None
    
    def cast_skill(
        self,
        caster_name: str,
        skill_name: str,
        target_name: Optional[str] = None,
        target_organ: Optional[str] = None
    ) -> Dict:
        """Использование скилла в бою"""
        caster = self.combat.get_character(caster_name)
        target = self.combat.get_character(target_name) if target_name else None
        
        if not caster:
            return {"success": False, "message": f"Персонаж {caster_name} не найден"}
        
        if not hasattr(caster, 'skill_book'):
            return {"success": False, "message": f"{caster_name} не умеет использовать магию"}
        
        # Используем скилл
        result = caster.skill_book.use_skill(skill_name, target, target_organ=target_organ)
        
        if result["success"]:
            # Добавляем в лог боя
            self.combat.add_to_log(f"[magic] {result['message']}")
            
            # Обрабатываем эффекты урона/лечения для боевой системы
            for effect_result in result.get("results", []):
                if effect_result.get("type") == "damage":
                    if target:
                        damage = effect_result.get("value", 0)
                        target.take_damage(damage)
                        self.combat.add_to_log(f"  Нанесено {damage:.1f} урона")
                
                elif effect_result.get("type") == "heal":
                    heal = effect_result.get("amount", 0)
                    caster.heal(heal)
                    self.combat.add_to_log(f"  Восстановлено {heal:.1f} HP")
        
        return result
    
    def get_available_skills_display(self, character_name: str) -> Table:
        """Создание таблицы доступных скиллов"""
        table = Table(title=f"Доступные скиллы: {character_name}")
        table.add_column("№", style="cyan", width=3)
        table.add_column("Название", style="green")
        table.add_column("Школа", style="magenta")
        table.add_column("Стоимость", style="yellow")
        table.add_column("КД", style="red", width=4)
        table.add_column("Статус", style="white")
        
        book = self.get_skill_book(character_name)
        if not book:
            return table
        
        for idx, (name, skill) in enumerate(book.skills.items(), 1):
            can_use, reason = skill.can_use(book.body)
            
            # Формируем строку стоимости
            costs = []
            for cost in skill.costs:
                organ = cost._get_organ(book.body)
                current = organ.current_volume if organ else 0
                costs.append(f"{cost.fluid_type.name}: {current:.0f}/{cost.amount:.0f}ml")
            cost_str = " | ".join(costs) if costs else "Бесплатно"
            
            status = "[green]✓ Готов[/green]" if can_use else f"[red]✗ {reason}[/red]"
            
            school_color = {
                "MILK": "white",
                "CUM": "yellow",
                "HYBRID": "purple"
            }.get(skill.school.name, "white")
            
            table.add_row(
                str(idx),
                name,
                f"[{school_color}]{skill.school.name}[/{school_color}]",
                cost_str,
                str(skill.cooldown),
                status
            )
        
        return table
    
    def get_perks_display(self, character_name: str) -> Table:
        """Отображение перков персонажа"""
        table = Table(title=f"Перки: {character_name}")
        table.add_column("Название", style="green")
        table.add_column("Тип", style="cyan")
        table.add_column("Ранг", style="yellow")
        table.add_column("Описание", style="white")
        
        book = self.get_skill_book(character_name)
        if not book:
            return table
        
        for perk in book.passive_perks:
            table.add_row(
                perk.name,
                perk.perk_type.value,
                f"{perk.current_rank}/{perk.max_rank}",
                perk.description
            )
        
        return table


# Команды для консоли
class MagicCommands:
    """Команды для управления магией в консоли"""
    
    def __init__(self, registry, combat_system):
        self.registry = registry
        self.magic = MagicCombatSystem(combat_system)
    
    def cmd_skills(self, args):
        """Показать доступные скиллы"""
        if not args:
            target = self.registry.get_active_body()
            if not target:
                return "Ошибка: Нет активного персонажа"
            name = target.name
        else:
            name = args[0]
        
        return self.magic.get_available_skills_display(name)
    
    def cmd_cast(self, args):
        """Использовать скилл: cast <skill_name> [target] [organ]"""
        if len(args) < 1:
            return "Использование: cast <название_скилла> [цель] [орган]"
        
        skill_name = args[0]
        target = args[1] if len(args) > 1 else None
        organ = args[2] if len(args) > 2 else None
        
        caster = self.registry.get_active_body()
        if not caster:
            return "Ошибка: Нет активного персонажа"
        
        result = self.magic.cast_skill(caster.name, skill_name, target, organ)
        
        if result["success"]:
            msg = f"✨ {result['message']}"
            for res in result.get("results", []):
                if res.get("type") == "damage":
                    msg += f"\\n  💥 Урон: {res.get('value', 0):.1f}"
                elif res.get("type") == "heal":
                    msg += f"\\n  💚 Лечение: {res.get('amount', 0):.1f}"
                elif res.get("type") == "fill":
                    msg += f"\\n  💧 Наполнение {res.get('organ')}: +{res.get('amount', 0):.1f}ml"
            return msg
        else:
            return f"✗ {result['message']}"
    
    def cmd_perks(self, args):
        """Показать перки персонажа"""
        target = self.registry.get_active_body()
        if not target:
            return "Ошибка: Нет активного персонажа"
        
        return self.magic.get_perks_display(target.name)
    
    def cmd_learn_skill(self, args):
        """Выучить новый скилл: learn_skill <skill_class>"""
        if not args:
            return "Использование: learn_skill <имя_класса_скилла>"
        
        skill_class = args[0]
        body = self.registry.get_active_body()
        
        if not body:
            return "Ошибка: Нет активного персонажа"
        
        # Импортируем и создаём скилл
        try:
            if skill_class in ["MilkSpray", "LactationHeal", "BreastShield"]:
                from magic.skills.milk_skills import MilkSpray, LactationHeal, BreastShield
                skill_map = {
                    "MilkSpray": MilkSpray,
                    "LactationHeal": LactationHeal,
                    "BreastShield": BreastShield
                }
                skill = skill_map[skill_class]()
            elif skill_class in ["CumShot", "VirilityBoost"]:
                from magic.skills.cum_skills import CumShot, VirilityBoost
                skill_map = {
                    "CumShot": CumShot,
                    "VirilityBoost": VirilityBoost
                }
                skill = skill_map[skill_class]()
            else:
                return f"Неизвестный скилл: {skill_class}"
            
            if hasattr(body, 'skill_book'):
                body.skill_book.add_skill(skill)
                return f"✓ Выучен скилл: {skill.name}"
            else:
                return "Ошибка: Персонаж не имеет книги скиллов"
                
        except Exception as e:
            return f"Ошибка: {e}"
    
    def cmd_add_perk(self, args):
        """Добавить перк: add_perk <perk_class> [organ]"""
        if not args:
            return "Использование: add_perk <имя_перка> [орган]"
        
        perk_name = args[0]
        organ = args[1] if len(args) > 1 else None
        
        body = self.registry.get_active_body()
        if not body:
            return "Ошибка: Нет активного персонажа"
        
        from magic.perks.base_perks import (
            FluidRegenerationPerk, OverfillCapacityPerk,
            PressureMasteryPerk, SensitiveOrgansPerk
        )
        from fluid_system import FluidType
        
        perk = None
        if perk_name == "FluidRegeneration":
            if not organ:
                return "Укажите орган для регенерации"
            fluid = FluidType.MILK if organ in ["breasts", "uterus"] else FluidType.CUM
            perk = FluidRegenerationPerk(organ, fluid, 5.0)
        elif perk_name == "OverfillCapacity":
            if not organ:
                return "Укажите орган"
            perk = OverfillCapacityPerk(organ, 0.2)
        elif perk_name == "PressureMastery":
            perk = PressureMasteryPerk()
        elif perk_name == "SensitiveOrgans":
            if not organ:
                return "Укажите орган"
            perk = SensitiveOrgansPerk(organ)
        
        if perk and hasattr(body, 'skill_book'):
            perk.apply_to(body)
            body.skill_book.passive_perks.append(perk)
            return f"✓ Получен перк: {perk.name}"
        
        return "Неизвестный перк или ошибка"


def register_magic_commands(registry, combat_system):
    """Регистрация всех магических команд"""
    magic_cmds = MagicCommands(registry, combat_system)
    
    registry.register("skills", magic_cmds.cmd_skills, "Показать доступные скиллы")
    registry.register("cast", magic_cmds.cmd_cast, "Использовать скилл: cast <skill> [target] [organ]")
    registry.register("perks", magic_cmds.cmd_perks, "Показать перки персонажа")
    registry.register("learn", magic_cmds.cmd_learn_skill, "Выучить скилл: learn <SkillClass>")
    registry.register("add_perk", magic_cmds.cmd_add_perk, "Добавить перк: add_perk <PerkClass> [organ]")
    
    return magic_cmds



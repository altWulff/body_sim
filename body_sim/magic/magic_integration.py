"""
Интеграция магической системы в body_sim.
Этот файл должен быть импортирован в основной проект.
"""
from typing import Dict, List, Optional
from rich.panel import Panel
from rich.text import Text

# Импорты из модуля magic
from body_sim.magic.fluid_magic import SkillBook
from body_sim.magic.skills.milk_skills import get_female_skills
from body_sim.magic.skills.cum_skills import get_male_skills
from body_sim.magic.skills.hybrid_skills import get_futanari_skills
from body_sim.magic.ui.magic_render import MagicRenderer

class MagicMixin:
    """Миксин для добавления магии в класс Body"""
    
    def init_magic(self):
        """Инициализация магической системы - вызвать в __init__ Body"""
        self.skill_book = SkillBook(self)
        self.magic_power = 1.0
        self.magic_resistance = 0.0
        self._init_gender_skills()
        self.magic_effects = []
    
    def _init_gender_skills(self):
        """Загрузка стартовых скиллов по полу"""
        if not hasattr(self, 'body_form'):
            return
            
        form = self.body_form.value if hasattr(self.body_form, 'value') else str(self.body_form)
        
        if form == "female":
            for skill in get_female_skills():
                self.skill_book.add_skill(skill)
        elif form == "male":
            for skill in get_male_skills():
                self.skill_book.add_skill(skill)
        elif form == "futanari":
            for skill in get_futanari_skills():
                self.skill_book.add_skill(skill)
            # Добавляем базовые скиллы обоих полов для футанари
            from magic.skills.milk_skills import MilkSpray
            from magic.skills.cum_skills import CumShot
            self.skill_book.add_skill(MilkSpray())
            self.skill_book.add_skill(CumShot())
    
    def magic_tick(self):
        """Обновление магии - вызвать в tick() Body"""
        if hasattr(self, 'skill_book'):
            self.skill_book.tick()
        
        # Обновление эффектов
        for effect in getattr(self, 'magic_effects', [])[:]:
            effect['duration'] -= 1
            if effect['duration'] <= 0:
                self.magic_effects.remove(effect)
                if effect['type'] == 'buff':
                    self.magic_power /= effect['value']
    
    def get_mana_status(self) -> dict:
        """Получение статуса маны для UI"""
        status = {'sources': [], 'total_mana': 0, 'max_mana': 0}
        
        # Грудь (молоко)
        if hasattr(self, 'breasts'):
            fullness = self.breasts.current_volume / self.breasts.max_volume if self.breasts.max_volume > 0 else 0
            status['sources'].append({
                'name': 'breasts',
                'type': 'MILK',
                'current': self.breasts.current_volume,
                'max': self.breasts.max_volume,
                'fullness': fullness,
                'color': 'white' if fullness < 0.5 else ('yellow' if fullness < 0.9 else 'red')
            })
            status['total_mana'] += self.breasts.current_volume
            status['max_mana'] += self.breasts.max_volume
        
        # Матка
        if hasattr(self, 'uterus'):
            fullness = self.uterus.current_volume / self.uterus.max_volume if self.uterus.max_volume > 0 else 0
            fluid_type = self.uterus.get_fluid_type() if hasattr(self.uterus, 'get_fluid_type') else None
            status['sources'].append({
                'name': 'uterus',
                'type': fluid_type.name if fluid_type else 'EMPTY',
                'current': self.uterus.current_volume,
                'max': self.uterus.max_volume,
                'fullness': fullness,
                'color': 'cyan'
            })
            status['total_mana'] += self.uterus.current_volume
            status['max_mana'] += self.uterus.max_volume
        
        # Пенис (сперма)
        if hasattr(self, 'penises') and self.penises:
            penis = self.penises[0]
            if hasattr(penis, 'fluid_container'):
                fc = penis.fluid_container
                fullness = fc.current_volume / fc.max_volume if fc.max_volume > 0 else 0
                status['sources'].append({
                    'name': 'penis',
                    'type': 'CUM',
                    'current': fc.current_volume,
                    'max': fc.max_volume,
                    'fullness': fullness,
                    'color': 'yellow'
                })
                status['total_mana'] += fc.current_volume
                status['max_mana'] += fc.max_volume
        
        # Яичники/Яички
        if hasattr(self, 'scrotum') and hasattr(self.scrotum, 'testicles'):
            total = sum(t.current_volume for t in self.scrotum.testicles)
            max_total = sum(t.max_volume for t in self.scrotum.testicles)
            fullness = total / max_total if max_total > 0 else 0
            status['sources'].append({
                'name': 'testicles',
                'type': 'CUM',
                'current': total,
                'max': max_total,
                'fullness': fullness,
                'color': 'gold'
            })
            status['total_mana'] += total
            status['max_mana'] += max_total
        
        # Яичники (для female)
        if hasattr(self, 'ovaries'):
            total = sum(o.current_volume for o in self.ovaries)
            max_total = sum(o.max_volume for o in self.ovaries)
            if max_total > 0:
                fullness = total / max_total
                status['sources'].append({
                    'name': 'ovaries',
                    'type': 'FLUID',
                    'current': total,
                    'max': max_total,
                    'fullness': fullness,
                    'color': 'magenta'
                })
                status['total_mana'] += total
                status['max_mana'] += max_total
        
        status['total_fullness'] = status['total_mana'] / status['max_mana'] if status['max_mana'] > 0 else 0
        return status
    
    def cast_spell(self, spell_name: str, target=None, **kwargs) -> dict:
        """Упрощённый интерфейс для каста"""
        if not hasattr(self, 'skill_book'):
            return {"success": False, "message": "Нет магической системы"}
        
        result = self.skill_book.use_skill(spell_name, target, **kwargs)
        
        # Применение магической силы
        if result["success"] and hasattr(self, 'magic_power') and self.magic_power != 1.0:
            for res in result.get("results", []):
                if res.get("type") in ["damage", "heal", "fill"]:
                    res["value"] = res.get("value", 0) * self.magic_power
        
        return result
    
    def get_magic_renderer(self) -> MagicRenderer:
        """Получение рендерера"""
        return MagicRenderer(self)


# Функции для интеграции в команды
def register_magic_to_body(body_class):
    """
    Динамическое добавление магических методов в класс Body.
    Использовать если нельзя изменить исходный класс.
    """
    body_class.init_magic = MagicMixin.init_magic
    body_class.magic_tick = MagicMixin.magic_tick
    body_class.get_mana_status = MagicMixin.get_mana_status
    body_class.cast_spell = MagicMixin.cast_spell
    body_class.get_magic_renderer = MagicMixin.get_magic_renderer
    body_class._init_gender_skills = MagicMixin._init_gender_skills
    return body_class


# Класс для прямого наследования
class MagicalBody(MagicMixin):
    """Пример класса с полной интеграцией магии"""
    pass

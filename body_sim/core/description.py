#body_sim/core/description.py

from typing import List, Dict, Optional, Callable, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import re
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich import box

from body_sim.core.enums import (
    CupSize, BreastState, VaginaState, UterusState, 
    UterusInflationStatus, FluidType, PenisState
)
from body_sim.anatomy import *
from body_sim.body.body import Body


class DescriptionStyle(Enum):
    BRIEF = "brief"           # Кратко
    STANDARD = "standard"     # Обычное с упоминанием наполнения если существенно
    DETAILED = "detailed"     # Подробное описание содержимого
    CLINICAL = "clinical"     # Точные цифры и медицинские термины
    EROTIC = "erotic"         # Фокус на ощущениях от наполнения


class DescriptionParser:
    """Парсер шаблонов [tag.attr] с поддержкой содержимого органов"""
    
    def __init__(self, body: Body):
        self.body = body
        self.tags = self._build_tag_registry()
    
    def _build_tag_registry(self) -> Dict[str, Callable]:
        return {
            # Базовые
            'actor.name': lambda: getattr(self.body, 'name', 'она'),
            'actor.race': self._get_race_name,
            'actor.sex': self._get_sex_name,
            
            # Грудь
            'breasts.size': self._get_breast_size,
            'breasts.cup': self._get_breast_cup,
            'breasts.state': self._get_breast_state,
            'breasts.filled': self._get_breast_filled,
            'breasts.fullness': self._get_breast_fullness,
            'breasts.contents': self._get_breast_contents,
            
            # Матка
            'womb.status': self._get_womb_status,
            'womb.filled': self._get_womb_filled,
            'womb.fullness': self._get_womb_fullness,
            'womb.contents': self._get_womb_contents,
            'womb.inflation': self._get_womb_inflation,
            
            # Влагалище
            'vagina.wetness': self._get_vagina_wetness,
            'vagina.contents': self._get_vagina_contents,
            
            # Желудок
            'stomach.filled': self._get_stomach_filled,
            'stomach.contents': self._get_stomach_contents,
            
            # Анус/Прямая кишка
            'anus.contents': self._get_anus_contents,
            'rectum.filled': self._get_rectum_filled,
            
            # Пенис
            'penis.size': self._get_penis_size,
            'penis.contents': self._get_penis_contents,
            
            # Рот
            'mouth.contents': self._get_mouth_contents,
        }
    
    def parse(self, template: str) -> str:
        result = template
        
        # Простые замены
        for tag, func in self.tags.items():
            pattern = f'\\[{tag}\\]'
            result = re.sub(pattern, lambda m: func(), result)
        
        # Условия
        result = re.sub(r'\[if:pregnant:([^\]]+)\]', 
                       lambda m: m.group(1) if self._check_pregnant() else '', result)
        result = re.sub(r'\[if:lactating:([^\]]+)\]', 
                       lambda m: m.group(1) if self._check_lactating_any() else '', result)
        result = re.sub(r'\[if:erect:([^\]]+)\]', 
                       lambda m: m.group(1) if self._check_erect() else '', result)
        result = re.sub(r'\[if:womb_full:([^\]]+)\]',
                       lambda m: m.group(1) if self._check_womb_full() else '', result)
        result = re.sub(r'\[if:breasts_full:([^\]]+)\]',
                       lambda m: m.group(1) if self._check_breasts_full() else '', result)
        result = re.sub(r'\[if:stuffed:([^\]]+)\]',
                       lambda m: m.group(1) if self._check_any_organ_full() else '', result)
        
        return result
    
    def _get_race_name(self) -> str:
        race = getattr(self.body, 'race', 'человек')
        return race.name.lower() if hasattr(race, 'name') else str(race).lower()
    
    def _get_sex_name(self) -> str:
        sex = getattr(self.body, 'sex', 'женщина')
        return sex.name.lower() if hasattr(sex, 'name') else str(sex).lower()
    
    def _get_breast_size(self) -> str:
        if not self.body.breast_grid:
            return "плоская грудь"
        breasts = list(self.body.breast_grid.all())
        if not breasts:
            return "плоская грудь"
        max_cup = max(b.cup for b in breasts)
        return f"{max_cup.name}-cup грудь"
    
    def _get_breast_cup(self) -> str:
        if not self.body.breast_grid:
            return "AA"
        breasts = list(self.body.breast_grid.all())
        if not breasts:
            return "AA"
        return max(b.cup for b in breasts).name
    
    def _get_breast_state(self) -> str:
        if not self.body.breast_grid:
            return "пустая"
        for b in self.body.breast_grid.all():
            if b.state == BreastState.LEAKING:
                return "сочащаяся"
            elif b.state == BreastState.OVERPRESSURED:
                return "переполненная"
        return "нормальная"
    
    def _get_breast_filled(self) -> str:
        if not self.body.breast_grid:
            return "0"
        b = list(self.body.breast_grid.all())[0]
        return f"{b.filled:.0f}мл"
    
    def _get_breast_fullness(self) -> str:
        if not self.body.breast_grid:
            return "0%"
        b = list(self.body.breast_grid.all())[0]
        ratio = b.filled / b.volume if b.volume > 0 else 0
        return f"{ratio:.0%}"
    
    def _get_breast_contents(self) -> str:
        if not self.body.breast_grid:
            return "пустые"
        b = list(self.body.breast_grid.all())[0]
        
        parts = []
        if b.filled > 10:
            fluid = self._describe_fluid_type(b.mixture)
            parts.append(f"{b.filled:.0f}мл {fluid}")
        
        # Проверка вставленных предметов через insertion_manager
        if hasattr(b, 'insertion_manager') and b.insertion_manager:
            objs = getattr(b.insertion_manager, 'inserted_objects', [])
            if objs:
                obj_names = [getattr(o, 'name', 'предмет') for o in objs]
                parts.append(f"внутри: {', '.join(obj_names)}")
        
        return ", ".join(parts) if parts else "пустые"
    
    def _get_womb_status(self) -> str:
        if not self.body.uterus_system or not self.body.uterus_system.primary:
            return "нет матки"
        u = self.body.uterus_system.primary
        if self._check_pregnant():
            return "беременная"
        return u.state.name.lower() if u.state else "норма"
    
    def _get_womb_filled(self) -> str:
        if not self.body.uterus_system or not self.body.uterus_system.primary:
            return "0"
        u = self.body.uterus_system.primary
        return f"{u.filled:.0f}мл"
    
    def _get_womb_fullness(self) -> str:
        if not self.body.uterus_system or not self.body.uterus_system.primary:
            return "0%"
        u = self.body.uterus_system.primary
        ratio = u.fill_ratio if hasattr(u, 'fill_ratio') else (u.filled / u.current_volume if u.current_volume > 0 else 0)
        return f"{ratio:.0%}"
    
    def _get_womb_contents(self) -> str:
        if not self.body.uterus_system or not self.body.uterus_system.primary:
            return "пуста"
        u = self.body.uterus_system.primary
        
        parts = []
        if u.filled > 0:
            fluid = self._describe_fluid_type(u.mixture)
            parts.append(f"{u.filled:.0f}мл {fluid}")
        
        if u.inserted_objects:
            obj_names = [getattr(o, 'name', 'предмет') for o in u.inserted_objects]
            parts.append(f"внутри: {', '.join(obj_names)}")
        
        return ", ".join(parts) if parts else "пуста"
    
    def _get_womb_inflation(self) -> str:
        if not self.body.uterus_system or not self.body.uterus_system.primary:
            return "норма"
        u = self.body.uterus_system.primary
        return u.inflation_status.value
    
    def _get_vagina_wetness(self) -> str:
        if not self.body.vaginas:
            return "сухая"
        v = self.body.vaginas[0]
        wet = getattr(v, 'lubrication', 0)
        if wet > 0.7: return "текущая"
        if wet > 0.4: return "влажная"
        return "сухая"
    
    def _get_vagina_contents(self) -> str:
        if not self.body.vaginas:
            return "пусто"
        v = self.body.vaginas[0]
        
        parts = []
        # Пенис внутри
        if getattr(v, 'current_penetration', None):
            p = v.current_penetration
            parts.append(f"пенис ({p.current_length:.0f}см)")
        
        # Другие объекты
        if getattr(v, 'inserted_objects', None):
            obj_names = [getattr(o, 'name', 'предмет') for o in v.inserted_objects]
            parts.append(f"объекты: {', '.join(obj_names)}")
        
        # Жидкость
        if hasattr(v, 'mixture') and v.mixture.total() > 0:
            parts.append(f"{v.mixture.total():.0f}мл жидкости")
        
        return ", ".join(parts) if parts else "пусто"
    
    def _get_stomach_filled(self) -> str:
        if not self.body.stomach_system or not self.body.stomach_system.primary:
            return "0"
        s = self.body.stomach_system.primary
        return f"{s.filled:.0f}мл"
    
    def _get_stomach_contents(self) -> str:
        if not self.body.stomach_system or not self.body.stomach_system.primary:
            return "пуст"
        s = self.body.stomach_system.primary
        
        parts = []
        if s.filled > 0:
            fluid = self._describe_fluid_type(s.mixture)
            parts.append(f"{s.filled:.0f}мл {fluid}")
        
        if getattr(s, 'solid_content', 0) > 0:
            parts.append(f"твердой пищи: {s.solid_content:.0f}г")
        
        if getattr(s, 'inserted_object', None):
            parts.append(f"глубоко внутри: {s.inserted_object.name}")
        
        return ", ".join(parts) if parts else "пуст"
    
    def _get_anus_contents(self) -> str:
        if not self.body.anuses:
            return "пуст"
        a = self.body.anuses[0]
        
        parts = []
        obj = getattr(a, 'get_current_object', lambda: None)()
        if obj:
            parts.append(f"растянут вокруг {getattr(obj, 'name', 'предмета')} ({getattr(obj, 'diameter', 0):.1f}см)")
        
        if getattr(a, 'fluid_content', 0) > 0:
            parts.append(f"спермы: {a.fluid_content:.0f}мл")
        
        return ", ".join(parts) if parts else "пуст"
    
    def _get_rectum_filled(self) -> str:
        if not self.body.rectum_system or not self.body.rectum_system.primary:
            return "0"
        r = self.body.rectum_system.primary
        return f"{r.filled:.0f}мл" if hasattr(r, 'filled') else "?"
    
    def _get_penis_size(self) -> str:
        if not self.body.penises:
            return "отсутствует"
        p = self.body.penises[0]
        return f"{p.current_length:.0f}см"
    
    def _get_penis_contents(self) -> str:
        if not self.body.penises:
            return ""
        p = self.body.penises[0]
        if p.scrotum:
            cum = p.scrotum.total_stored_fluids.get(FluidType.CUM, 0)
            return f"спермы в яичках: {cum:.0f}мл"
        return ""
    
    def _get_mouth_contents(self) -> str:
        if not self.body.mouth_system or not self.body.mouth_system.primary:
            return "пуст"
        m = self.body.mouth_system.primary
        
        parts = []
        if getattr(m, 'inserted_object', None):
            parts.append(f"заполнен {getattr(m.inserted_object, 'name', 'предметом')}")
        
        if m.mixture.total() > 0:
            parts.append(f"жидкости: {m.mixture.total():.0f}мл")
        
        return ", ".join(parts) if parts else "пуст"
    
    def _describe_fluid_type(self, mixture) -> str:
        """Описывает тип жидкости из смеси"""
        if not mixture or not hasattr(mixture, 'components'):
            return "жидкости"
        
        if not mixture.components:
            return "жидкости"
        
        # Находим преобладающий тип
        primary = max(mixture.components.items(), key=lambda x: x[1])
        fluid_type = primary[0]
        
        names = {
            FluidType.CUM: "спермы",
            FluidType.MILK: "молока", 
            FluidType.WATER: "воды",
            FluidType.SALIVA: "слюны",
            FluidType.CHYLE: "химуса",
            FluidType.BLOOD: "крови",
            FluidType.EGG_WHITE: "яичной жидкости",
        }
        return names.get(fluid_type, "жидкости")
    
    def _check_pregnant(self) -> bool:
        if not self.body.uterus_system or not self.body.uterus_system.primary:
            return False
        u = self.body.uterus_system.primary
        return getattr(u, 'pregnant', False) or getattr(u, 'gestation_weeks', 0) > 0
    
    def _check_lactating_any(self) -> bool:
        if not self.body.breast_grid:
            return False
        return any(b.state == BreastState.LEAKING for b in self.body.breast_grid.all())
    
    def _check_erect(self) -> bool:
        return any(p.is_erect for p in self.body.penises) if self.body.penises else False
    
    def _check_womb_full(self) -> bool:
        if not self.body.uterus_system or not self.body.uterus_system.primary:
            return False
        u = self.body.uterus_system.primary
        return u.fill_ratio > 0.5 if hasattr(u, 'fill_ratio') else u.filled > 100
    
    def _check_breasts_full(self) -> bool:
        if not self.body.breast_grid:
            return False
        for b in self.body.breast_grid.all():
            ratio = b.filled / b.volume if b.volume > 0 else 0
            if ratio > 0.7:
                return True
        return False
    
    def _check_any_organ_full(self) -> bool:
        return self._check_womb_full() or self._check_breasts_full()


class AppearanceDescriptionEngine:
    """Генератор текстовых описаний с учетом наполнения органов"""
    
    def __init__(self, body: Body):
        self.body = body
        self.parser = DescriptionParser(body)
        
    def generate(self, style: DescriptionStyle = DescriptionStyle.STANDARD) -> str:
        if style == DescriptionStyle.BRIEF:
            return self._generate_brief()
        elif style == DescriptionStyle.CLINICAL:
            return self._generate_clinical()
        elif style == DescriptionStyle.EROTIC:
            return self._generate_erotic()
        elif style == DescriptionStyle.DETAILED:
            return self._generate_detailed()
        return self._generate_standard()
    
    def _generate_brief(self) -> str:
        parts = [self._describe_height(), self._describe_build()]
        
        if self.body.breast_grid:
            # Упоминаем если грудь переполнена
            if self._is_organ_full('breasts'):
                parts.append("с переполненными молоком грудями")
            else:
                parts.append(f"с {self._describe_breasts_brief()}")
        
        if self._check_pregnant():
            parts.append("и округлым животом")
        elif self._is_organ_full('womb'):
            parts.append("и раздутым животом")
            
        return " ".join(p for p in parts if p).capitalize() + "."
    
    def _generate_standard(self) -> str:
        sentences = []
        
        # Вводное
        intro = f"Перед тобой {self._describe_height()} {self._get_race_name()} {self._describe_build()}."
        sentences.append(intro)
        
        # Лицо
        face = self._describe_face()
        if face:
            sentences.append(f"У нее {face}.")
        
        # Тело + грудь
        body_desc = self._sentence_body()
        if body_desc:
            sentences.append(body_desc)
        
        # Нижняя часть
        lower = self._sentence_lower_body()
        if lower:
            sentences.append(lower)
        
        # Содержимое органов (если существенно)
        contents = self._sentence_organ_contents()
        if contents:
            sentences.append(contents)
        
        # Особые состояния
        special = self._sentence_special_states()
        if special:
            sentences.append(special)
            
        return " ".join(sentences)
    
    def _generate_detailed(self) -> str:
        """Подробное с деталями наполнения"""
        text = self._generate_standard()
        
        details = []
        # Детали по каждому органу
        if self.body.uterus_system and self.body.uterus_system.primary:
            u = self.body.uterus_system.primary
            if u.filled > 0 or u.inserted_objects:
                details.append(f"Матка: {self.parser._get_womb_contents()}")
        
        if self.body.breast_grid:
            for i, b in enumerate(self.body.breast_grid.all(), 1):
                if b.filled > 0:
                    details.append(f"Грудь {i}: {b.filled:.0f}мл, состояние: {b.state.name if b.state else 'норма'}")
        
        if self.body.stomach_system and self.body.stomach_system.primary:
            s = self.body.stomach_system.primary
            if s.filled > 0:
                details.append(f"Желудок: {self.parser._get_stomach_contents()}")
        
        if details:
            text += " " + " ".join(details)
        
        return text
    
    def _generate_clinical(self) -> str:
        lines = [
            f"Рост: {self.body.height:.1f} см | Раса: {self._get_race_name().upper()}",
            "─" * 40
        ]
        
        # Грудь
        if self.body.breast_grid:
            lines.append("【ГРУДНЫЕ ЖЕЛЕЗЫ】")
            for i, b in enumerate(self.body.breast_grid.all(), 1):
                cup = b.cup.name
                fill_pct = (b.filled / b.volume * 100) if b.volume > 0 else 0
                objs = []
                if hasattr(b, 'insertion_manager') and b.insertion_manager:
                    objs = [getattr(o, 'name', 'obj') for o in getattr(b.insertion_manager, 'inserted_objects', [])]
                obj_str = f" | Объекты: {', '.join(objs)}" if objs else ""
                lines.append(f"  #{i}: {cup} | {b.filled:.0f}/{b.volume:.0f}мл ({fill_pct:.0f}%) | {b.state.name}{obj_str}")
        
        # Матка
        if self.body.uterus_system and self.body.uterus_system.primary:
            u = self.body.uterus_system.primary
            lines.append("【МАТКА】")
            lines.append(f"  Статус: {u.inflation_status.value}")
            lines.append(f"  Заполнение: {u.filled:.0f}/{u.current_volume:.0f}мл ({u.fill_ratio:.0%})")
            if u.inserted_objects:
                lines.append(f"  Ретенция: {[getattr(o, 'name', 'obj') for o in u.inserted_objects]}")
        
        # Влагалище
        if self.body.vaginas:
            v = self.body.vaginas[0]
            lines.append("【ВЛАГАЛИЩЕ】")
            contents = self.parser._get_vagina_contents()
            lines.append(f"  Содержимое: {contents}")
        
        # Анус
        if self.body.anuses:
            a = self.body.anuses[0]
            lines.append("【АНУС】")
            obj = getattr(a, 'get_current_object', lambda: None)()
            if obj:
                lines.append(f"  Пенетрация: {getattr(obj, 'name', 'object')} ({getattr(obj, 'diameter', 0):.1f}см)")
            if getattr(a, 'fluid_content', 0) > 0:
                lines.append(f"  Ректальное содержимое: {a.fluid_content:.0f}мл")
        
        # Желудок
        if self.body.stomach_system and self.body.stomach_system.primary:
            s = self.body.stomach_system.primary
            if s.filled > 0 or getattr(s, 'inserted_object', None):
                lines.append("【ЖЕЛУДОК】")
                lines.append
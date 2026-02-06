# body_sim/characters/breast_reactions.py
"""
Реакции персонажей на состояние груди.
Поддерживает разные типы персонажей (Roxy, Misaka, и т.д.)
"""

from typing import Dict, List, Callable, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum, auto
import random

if TYPE_CHECKING:
    from body_sim.anatomy.breast import Breast
    from body_sim.body.body import Body
    from body_sim.characters.roxy_migurdia import RoxyMigurdia


class BreastEventType(Enum):
    """Типы событий груди для реакций."""
    START_LEAKING = auto()          # Начало утечки
    STOP_LEAKING = auto()           # Остановка утечки
    OVERPRESSURED = auto()          # Критическое давление
    ENGORGED = auto()               # Переполнение молоком
    CUP_INCREASE = auto()           # Увеличение размера
    CUP_DECREASE = auto()           # Уменьшение размера
    HIGH_SAG = auto()               # Сильное провисание
    INSERTION_START = auto()        # Начало вставки предмета
    INSERTION_DEEP = auto()         # Глубокая вставка
    LACTATION_START = auto()        # Начало лактации
    LACTATION_PEAK = auto()         # Пик лактации
    NIPPLE_STRETCH = auto()         # Растяжение соска
    NIPPLE_GAPING = auto()          # Раскрытие соска
    INFLATION_MAX = auto()          # Максимальное растяжение


@dataclass
class BreastReaction:
    """Реакция на событие груди."""
    text: str
    intensity: float = 1.0          # 0.0-1.0, влияет на силу реакции
    emotion: str = "neutral"        # neutral, pleasure, pain, embarrassment, panic
    sound_effect: Optional[str] = None  # Описание звука
    physical_effect: Optional[str] = None  # Физический эффект


class CharacterReactionProfile:
    """Профиль реакций персонажа."""
    
    def __init__(self, name: str, personality_traits: List[str]):
        self.name = name
        self.personality_traits = personality_traits
        self.reactions: Dict[BreastEventType, List[BreastReaction]] = {}
        self._setup_default_reactions()
    
    def _setup_default_reactions(self):
        """Базовые реакции (можно переопределить)."""
        self.reactions = {
            BreastEventType.START_LEAKING: [
                BreastReaction("Чувствую, как что-то вытекает...", 0.4, "embarrassment", "*писк*"),
                BreastReaction("О нет, промокает...", 0.5, "embarrassment", "*вздох*"),
            ],
            BreastEventType.OVERPRESSURED: [
                BreastReaction("Слишком туго! Больно!", 0.8, "pain", "*стон*"),
                BreastReaction("Кажется, лопну!", 0.9, "panic", "*вскрик*"),
            ],
            BreastEventType.ENGORGED: [
                BreastReaction("Так тяжело... Нужно сцедить", 0.6, "discomfort"),
                BreastReaction("Грудь готова взорваться", 0.7, "pain"),
            ],
            BreastEventType.CUP_INCREASE: [
                BreastReaction("Ого, стало теснее...", 0.5, "surprise"),
                BreastReaction("Вырастает?!", 0.6, "shock"),
            ],
            BreastEventType.HIGH_SAG: [
                BreastReaction("Так низко свисает...", 0.5, "embarrassment"),
                BreastReaction("Вес тянет вниз", 0.4, "discomfort"),
            ],
        }
    
    def get_reaction(self, event: BreastEventType, intensity: float = 1.0) -> Optional[BreastReaction]:
        """Получить подходящую реакцию."""
        if event not in self.reactions:
            return None
        
        # Фильтруем по интенсивности
        suitable = [r for r in self.reactions[event] 
                   if abs(r.intensity - intensity) < 0.3]
        
        if not suitable:
            suitable = self.reactions[event]
        
        return random.choice(suitable) if suitable else None
    
    def add_reaction(self, event: BreastEventType, reaction: BreastReaction):
        """Добавить реакцию."""
        if event not in self.reactions:
            self.reactions[event] = []
        self.reactions[event].append(reaction)


class RoxyBreastProfile(CharacterReactionProfile):
    """Профиль реакций Рокси Мигурдии (мигурдийская чувствительность)."""
    
    def __init__(self):
        super().__init__("Roxy", ["tsundere", "prideful", "sensitive", "insecure_about_breasts"])
        self._setup_roxy_reactions()
    
    def _setup_roxy_reactions(self):
        """Специфичные реакции Рокси с учётом расовой чувствительности."""
        
        # Утечка - особенно стыдно для гордой магии
        self.reactions[BreastEventType.START_LEAKING] = [
            BreastReaction(
                "\"Н-не смотри! Это... это нормально!\" *краснеет*",
                0.6, "embarrassment", "*писк*", "сильное покраснение"
            ),
            BreastReaction(
                "\"Просто... просто жарко, вот и всё!\" *отводит глаза*",
                0.5, "tsundere", "*кашель*", "потные ладони"
            ),
            BreastReaction(
                "*покрывается мурашками от мигурдийской чувствительности*",
                0.7, "pleasure", "*тихий стон*", "дрожь"
            ),
        ]
        
        # Переполнение - болезненно (мигурдийцы чувствительны к боли)
        self.reactions[BreastEventType.OVERPRESSURED] = [
            BreastReaction(
                "\"Ай! Больно! Почему так чувствительно?!\"",
                0.9, "pain", "*вскрик боли*", "слёзы на глазах"
            ),
            BreastReaction(
                "\"Я мигурдийка, я должна терпеть... но нет сил!\"",
                0.85, "pain", "*стон*", "сжимает кулаки"
            ),
            BreastReaction(
                "\"Как будто кожа натягивается слишком сильно...\"",
                0.8, "pain", "*хриплый вдох*", "бледность"
            ),
        ]
        
        # Переполнение молоком
        self.reactions[BreastEventType.ENGORGED] = [
            BreastReaction(
                "\"Так тяжело... и это при моём-то размере...\" *смотрит вниз с тоской*",
                0.7, "embarrassment", "*вздох*", "опускает плечи"
            ),
            BreastReaction(
                "\"Если бы грудь была побольше, может, не так бы тянуло...\"",
                0.6, "insecurity", "*недовольный звук*", "обнимает себя"
            ),
        ]
        
        # Увеличение размера - комплексы
        self.reactions[BreastEventType.CUP_INCREASE] = [
            BreastReaction(
                "\"Ч-что?! Она растёт?! Наконец-то...\" *потом краснеет* \"Я не это имела в виду!\"",
                0.6, "tsundere", "*вздох облегчения*", "трогает грудь осторожно"
            ),
            BreastReaction(
                "\"Н-не зазнавайся! Это просто отёк!\"",
                0.5, "tsundere", "*откашливается*", "отводит руки"
            ),
        ]
        
        # Уменьшение - разочарование
        self.reactions[BreastEventType.CUP_DECREASE] = [
            BreastReaction(
                "\"И снова AA... как всегда...\" *грустно опускает взгляд*",
                0.5, "sadness", "*вздох*", "плечи опущены"
            ),
            BreastReaction(
                "\"Н-ничего страшного! Маленькая грудь тоже хороша!\" *фальшивая улыбка*",
                0.4, "denial", "*нервный смешок*", "сжимает кулаки"
            ),
        ]
        
        # Провисание - для маленькой груди особенно заметно
        self.reactions[BreastEventType.HIGH_SAG] = [
            BreastReaction(
                "\"Она... она свисает?! Но она же маленькая!\" *паника*",
                0.7, "panic", "*вскрик*", "хватается за грудь"
            ),
            BreastReaction(
                "\"Мигурдийская кожа такая нежная... всё тянет вниз...\"",
                0.6, "discomfort", "*стон*", "поддерживает грудь руками"
            ),
        ]
        
        # Вставка предмета - болезненно из-за чувствительности
        self.reactions[BreastEventType.INSERTION_START] = [
            BreastReaction(
                "\"Т-ты уверен? Там так тесно...\" *дрожит*",
                0.6, "anxiety", "*тихий стон*", "напряжение мышц"
            ),
            BreastReaction(
                "\"Ах! Чувствую каждый миллиметр... мигурдийская кожа...\"",
                0.7, "pleasure_pain", "*вздох*", "мурашки по коже"
            ),
        ]
        
        self.reactions[BreastEventType.INSERTION_DEEP] = [
            BreastReaction(
                "\"Глубоко! Слишком глубоко! Остановись!\" *слёзы*",
                0.9, "pain", "*крик*", "сильное напряжение"
            ),
            BreastReaction(
                "\"Чувствую... как давит изнутри...\" *тяжёлое дыхание*",
                0.8, "overwhelm", "*стон*", "покраснение всего тела"
            ),
        ]
        
        # Лактация
        self.reactions[BreastEventType.LACTATION_START] = [
            BreastReaction(
                "\"Лактация? Но я... я ещё не готова быть матерью...\"",
                0.6, "confusion", "*нервный смешок*", "трогает грудь"
            ),
            BreastReaction(
                "\"Так странно... тепло распространяется...\"",
                0.5, "wonder", "*тихий вздох*", "мягкое выражение лица"
            ),
        ]
        
        # Растяжение соска
        self.reactions[BreastEventType.NIPPLE_STRETCH] = [
            BreastReaction(
                "\"Сосок... он растягивается?!\" *широко раскрытые глаза*",
                0.7, "shock", "*вскрик*", "замирает от удивления"
            ),
            BreastReaction(
                "\"Так чувствительно... каждое прикосновение...\"",
                0.8, "pleasure", "*тихий стон*", "дрожь"
            ),
        ]
        
        # Раскрытие соска
        self.reactions[BreastEventType.NIPPLE_GAPING] = [
            BreastReaction(
                "\"Он открылся?! Видно изнутри?! Н-не смотри!\" *паника*",
                0.9, "panic_embarrassment", "*вскрик*", "закрывает грудь руками"
            ),
            BreastReaction(
                "\"Как будто что-то пустое... странное ощущение...\"",
                0.6, "weird", "*недоумение*", "осторожно трогает"
            ),
        ]
        
        # Максимальное растяжение
        self.reactions[BreastEventType.INFLATION_MAX] = [
            BreastReaction(
                "\"Больше нельзя! Лопнет! Я чувствую!\" *истерика*",
                1.0, "panic", "*крик*", "дрожь всего тела"
            ),
            BreastReaction(
                "\"Мигурдийская кожа... она такая тонкая... остановись!\"",
                0.95, "fear", "*плач*", "синюшность кожи"
            ),
        ]


class MisakaBreastProfile(CharacterReactionProfile):
    """Профиль реакций Мисаки Микото (гордая, электрические способности)."""
    
    def __init__(self):
        super().__init__("Misaka", ["tsundere", "prideful", "electromaster", "insecure_about_breasts"])
        self._setup_misaka_reactions()
    
    def _setup_misaka_reactions(self):
        """Реакции Мисаки."""
        
        self.reactions[BreastEventType.START_LEAKING] = [
            BreastReaction(
                "\"К-какого?! Почему оно течёт?!\" *искры из волос*",
                0.6, "embarrassment", "*треск электричества*", "электростатика"
            ),
            BreastReaction(
                "\"Не смотри, идиот! Или я ударю током!\"",
                0.5, "tsundere", "*щелчок разряда*", "искры в глазах"
            ),
        ]
        
        self.reactions[BreastEventType.OVERPRESSURED] = [
            BreastReaction(
                "\"Бип-боп! Критическое давление! Шутка... ой, больно!\"",
                0.7, "pain", "*искры*", "сжимает грудь"
            ),
            BreastReaction(
                "\"Электромагнитный щит не помогает от этого!\"",
                0.8, "pain", "*стон*", "напряжение"
            ),
        ]
        
        self.reactions[BreastEventType.CUP_INCREASE] = [
            BreastReaction(
                "\"Растёт?! Наконец-то! ...Я не говорила этого вслух!\"",
                0.6, "tsundere", "*откашливается*", "краснеет"
            ),
        ]
        
        self.reactions[BreastEventType.CUP_DECREASE] = [
            BreastReaction(
                "\"И снова плоская... как железнодорожная рельса...\"",
                0.5, "sadness", "*вздох*", "опускает плечи"
            ),
        ]


# ============ СИСТЕМА РЕАКЦИЙ ============

class BreastReactionSystem:
    """Система отслеживания и реакции на события груди."""
    
    def __init__(self):
        self.profiles: Dict[str, CharacterReactionProfile] = {}
        self._last_states: Dict[str, Dict] = {}  # Для отслеживания изменений
        self._setup_default_profiles()
    
    def _setup_default_profiles(self):
        """Инициализация стандартных профилей."""
        self.register_profile("roxy", RoxyBreastProfile())
        self.register_profile("misaka", MisakaBreastProfile())
        self.register_profile("default", CharacterReactionProfile("Default", []))
    
    def register_profile(self, name: str, profile: CharacterReactionProfile):
        """Зарегистрировать профиль."""
        self.profiles[name.lower()] = profile
    
    def get_profile(self, name: str) -> CharacterReactionProfile:
        """Получить профиль."""
        return self.profiles.get(name.lower(), self.profiles["default"])
    
    def detect_events(self, breast: 'Breast', body_id: int, breast_id: str) -> List[BreastEventType]:
        """Определить произошедшие события."""
        events = []
        
        # Безопасно получаем текущее состояние
        try:
            current_state = breast.state.name if hasattr(breast, 'state') and breast.state else 'UNKNOWN'
        except:
            current_state = 'UNKNOWN'
        
        try:
            current_cup = breast.dynamic_cup.name if hasattr(breast, 'dynamic_cup') and breast.dynamic_cup else 'UNKNOWN'
        except:
            current_cup = 'UNKNOWN'
        
        try:
            current_filled = float(breast.filled) if hasattr(breast, 'filled') else 0.0
        except:
            current_filled = 0.0
        
        try:
            current_sag = float(breast.sag) if hasattr(breast, 'sag') else 0.0
        except:
            current_sag = 0.0
        
        # Давление - безопасно
        current_pressure = 0.0
        if hasattr(breast, 'pressure'):
            try:
                from body_sim.core.fluids import FLUID_DEFS
                current_pressure = breast.pressure(FLUID_DEFS)
            except:
                current_pressure = 0.0
        
        state_data = {
            'state': current_state,
            'cup': current_cup,
            'filled': current_filled,
            'sag': current_sag,
            'pressure': current_pressure,
        }
        
        key = f"{body_id}_{breast_id}"
        last = self._last_states.get(key, {})
        
        # Утечка
        if current_state == 'LEAKING' and last.get('state') != 'LEAKING':
            events.append(BreastEventType.START_LEAKING)
        elif current_state != 'LEAKING' and last.get('state') == 'LEAKING':
            events.append(BreastEventType.STOP_LEAKING)
        
        # Переполнение
        if current_state == 'OVERPRESSURED' and last.get('state') != 'OVERPRESSURED':
            events.append(BreastEventType.OVERPRESSURED)
        
        # Изменение размера
        last_cup = last.get('cup')
        if last_cup and last_cup != 'UNKNOWN' and current_cup != 'UNKNOWN' and last_cup != current_cup:
            try:
                from body_sim.core.enums import CupSize
                old_val = getattr(CupSize, last_cup, CupSize.AA).value
                new_val = getattr(CupSize, current_cup, CupSize.AA).value
                if new_val > old_val:
                    events.append(BreastEventType.CUP_INCREASE)
                else:
                    events.append(BreastEventType.CUP_DECREASE)
            except Exception:
                pass  # Игнорируем ошибки сравнения
        
        # Провисание
        if current_sag > 0.7 and last.get('sag', 0) <= 0.7:
            events.append(BreastEventType.HIGH_SAG)
        
        # Лактация
        if hasattr(breast, 'lactation') and breast.lactation:
            try:
                lact_state = breast.lactation.state.name if hasattr(breast.lactation.state, 'name') else str(breast.lactation.state)
                if lact_state == 'ACTIVE' and last.get('lactation') != 'ACTIVE':
                    events.append(BreastEventType.LACTATION_START)
            except:
                pass
        
        # Сохраняем состояние
        state_data['lactation'] = None
        if hasattr(breast, 'lactation') and breast.lactation:
            try:
                state_data['lactation'] = breast.lactation.state.name if hasattr(breast.lactation.state, 'name') else str(breast.lactation.state)
            except:
                pass
        
        self._last_states[key] = state_data
        
        return events
    
    def process_reactions(self, body: 'Body', profile_name: str = "default") -> List[BreastReaction]:
        """Обработать реакции для тела."""
        if not hasattr(body, 'has_breasts') or not body.has_breasts:
            return []
        
        if not hasattr(body, 'breast_grid') or not body.breast_grid:
            return []
        
        profile = self.get_profile(profile_name)
        reactions = []
        body_id = id(body)
        
        try:
            rows = body.breast_grid.rows if hasattr(body.breast_grid, 'rows') else []
        except:
            return []
        
        for r_idx, row in enumerate(rows):
            if not row:
                continue
            for c_idx, breast in enumerate(row):
                if breast is None:
                    continue
                breast_id = f"{r_idx}_{c_idx}"
                try:
                    events = self.detect_events(breast, body_id, breast_id)
                    for event in events:
                        reaction = profile.get_reaction(event)
                        if reaction:
                            reactions.append(reaction)
                except Exception as e:
                    # Логируем ошибку но не прерываем работу
                    print(f"[DEBUG] Error processing breast {breast_id}: {e}")
                    continue
        
        return reactions
    
    def clear_state(self, body_id: Optional[int] = None):
        """Очистить сохранённые состояния."""
        if body_id is None:
            self._last_states.clear()
        else:
            keys_to_remove = [k for k in self._last_states.keys() if k.startswith(f"{body_id}_")]
            for key in keys_to_remove:
                del self._last_states[key]


# ============ ИНТЕГРАЦИЯ С КОНСОЛЬЮ ============

def register_reaction_commands(registry, reaction_system: 'BreastReactionSystem'):
    """Зарегистрировать команды реакций."""
    from body_sim.ui.commands import Command, console
    
    def cmd_reactions(args, ctx):
        """Показать реакции на текущее состояние груди."""
        if not ctx.active_body:
            console.print("[red]No active body![/red]")
            return
        
        if not hasattr(ctx.active_body, 'has_breasts') or not ctx.active_body.has_breasts:
            console.print("[red]No breasts to react to![/red]")
            return
        
        # Определяем профиль
        profile_name = "default"
        body_type = type(ctx.active_body).__name__.lower()
        
        if "roxy" in body_type or "migurdia" in body_type:
            profile_name = "roxy"
        elif "misaka" in body_type:
            profile_name = "misaka"
        
        try:
            # Получаем реакции
            reactions = reaction_system.process_reactions(ctx.active_body, profile_name)
            
            if not reactions:
                console.print("[dim]No new reactions...[/dim]")
                # Показываем текущее состояние для отладки
                if args and args[0] == 'debug':
                    console.print(f"[dim]Body type: {body_type}[/dim]")
                    console.print(f"[dim]Profile: {profile_name}[/dim]")
                    console.print(f"[dim]Breasts: {len(ctx.active_body.breast_grid.all()) if hasattr(ctx.active_body.breast_grid, 'all') else 'N/A'}[/dim]")
                return
            
            # Выводим
            for reaction in reactions:
                color_map = {
                    "neutral": "white",
                    "pleasure": "magenta",
                    "pain": "red",
                    "embarrassment": "yellow",
                    "panic": "bright_red",
                    "tsundere": "bright_cyan",
                    "discomfort": "yellow",
                    "surprise": "cyan",
                    "shock": "bright_cyan",
                    "sadness": "blue",
                    "denial": "dim",
                    "anxiety": "yellow",
                    "confusion": "yellow",
                    "wonder": "green",
                }
                color = color_map.get(reaction.emotion, "white")
                
                console.print(f"\n[{color}]{reaction.text}[/{color}]")
                if reaction.sound_effect:
                    console.print(f"[dim italic]{reaction.sound_effect}[/dim italic]")
                if reaction.physical_effect:
                    console.print(f"[dim]*{reaction.physical_effect}*[/dim]")
                    
        except Exception as e:
            console.print(f"[red]Error processing reactions: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    def cmd_reaction_test(args, ctx):
        """Тестировать конкретную реакцию."""
        if not args:
            # Показать доступные события
            console.print("[cyan]Available events:[/cyan]")
            for event in BreastEventType:
                console.print(f"  {event.name}")
            console.print("\n[yellow]Profiles: roxy, misaka, default[/yellow]")
            return
        
        event_name = args[0].upper()
        try:
            event = BreastEventType[event_name]
        except KeyError:
            console.print(f"[red]Unknown event: {event_name}[/red]")
            return
        
        profile_name = args[1].lower() if len(args) > 1 else "roxy"
        profile = reaction_system.get_profile(profile_name)
        
        reaction = profile.get_reaction(event)
        if reaction:
            console.print(f"[bold]Testing {event.name} for {profile_name}:[/bold]")
            console.print(f"Text: {reaction.text}")
            console.print(f"Emotion: {reaction.emotion}")
            console.print(f"Intensity: {reaction.intensity}")
            if reaction.sound_effect:
                console.print(f"Sound: {reaction.sound_effect}")
            if reaction.physical_effect:
                console.print(f"Physical: {reaction.physical_effect}")
        else:
            console.print("[dim]No reaction defined for this event[/dim]")
    
    def cmd_reaction_clear(args, ctx):
        """Очистить сохранённые состояния (для тестирования)."""
        if ctx.active_body:
            reaction_system.clear_state(id(ctx.active_body))
            console.print("[green]Cleared reaction state for current body[/green]")
        else:
            reaction_system.clear_state()
            console.print("[green]Cleared all reaction states[/green]")
    
    registry.register(Command(
        "reactions", ["react"],
        "Show breast reactions",
        "reactions [debug]",
        cmd_reactions,
        "breasts"
    ))
    
    registry.register(Command(
        "reaction_test", ["rtest"],
        "Test specific reaction",
        "reaction_test <event> [profile]",
        cmd_reaction_test,
        "debug"
    ))
    
    registry.register(Command(
        "reaction_clear", ["rclear"],
        "Clear reaction states",
        "reaction_clear",
        cmd_reaction_clear,
        "debug"
    ))


# Глобальный экземпляр системы
_reaction_system: Optional[BreastReactionSystem] = None

def get_reaction_system() -> BreastReactionSystem:
    """Получить глобальный экземпляр системы реакций."""
    global _reaction_system
    if _reaction_system is None:
        _reaction_system = BreastReactionSystem()
    return _reaction_system
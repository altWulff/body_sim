# body_sim/characters/uterus_reactions.py
"""
Реакции персонажей на состояние репродуктивной системы.
Поддерживает разные типы персонажей (Roxy, Misaka, и т.д.)
"""

from typing import Dict, List, Callable, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum, auto
import random

if TYPE_CHECKING:
    from body_sim.anatomy.uterus import Uterus, Ovary, FallopianTube
    from body_sim.body.body import Body


class UterusEventType(Enum):
    """Типы событий матки для реакций."""
    # Инфляция
    INFLATION_START = auto()           # Начало инфляции
    INFLATION_STRETCHED = auto()       # Растянута (1.5x)
    INFLATION_DISTENDED = auto()       # Выпучена (2.0x)
    INFLATION_HYPER = auto()           # Гипер-инфляция (2.5x)
    INFLATION_RISK = auto()            # Риск разрыва (3.0x+)
    INFLATION_ULTRA = auto()           # Ультра-растяжение (10x+)
    INFLATION_MEGA = auto()            # Мега-растяжение (50x+)
    INFLATION_GIGA = auto()            # Гига-растяжение (100x+)
    INFLATION_TERA = auto()            # Тера-растяжение (250x+)
    INFLATION_MAX = auto()             # Предельное растяжение (500x)

    # Состояния матки
    UTERUS_EMPTY = auto()              # Пустая матка
    UTERUS_NORMAL = auto()             # Нормальное состояние
    UTERUS_TENSE = auto()              # Напряжённая
    UTERUS_OVERPRESSURED = auto()      # Переполненная
    UTERUS_LEAKING = auto()            # Утечка через шейку

    # Пролапс
    PROLAPSE_DESCENDED = auto()        # Опущение матки
    PROLAPSE_PARTIAL = auto()          # Частичный пролапс
    PROLAPSE_COMPLETE = auto()         # Полный пролапс
    PROLAPSE_EVERSIO = auto()          # Выворот матки

    # Яичники
    OVARY_ENLARGED = auto()            # Увеличение яичника
    OVARY_PROLAPSED = auto()           # Пролапс яичника
    OVARY_EVERTED = auto()             # Выворот яичника
    OVARY_TORSION = auto()             # Перекрут яичника
    OVARY_INFLATED = auto()            # Инфляция яичника

    # Трубы
    TUBE_STRETCHED = auto()            # Растяжение трубы
    TUBE_DILATED = auto()              # Расширение трубы
    TUBE_BLOCKED = auto()              # Закупорка трубы
    TUBE_PROLAPSED = auto()            # Пролапс трубы
    TUBE_EVERTED = auto()              # Выворот трубы с яичником

    # Жидкость
    FLUID_ADDED = auto()               # Добавление жидкости
    FLUID_OVERFLOW = auto()            # Переполнение
    FLUID_BACKFLOW = auto()            # Обратный поток

    # Предметы
    OBJECT_INSERTED = auto()           # Вставка предмета
    OBJECT_DEEP = auto()               # Глубокая вставка
    OBJECT_REMOVED = auto()            # Извлечение предмета


@dataclass
class UterusReaction:
    """Реакция на событие матки."""
    text: str
    intensity: float = 1.0          # 0.0-1.0, влияет на силу реакции
    emotion: str = "neutral"        # neutral, pleasure, pain, embarrassment, panic, etc.
    sound_effect: Optional[str] = None
    physical_effect: Optional[str] = None


class CharacterUterusProfile:
    """Профиль реакций персонажа на состояние матки."""

    def __init__(self, name: str, personality_traits: List[str]):
        self.name = name
        self.personality_traits = personality_traits
        self.reactions: Dict[UterusEventType, List[UterusReaction]] = {}
        self._setup_default_reactions()

    def _setup_default_reactions(self):
        """Базовые реакции."""
        self.reactions = {
            UterusEventType.UTERUS_NORMAL: [
                UterusReaction("Всё в порядке...", 0.1, "neutral"),
            ],
            UterusEventType.UTERUS_TENSE: [
                UterusReaction("Немного тянет внизу живота", 0.3, "discomfort"),
            ],
            UterusEventType.UTERUS_OVERPRESSURED: [
                UterusReaction("Слишком полно! Больно!", 0.8, "pain", "*стон*"),
            ],
            UterusEventType.UTERUS_LEAKING: [
                UterusReaction("Что-то вытекает...", 0.5, "embarrassment", "*вздох*"),
            ],
            UterusEventType.PROLAPSE_DESCENDED: [
                UterusReaction("Чувствую тяжесть...", 0.4, "discomfort"),
            ],
            UterusEventType.PROLAPSE_COMPLETE: [
                UterusReaction("Что-то выходит наружу! Помогите!", 0.9, "panic", "*крик*"),
            ],
            UterusEventType.OVARY_EVERTED: [
                UterusReaction("Внутренности... снаружи...", 0.95, "shock", "*вскрик*"),
            ],
        }

    def get_reaction(self, event: UterusEventType, intensity: float = 1.0) -> Optional[UterusReaction]:
        """Получить подходящую реакцию."""
        if event not in self.reactions:
            return None

        suitable = [r for r in self.reactions[event] 
                   if abs(r.intensity - intensity) < 0.3]

        if not suitable:
            suitable = self.reactions[event]

        return random.choice(suitable) if suitable else None

    def add_reaction(self, event: UterusEventType, reaction: UterusReaction):
        """Добавить реакцию."""
        if event not in self.reactions:
            self.reactions[event] = []
        self.reactions[event].append(reaction)


class RoxyUterusProfile(CharacterUterusProfile):
    """Профиль реакций Рокси Мигурдии на состояние матки."""

    def __init__(self):
        super().__init__("Roxy", ["tsundere", "prideful", "sensitive", "inexperienced"])
        self._setup_roxy_reactions()

    def _setup_roxy_reactions(self):
        """Специфичные реакции Рокси."""

        # Инфляция - начальная стадия
        self.reactions[UterusEventType.INFLATION_START] = [
            UterusReaction(
                "\"Н-не так сильно... там чувствительно...\" *краснеет*",
                0.4, "embarrassment", "*тихий стон*", "покраснение шеи"
            ),
        ]

        self.reactions[UterusEventType.INFLATION_STRETCHED] = [
            UterusReaction(
                "\"Растягивается... странное ощущение...\" *сжимает живот*",
                0.5, "weird", "*вздох*", "напряжение мышц"
            ),
            UterusReaction(
                "\"Мигурдийская кожа такая нежная... кажется, натягивается...\"",
                0.6, "pleasure_pain", "*тихий стон*", "мурашки по коже"
            ),
        ]

        self.reactions[UterusEventType.INFLATION_DISTENDED] = [
            UterusReaction(
                "\"Видно?! Снаружи видно?!\" *паника* 'Я выгляжу беременной!\'\"Видно?! Снаружи видно?!\" *паника* 'Я выгляжу беременной!\'",
                0.7, "panic_embarrassment", "*вскрик*", "сильное покраснение"
            ),
            UterusReaction(
                "\'Так полно... как будто что-то огромное внутри...\'",
                0.6, "overwhelm", "*тяжёлое дыхание*", "выпячивается живот"
            ),
        ]

        self.reactions[UterusEventType.INFLATION_HYPER] = [
            UterusReaction(
                "\'Больше нельзя! Кожа натягивается слишком сильно!\'",
                0.8, "pain", "*стон боли*", "бледность кожи"
            ),
            UterusReaction(
                "\"Чувствую каждую стенку... так тонко...\" *слёзы*",
                0.85, "fear", "*тихий плач*", "дрожь"
            ),
        ]

        self.reactions[UterusEventType.INFLATION_RISK] = [
            UterusReaction(
                "\"Лопнет! Я серьёзно! Мигурдийская кожа не резиновая!\"",
                0.9, "panic", "*крик*", "истерика"
            ),
            UterusReaction(
                "\"П-пожалуйста... остановись... я боюсь...\" *трясётся*",
                0.85, "fear", "*плач*", "синюшность губ"
            ),
        ]

        # Ультра+ растяжения
        self.reactions[UterusEventType.INFLATION_ULTRA] = [
            UterusReaction(
                "\"Это... это невозможно... как я ещё цела...\" *шок*",
                0.9, "shock", "*дрожащий голос*", "потеря ориентации"
            ),
        ]

        self.reactions[UterusEventType.INFLATION_MEGA] = [
            UterusReaction(
                "\"Я... я как воздушный шар... но внутри...\"",
                0.95, "dissociation", "*слабый голос*", "обморочное состояние"
            ),
        ]

        self.reactions[UterusEventType.INFLATION_GIGA] = [
            UterusReaction(
                "\"Не чувствую... ничего не чувствую... только растяжение...\"",
                1.0, "dissociation", "*едва слышно*", "шоковое состояние"
            ),
        ]

        self.reactions[UterusEventType.INFLATION_MAX] = [
            UterusReaction(
                "\"Предел... 500 раз... я... я...\" *потеря сознания*",
                1.0, "unconscious", "*стон*", "обморок"
            ),
        ]

        # Пролапс
        self.reactions[UterusEventType.PROLAPSE_DESCENDED] = [
            UterusReaction(
                "\"Что-то... опускается... тяжесть...\" *бледнеет*",
                0.5, "fear", "*вздох*", "холодный пот"
            ),
        ]

        self.reactions[UterusEventType.PROLAPSE_PARTIAL] = [
            UterusReaction(
                "\"Нет-нет-нет! Что-то выходит! Внутри всё пусто!\"",
                0.8, "panic", "*крик*", "сильное кровотечение"
            ),
        ]

        self.reactions[UterusEventType.PROLAPSE_COMPLETE] = [
            UterusReaction(
                "\'МАТКА! МАТКА НАРУЖУ!\' *истерика* 'Врача!\'",
                0.95, "panic", "*истерический крик*", "шоковое состояние"
            ),
        ]

        self.reactions[UterusEventType.PROLAPSE_EVERSIO] = [
            UterusReaction(
                "\"Всё вывернуто... всё наружу... видно всё...\" *обморок*",
                1.0, "shock", "*хрип*", "потеря сознания"
            ),
        ]

        # Яичники
        self.reactions[UterusEventType.OVARY_ENLARGED] = [
            UterusReaction(
                "\"Сбоку болит... как будто яичник увеличился...\"",
                0.5, "discomfort", "*стон*", "прижимает руку к боку"
            ),
        ]

        self.reactions[UterusEventType.OVARY_PROLAPSED] = [
            UterusReaction(
                "\"Что-то шевелится внутри... труба тянет...\"",
                0.7, "fear", "*вздох*", "спазмы"
            ),
        ]

        self.reactions[UterusEventType.OVARY_EVERTED] = [
            UterusReaction(
                "\"ЯИЧНИК! Он снаружи! Видишь?! Фолликулы!\" *паника*",
                0.9, "panic", "*вскрик*", "сильное кровотечение"
            ),
            UterusReaction(
                "\"Он свисает... на трубе... как вишня...\" *шок*",
                0.85, "shock", "*дрожащий голос*", "потеря чувствительности"
            ),
        ]

        self.reactions[UterusEventType.OVARY_TORSION] = [
            UterusReaction(
                "\"БОЛЬ! РЕЖУЩАЯ! НЕ МОГУ ДВИГАТЬСЯ!\"",
                1.0, "agony", "*крик агонии*", "синюшность тканей"
            ),
        ]

        # Трубы
        self.reactions[UterusEventType.TUBE_STRETCHED] = [
            UterusReaction(
                "\"Тянет сбоку... как ниточка... длинная...\"",
                0.4, "weird", "*вздох*", "необычное ощущение"
            ),
        ]

        self.reactions[UterusEventType.TUBE_DILATED] = [
            UterusReaction(
                "\"Внутри что-то широкое... труба раскрылась...\"",
                0.6, "weird", "*тихий стон*", "пульсация"
            ),
        ]

        self.reactions[UterusEventType.TUBE_EVERTED] = [
            UterusReaction(
                "\"Труба вывернулась! Яичник на конце! Видно всё!\"",
                0.9, "panic", "*крик*", "обильное кровотечение"
            ),
        ]

        # Жидкость
        self.reactions[UterusEventType.FLUID_OVERFLOW] = [
            UterusReaction(
                "\"Не влезает! Давит на всё внутри!\"",
                0.7, "pain", "*стон*", "напряжение пресса"
            ),
        ]

        self.reactions[UterusEventType.FLUID_BACKFLOW] = [
            UterusReaction(
                "\"Течёт обратно! Из яичников! Странное ощущение...\"",
                0.5, "weird", "*вздох*", "пульсация в боках"
            ),
        ]

        # Предметы
        self.reactions[UterusEventType.OBJECT_INSERTED] = [
            UterusReaction(
                "\"Т-туда?! В матку?!\" *краснеет до корней волос*",
                0.6, "embarrassment", "*писк*", "сильное сердцебиение"
            ),
            UterusReaction(
                "\"Чувствую... как заходит... шейка раскрывается...\"",
                0.7, "pleasure_pain", "*тихий стон*", "мурашки"
            ),
        ]

        self.reactions[UterusEventType.OBJECT_DEEP] = [
            UterusReaction(
                "\"Глубоко! В самой глубине! Чувствую кончик!\"",
                0.8, "overwhelm", "*тяжёлое дыхание*", "сокращения матки"
            ),
        ]


# ============ СИСТЕМА РЕАКЦИЙ ============

class UterusReactionSystem:
    """Система отслеживания и реакции на события матки."""

    def __init__(self):
        self.profiles: Dict[str, CharacterUterusProfile] = {}
        self._last_states: Dict[str, Dict] = {}
        self._setup_default_profiles()

    def _setup_default_profiles(self):
        """Инициализация стандартных профилей."""
        self.register_profile("roxy", RoxyUterusProfile())
        self.register_profile("default", CharacterUterusProfile("Default", []))

    def register_profile(self, name: str, profile: CharacterUterusProfile):
        """Зарегистрировать профиль."""
        self.profiles[name.lower()] = profile

    def get_profile(self, name: str) -> CharacterUterusProfile:
        """Получить профиль."""
        return self.profiles.get(name.lower(), self.profiles["default"])

    def _get_inflation_event(self, stretch: float) -> Optional[UterusEventType]:
        """Определить событие инфляции по растяжению."""
        if stretch >= 500.0:
            return UterusEventType.INFLATION_MAX
        elif stretch >= 250.0:
            return UterusEventType.INFLATION_TERA
        elif stretch >= 100.0:
            return UterusEventType.INFLATION_GIGA
        elif stretch >= 50.0:
            return UterusEventType.INFLATION_MEGA
        elif stretch >= 10.0:
            return UterusEventType.INFLATION_ULTRA
        elif stretch >= 3.5:
            return UterusEventType.INFLATION_RISK
        elif stretch >= 2.5:
            return UterusEventType.INFLATION_HYPER
        elif stretch >= 2.0:
            return UterusEventType.INFLATION_DISTENDED
        elif stretch >= 1.5:
            return UterusEventType.INFLATION_STRETCHED
        elif stretch > 1.2:
            return UterusEventType.INFLATION_START
        return None

    def _get_prolapse_event(self, descent: float, is_everted: bool) -> Optional[UterusEventType]:
        """Определить событие пролапса."""
        if is_everted:
            return UterusEventType.PROLAPSE_EVERSIO
        elif descent >= 0.7:
            return UterusEventType.PROLAPSE_COMPLETE
        elif descent >= 0.3:
            return UterusEventType.PROLAPSE_PARTIAL
        elif descent >= 0.1:
            return UterusEventType.PROLAPSE_DESCENDED
        return None

    def detect_events(self, uterus: 'Uterus', body_id: int, uterus_id: str = "0") -> List[UterusEventType]:
        """Определить произошедшие события."""
        events = []

        # Безопасно получаем состояние
        try:
            current_state = uterus.state.name if hasattr(uterus, 'state') and uterus.state else 'NORMAL'
        except:
            current_state = 'NORMAL'

        try:
            inflation_status = uterus.inflation_status.value if hasattr(uterus, 'inflation_status') else 'normal'
        except:
            inflation_status = 'normal'

        # Растяжение
        total_stretch = 1.0
        try:
            wall_stretch = getattr(uterus.walls, 'stretch_ratio', 1.0) if hasattr(uterus, 'walls') else 1.0
            inflation_ratio = getattr(uterus, 'inflation_ratio', 1.0)
            total_stretch = wall_stretch * inflation_ratio
        except:
            pass

        # Пролапс
        descent = getattr(uterus, 'descent_position', 0.0) or 0.0
        is_everted = getattr(uterus, 'is_everted', False) or False

        # Жидкость
        filled = getattr(uterus, 'uterus_filled', 0.0) or 0.0

        key = f"{body_id}_uterus_{uterus_id}"
        last = self._last_states.get(key, {})

        # Инфляция
        inflation_event = self._get_inflation_event(total_stretch)
        last_stretch = last.get('total_stretch', 1.0)

        if inflation_event and total_stretch > last_stretch * 1.1:  # Значительное увеличение
            # Проверяем, что это новый уровень
            last_event = self._get_inflation_event(last_stretch)
            if inflation_event != last_event:
                events.append(inflation_event)

        # Состояние матки
        if current_state != last.get('state'):
            state_map = {
                'EMPTY': UterusEventType.UTERUS_EMPTY,
                'NORMAL': UterusEventType.UTERUS_NORMAL,
                'TENSE': UterusEventType.UTERUS_TENSE,
                'OVERPRESSURED': UterusEventType.UTERUS_OVERPRESSURED,
                'LEAKING': UterusEventType.UTERUS_LEAKING,
            }
            if current_state in state_map:
                events.append(state_map[current_state])

        # Пролапс
        prolapse_event = self._get_prolapse_event(descent, is_everted)
        last_prolapse = self._get_prolapse_event(
            last.get('descent', 0.0), 
            last.get('is_everted', False)
        )
        if prolapse_event and prolapse_event != last_prolapse:
            events.append(prolapse_event)

        # Яичники
        for ovary in getattr(uterus, 'ovaries', []):
            if not ovary:
                continue
            # Проверяем состояние яичника
            try:
                ovary_state = ovary.state.name if hasattr(ovary, 'state') and ovary.state else 'NORMAL'
                last_ovary_state = last.get(f'ovary_{id(ovary)}', 'NORMAL')

                if ovary_state != last_ovary_state:
                    if ovary_state == 'EVERTED':
                        events.append(UterusEventType.OVARY_EVERTED)
                    elif ovary_state == 'PROLAPSED':
                        events.append(UterusEventType.OVARY_PROLAPSED)
                    elif ovary_state == 'TORSION':
                        events.append(UterusEventType.OVARY_TORSION)
            except:
                pass

        # Трубы
        for tube in getattr(uterus, 'tubes', []):
            if not tube:
                continue
            try:
                tube_stretch = getattr(tube, 'current_stretch', 1.0)
                last_tube_stretch = last.get(f'tube_{id(tube)}', 1.0)

                if tube_stretch >= 2.0 and last_tube_stretch < 2.0:
                    events.append(UterusEventType.TUBE_STRETCHED)

                if getattr(tube, 'is_everted', False) and not last.get(f'tube_everted_{id(tube)}', False):
                    events.append(UterusEventType.TUBE_EVERTED)
            except:
                pass

        # Сохраняем текущее состояние
        self._last_states[key] = {
            'state': current_state,
            'inflation_status': inflation_status,
            'total_stretch': total_stretch,
            'descent': descent,
            'is_everted': is_everted,
            'filled': filled,
        }

        # Сохраняем состояния яичников
        for ovary in getattr(uterus, 'ovaries', []):
            if ovary:
                try:
                    self._last_states[key][f'ovary_{id(ovary)}'] = ovary.state.name if hasattr(ovary.state, 'name') else str(ovary.state)
                except:
                    pass

        # Сохраняем состояния труб
        for tube in getattr(uterus, 'tubes', []):
            if tube:
                try:
                    self._last_states[key][f'tube_{id(tube)}'] = getattr(tube, 'current_stretch', 1.0)
                    self._last_states[key][f'tube_everted_{id(tube)}'] = getattr(tube, 'is_everted', False)
                except:
                    pass

        return events

    def process_reactions(self, body: 'Body', profile_name: str = "default") -> List[UterusReaction]:
        """Обработать реакции для тела."""
        if not hasattr(body, 'uterus_system') or not body.uterus_system:
            return []

        profile = self.get_profile(profile_name)
        reactions = []
        body_id = id(body)

        try:
            uteri = body.uterus_system.uteri if hasattr(body.uterus_system, 'uteri') else []
        except:
            return []

        for u_idx, uterus in enumerate(uteri):
            if uterus is None:
                continue
            uterus_id = str(u_idx)
            try:
                events = self.detect_events(uterus, body_id, uterus_id)
                for event in events:
                    reaction = profile.get_reaction(event)
                    if reaction:
                        reactions.append(reaction)
            except Exception as e:
                # Логируем ошибку но не прерываем работу
                print(f"[DEBUG] Error processing uterus {uterus_id}: {e}")
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

def register_uterus_reaction_commands(registry, reaction_system: UterusReactionSystem):
    """Зарегистрировать команды реакций матки."""
    from body_sim.ui.commands import Command, console

    def cmd_uterus_reactions(args, ctx):
        """Показать реакции на текущее состояние матки."""
        if not ctx.active_body:
            console.print("[red]No active body![/red]")
            return

        if not hasattr(ctx.active_body, 'uterus_system') or not ctx.active_body.uterus_system:
            console.print("[red]No uterus to react to![/red]")
            return

        # Определяем профиль
        profile_name = "default"
        body_type = type(ctx.active_body).__name__.lower()

        if "roxy" in body_type or "migurdia" in body_type:
            profile_name = "roxy"

        try:
            # Получаем реакции
            reactions = reaction_system.process_reactions(ctx.active_body, profile_name)

            if not reactions:
                console.print("[dim]No new uterus reactions...[/dim]")
                # Показываем текущее состояние для отладки
                if args and args[0] == 'debug':
                    console.print(f"[dim]Body type: {body_type}[/dim]")
                    console.print(f"[dim]Profile: {profile_name}[/dim]")
                    if hasattr(ctx.active_body.uterus_system, 'uteri'):
                        console.print(f"[dim]Uteri: {len(ctx.active_body.uterus_system.uteri)}[/dim]")
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
                    "fear": "bright_red",
                    "weird": "yellow",
                    "overwhelm": "red",
                    "agony": "bright_red",
                    "dissociation": "dim",
                    "unconscious": "dim",
                    "panic_embarrassment": "bright_yellow",
                    "pleasure_pain": "magenta",
                }
                color = color_map.get(reaction.emotion, "white")

                console.print(f"\n[{color}]{reaction.text}[/{color}]")
                if reaction.sound_effect:
                    console.print(f"[dim italic]{reaction.sound_effect}[/dim italic]")
                if reaction.physical_effect:
                    console.print(f"[dim]*{reaction.physical_effect}*[/dim]")

        except Exception as e:
            console.print(f"[red]Error processing uterus reactions: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")

    def cmd_uterus_reaction_test(args, ctx):
        """Тестировать конкретную реакцию матки."""
        if not args:
            # Показать доступные события
            console.print("[cyan]Available uterus events:[/cyan]")
            for event in UterusEventType:
                console.print(f"  {event.name}")
            console.print("\n[yellow]Profiles: roxy, default[/yellow]")
            return

        event_name = args[0].upper()
        try:
            event = UterusEventType[event_name]
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

    def cmd_uterus_reaction_clear(args, ctx):
        """Очистить сохранённые состояния матки."""
        if ctx.active_body:
            reaction_system.clear_state(id(ctx.active_body))
            console.print("[green]Cleared uterus reaction state for current body[/green]")
        else:
            reaction_system.clear_state()
            console.print("[green]Cleared all uterus reaction states[/green]")

    registry.register(Command(
        "uterus_reactions", ["ureact", "ur"],
        "Show uterus reactions",
        "uterus_reactions [debug]",
        cmd_uterus_reactions,
        "uterus"
    ))

    registry.register(Command(
        "uterus_reaction_test", ["urtest"],
        "Test specific uterus reaction",
        "uterus_reaction_test <event> [profile]",
        cmd_uterus_reaction_test,
        "debug"
    ))

    registry.register(Command(
        "uterus_reaction_clear", ["urclear"],
        "Clear uterus reaction states",
        "uterus_reaction_clear",
        cmd_uterus_reaction_clear,
        "debug"
    ))


def integrate_with_tick(bodies: List, dt: float, console):
    """Интегрировать реакции с tick обновлением."""
    system = get_uterus_reaction_system()

    for body in bodies:
        if not hasattr(body, 'uterus_system') or not body.uterus_system:
            continue

        # Определяем профиль
        profile_name = "default"
        body_type = type(body).__name__.lower()
        if "roxy" in body_type or "migurdia" in body_type:
            profile_name = "roxy"

        try:
            reactions = system.process_reactions(body, profile_name)
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
                    "fear": "bright_red",
                    "weird": "yellow",
                    "overwhelm": "red",
                    "agony": "bright_red",
                    "dissociation": "dim",
                    "unconscious": "dim",
                    "panic_embarrassment": "bright_yellow",
                    "pleasure_pain": "magenta",
                }
                color = color_map.get(reaction.emotion, "white")

                console.print(f"\n[{color}][Uterus] {reaction.text}[/{color}]")
                if reaction.sound_effect:
                    console.print(f"[dim italic]{reaction.sound_effect}[/dim italic]")
        except Exception as e:
            # Не прерываем tick из-за ошибки реакций
            pass


# Глобальный экземпляр системы
_reaction_system: Optional[UterusReactionSystem] = None

def get_uterus_reaction_system() -> UterusReactionSystem:
    """Получить глобальный экземпляр системы реакций матки."""
    global _reaction_system
    if _reaction_system is None:
        _reaction_system = UterusReactionSystem()
    return _reaction_system

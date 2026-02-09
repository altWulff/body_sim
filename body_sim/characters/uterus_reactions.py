# body_sim/characters/uterus_reactions.py
"""
Реакции персонажей на состояние репродуктивной системы.
Поддерживает разные типы персонажей (Roxy, Misaka, и т.д.)
"""

from typing import Dict, List, Callable, Optional, TYPE_CHECKING, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import random

if TYPE_CHECKING:
    from body_sim.anatomy.uterus import Uterus, Ovary, FallopianTube
    from body_sim.body.body import Body


class UterusEventType(Enum):
    """Типы событий матки для реакций."""
    # Инфляция
    INFLATION_START = auto()
    INFLATION_STRETCHED = auto()
    INFLATION_DISTENDED = auto()
    INFLATION_HYPER = auto()
    INFLATION_RISK = auto()
    INFLATION_ULTRA = auto()
    INFLATION_MEGA = auto()
    INFLATION_GIGA = auto()
    INFLATION_TERA = auto()
    INFLATION_MAX = auto()
    
    # Состояния матки
    UTERUS_EMPTY = auto()
    UTERUS_NORMAL = auto()
    UTERUS_TENSE = auto()
    UTERUS_OVERPRESSURED = auto()
    UTERUS_LEAKING = auto()
    
    # Пролапс
    PROLAPSE_DESCENDED = auto()
    PROLAPSE_PARTIAL = auto()
    PROLAPSE_COMPLETE = auto()
    PROLAPSE_EVERSIO = auto()
    
    # Яичники
    OVARY_ENLARGED = auto()
    OVARY_PROLAPSED = auto()
    OVARY_EVERTED = auto()
    OVARY_TORSION = auto()
    OVARY_INFLATED = auto()
    
    # Трубы
    TUBE_STRETCHED = auto()
    TUBE_DILATED = auto()
    TUBE_BLOCKED = auto()
    TUBE_PROLAPSED = auto()
    TUBE_EVERTED = auto()
    
    # Жидкость
    FLUID_ADDED = auto()
    FLUID_OVERFLOW = auto()
    FLUID_BACKFLOW = auto()
    
    # Предметы
    OBJECT_INSERTED = auto()
    OBJECT_DEEP = auto()
    OBJECT_REMOVED = auto()


@dataclass
class UterusReaction:
    """Реакция на событие матки."""
    text: str
    intensity: float = 1.0
    emotion: str = "neutral"
    sound_effect: Optional[str] = None
    physical_effect: Optional[str] = None
    cooldown: float = 0.0  # Кулдаун в секундах (0 = нет кулдауна)


class CharacterUterusProfile:
    """Профиль реакций персонажа на состояние матки."""
    
    def __init__(self, name: str, personality_traits: List[str]):
        self.name = name
        self.personality_traits = personality_traits
        self.reactions: Dict[UterusEventType, List[UterusReaction]] = {}
        self._setup_default_reactions()
    
    def _setup_default_reactions(self):
        """Базовые реакции (постоянные для активных состояний)."""
        self.reactions = {
            UterusEventType.UTERUS_NORMAL: [
                UterusReaction("Всё в порядке...", 0.1, "neutral"),
            ],
            UterusEventType.UTERUS_TENSE: [
                UterusReaction("Немного тянет внизу живота...", 0.3, "discomfort"),
                UterusReaction("Чувствую напряжение внутри...", 0.3, "discomfort"),
            ],
            UterusEventType.UTERUS_OVERPRESSURED: [
                UterusReaction("Слишком полно! Больно!", 0.8, "pain", "*стон*"),
                UterusReaction("Давит изнутри! Не могу терпеть!", 0.8, "pain", "*крик*"),
            ],
            UterusEventType.UTERUS_LEAKING: [
                UterusReaction("Что-то вытекает... стыдно...", 0.5, "embarrassment", "*вздох*"),
                UterusReaction("Мокро... всё текёт...", 0.5, "embarrassment"),
            ],
            UterusEventType.PROLAPSE_DESCENDED: [
                UterusReaction("Чувствую тяжесть... опускается...", 0.4, "fear", "*вздох*"),
            ],
            UterusEventType.PROLAPSE_COMPLETE: [
                UterusReaction("Что-то выходит наружу! Помогите!", 0.9, "panic", "*крик*"),
                UterusReaction("Всё выпадает! Всё наружу!", 0.95, "panic", "*истерика*"),
            ],
            UterusEventType.OVARY_EVERTED: [
                UterusReaction("Внутренности... снаружи... видно всем...", 0.95, "shock", "*вскрик*"),
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
        """Специфичные реакции Рокси (постоянные для активных состояний)."""
        
        # Инфляция - постоянные реакции пока активно
        self.reactions[UterusEventType.INFLATION_START] = [
            UterusReaction(
                "\"Н-не так сильно... там чувствительно...\" *краснеет*",
                0.4, "embarrassment", "*тихий стон*", "покраснение шеи"
            ),
            UterusReaction(
                "\"Растягивается... внутри всё давит...\" *сжимает живот*",
                0.4, "embarrassment", "*вздох*"
            ),
        ]
        
        self.reactions[UterusEventType.INFLATION_STRETCHED] = [
            UterusReaction(
                "\"Мигурдийская кожа такая нежная... натягивается...\"",
                0.5, "pleasure_pain", "*тихий стон*", "мурашки по коже"
            ),
            UterusReaction(
                "\"Как будто внутри шар... странное ощущение...\"",
                0.5, "weird", "*вздох*", "напряжение мышц"
            ),
        ]
        
        self.reactions[UterusEventType.INFLATION_DISTENDED] = [
            UterusReaction(
                "\"Видно?! Снаружи видно?! Я выгляжу беременной!\" *паника*",
                0.7, "panic_embarrassment", "*вскрик*", "сильное покраснение"
            ),
            UterusReaction(
                "\"Так полно... как будто что-то огромное внутри...\" *тяжело дышит*",
                0.6, "overwhelm", "*тяжёлое дыхание*", "выпячивается живот"
            ),
        ]
        
        self.reactions[UterusEventType.INFLATION_HYPER] = [
            UterusReaction(
                "\"Больше нельзя! Кожа натягивается слишком сильно!\"",
                0.8, "pain", "*стон боли*", "бледность кожи"
            ),
            UterusReaction(
                "\"Чувствую каждую стенку... так тонко... болит...\" *слёзы*",
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
        
        self.reactions[UterusEventType.INFLATION_ULTRA] = [
            UterusReaction(
                "\"Это... это невозможно... как я ещё цела...\" *шок*",
                0.9, "shock", "*дрожащий голос*", "потеря ориентации"
            ),
            UterusReaction(
                "\"Всё натянуто как барабан... любой удар...\"",
                0.9, "fear", "*дрожь*", "гиперчувствительность"
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
        
        # Пролапс - постоянные
        self.reactions[UterusEventType.PROLAPSE_DESCENDED] = [
            UterusReaction(
                "\"Что-то... опускается... тяжесть внизу...\" *бледнеет*",
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
                "\"МАТКА! МАТКА НАРУЖУ!\" *истерика* \"Врача!\"",
                0.95, "panic", "*истерический крик*", "шоковое состояние"
            ),
            UterusReaction(
                "\"Всё выпало! Всё наружу! Помогите!\" *истерика*",
                0.95, "panic", "*крик*", "обильное кровотечение"
            ),
        ]
        
        self.reactions[UterusEventType.PROLAPSE_EVERSIO] = [
            UterusReaction(
                "\"Всё вывернуто... всё наружу... видно всё...\" *обморок*",
                1.0, "shock", "*хрип*", "потеря сознания"
            ),
        ]
        
        # Яичники - постоянные
        self.reactions[UterusEventType.OVARY_ENLARGED] = [
            UterusReaction(
                "\"Сбоку болит... яичник увеличился... давит...\"",
                0.5, "discomfort", "*стон*", "прижимает руку к боку"
            ),
        ]
        
        self.reactions[UterusEventType.OVARY_PROLAPSED] = [
            UterusReaction(
                "\"Что-то шевелится внутри... труба тянет... болит...\"",
                0.7, "fear", "*вздох*", "спазмы"
            ),
        ]
        
        self.reactions[UterusEventType.OVARY_EVERTED] = [
            UterusReaction(
                "\"ЯИЧНИК! Он снаружи! Видишь?! Фолликулы!\" *паника*",
                0.9, "panic", "*вскрик*", "сильное кровотечение"
            ),
            UterusReaction(
                "\"Он свисает... на трубе... как вишня... мерзко...\" *шок*",
                0.85, "shock", "*дрожащий голос*", "потеря чувствительности"
            ),
        ]
        
        self.reactions[UterusEventType.OVARY_TORSION] = [
            UterusReaction(
                "\"БОЛЬ! РЕЖУЩАЯ! НЕ МОГУ ДВИГАТЬСЯ!\"",
                1.0, "agony", "*крик агонии*", "синюшность тканей"
            ),
        ]
        
        # Трубы - постоянные
        self.reactions[UterusEventType.TUBE_STRETCHED] = [
            UterusReaction(
                "\"Тянет сбоку... как ниточка... длинная... странно...\"",
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
        
        # Жидкость - постоянные
        self.reactions[UterusEventType.FLUID_OVERFLOW] = [
            UterusReaction(
                "\"Не влезает! Давит на всё внутри! Переполняется!\"",
                0.7, "pain", "*стон*", "напряжение пресса"
            ),
        ]
        
        self.reactions[UterusEventType.FLUID_BACKFLOW] = [
            UterusReaction(
                "\"Течёт обратно! Из яичников! Странное ощущение...\"",
                0.5, "weird", "*вздох*", "пульсация в боках"
            ),
        ]
        
        # Предметы - постоянные пока внутри
        self.reactions[UterusEventType.OBJECT_INSERTED] = [
            UterusReaction(
                "\"Т-туда?! В матку?!\" *краснеет до корней волос*",
                0.6, "embarrassment", "*писк*", "сильное сердцебиение"
            ),
            UterusReaction(
                "\"Чувствую... как внутри... шейка сжимается...\"",
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
    """Система отслеживания и реакции на события матки (постоянные реакции)."""
    
    def __init__(self):
        self.profiles: Dict[str, CharacterUterusProfile] = {}
        self._last_states: Dict[str, Dict] = {}
        self._active_events: Dict[str, Set[UterusEventType]] = {}  # Активные события по телу
        self._last_reaction_time: Dict[str, float] = {}  # Время последней реакции
        self._reaction_interval: float = 3.0  # Интервал между реакциями (сек)
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
    
    def _get_state_event(self, state_name: str) -> Optional[UterusEventType]:
        """Преобразовать имя состояния в событие."""
        state_map = {
            'EMPTY': UterusEventType.UTERUS_EMPTY,
            'NORMAL': UterusEventType.UTERUS_NORMAL,
            'TENSE': UterusEventType.UTERUS_TENSE,
            'OVERPRESSURED': UterusEventType.UTERUS_OVERPRESSURED,
            'LEAKING': UterusEventType.UTERUS_LEAKING,
        }
        return state_map.get(state_name)
    
    def detect_current_events(self, uterus: 'Uterus') -> Set[UterusEventType]:
        """Определить ВСЕ текущие активные события (постоянное отслеживание)."""
        events = set()
        
        if not uterus:
            return events
        
        # Безопасно получаем состояние
        try:
            current_state = uterus.state.name if hasattr(uterus, 'state') and uterus.state else 'NORMAL'
        except:
            current_state = 'NORMAL'
        
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
        
        # Состояние матки
        state_event = self._get_state_event(current_state)
        if state_event:
            events.add(state_event)
        
        # Инфляция (всегда добавляем если > 1.2)
        inflation_event = self._get_inflation_event(total_stretch)
        if inflation_event:
            events.add(inflation_event)
        
        # Пролапс
        prolapse_event = self._get_prolapse_event(descent, is_everted)
        if prolapse_event:
            events.add(prolapse_event)
        
        # Яичники
        for ovary in getattr(uterus, 'ovaries', []):
            if not ovary:
                continue
            
            is_ovary_everted = getattr(ovary, 'is_everted', False) or False
            if is_ovary_everted:
                events.add(UterusEventType.OVARY_EVERTED)
            
            size_ratio = getattr(ovary, 'size_ratio', 1.0) or 1.0
            if size_ratio > 1.5:
                events.add(UterusEventType.OVARY_ENLARGED)
            
            has_torsion = getattr(ovary, 'has_torsion', False) or False
            if has_torsion:
                events.add(UterusEventType.OVARY_TORSION)
        
        # Фаллопиевы трубы
        for tube in getattr(uterus, 'tubes', []):
            if not tube:
                continue
            
            stretch = getattr(tube, 'current_stretch', 1.0) or 1.0
            if stretch > 2.0:
                events.add(UterusEventType.TUBE_STRETCHED)
            
            is_tube_everted = getattr(tube, 'is_everted', False) or False
            if is_tube_everted:
                events.add(UterusEventType.TUBE_EVERTED)
        
        return events
    
    def process_reactions(self, body: 'Body', events: Set[UterusEventType], 
                         force_all: bool = False) -> List[UterusReaction]:
        """Обработать реакции на активные события."""
        reactions = []
        
        if not events:
            return reactions
        
        # Определяем профиль персонажа
        character_name = getattr(body, 'character_name', 'default') or 'default'
        profile = self.get_profile(character_name)
        
        body_key = str(id(body))
        current_time = getattr(body, 'simulation_time', 0.0)
        last_time = self._last_reaction_time.get(body_key, 0.0)
        
        # Проверяем кулдаун (если не force_all)
        if not force_all and (current_time - last_time) < self._reaction_interval:
            return reactions
        
        # Получаем реакции для всех активных событий
        for event in events:
            reaction = profile.get_reaction(event)
            if reaction:
                reactions.append(reaction)
        
        # Обновляем время последней реакции
        if reactions:
            self._last_reaction_time[body_key] = current_time
        
        return reactions
    
    def update(self, body: 'Body', dt: float = 1.0, force_reaction: bool = False) -> List[UterusReaction]:
        """Обновить систему реакций для тела (вызывать каждый тик)."""
        reactions = []
        
        if not hasattr(body, 'uterus_system') or not body.uterus_system:
            return reactions
        
        body_key = str(id(body))
        all_current_events: Set[UterusEventType] = set()
        
        # Собираем все активные события со всех маток
        for i, uterus in enumerate(getattr(body.uterus_system, 'uteri', [])):
            if not uterus:
                continue
            
            uterus_events = self.detect_current_events(uterus)
            all_current_events.update(uterus_events)
        
        # Сохраняем активные события
        self._active_events[body_key] = all_current_events
        
        # Обрабатываем реакции
        reactions = self.process_reactions(body, all_current_events, force_reaction)
        
        return reactions
    
    def get_active_events(self, body: 'Body') -> Set[UterusEventType]:
        """Получить текущие активные события для тела."""
        body_key = str(id(body))
        return self._active_events.get(body_key, set())
    
    def clear_body_state(self, body: 'Body'):
        """Очистить состояние для тела (при смене персонажа)."""
        body_key = str(id(body))
        self._active_events.pop(body_key, None)
        self._last_reaction_time.pop(body_key, None)
        self._last_states.pop(body_key, None)


# Глобальный экземпляр системы
_reaction_system: Optional[UterusReactionSystem] = None

def get_uterus_reaction_system() -> UterusReactionSystem:
    """Получить глобальный экземпляр системы реакций."""
    global _reaction_system
    if _reaction_system is None:
        _reaction_system = UterusReactionSystem()
    return _reaction_system


def register_uterus_reaction_commands(registry, reaction_system: UterusReactionSystem = None):
    """Зарегистрировать команды для системы реакций матки."""
    from body_sim.ui.commands import Command, CommandContext
    from rich.console import Console
    
    console = Console()
    
    if reaction_system is None:
        reaction_system = get_uterus_reaction_system()
    
    def cmd_uterus_reactions(args: List[str], ctx: CommandContext):
        """Показать текущие реакции на состояние матки (принудительно)."""
        if not ctx.active_body:
            console.print("[red]No body selected[/red]")
            return
        
        body = ctx.active_body
        reactions = reaction_system.update(body, force_reaction=True)
        
        if not reactions:
            # Показываем активные события даже если кулдаун
            active_events = reaction_system.get_active_events(body)
            if active_events:
                console.print("[dim]Active states (cooldown):[/dim]")
                for event in active_events:
                    console.print(f"  [cyan]- {event.name}[/cyan]")
            else:
                console.print("[dim]No active uterus states[/dim]")
            return
        
        console.print("[bold magenta]Uterus Reactions:[/bold magenta]")
        for reaction in reactions:
            console.print(f"\n[bold]{reaction.emotion.upper()}:[/bold] {reaction.text}")
            if reaction.sound_effect:
                console.print(f"  [dim]{reaction.sound_effect}[/dim]")
            if reaction.physical_effect:
                console.print(f"  [yellow]Effect:[/yellow] {reaction.physical_effect}")
    
    def cmd_uterus_profile(args: List[str], ctx: CommandContext):
        """Установить профиль реакций для персонажа."""
        if not ctx.active_body:
            console.print("[red]No body selected[/red]")
            return
        
        if not args:
            console.print("[red]Usage: uterus_profile <name>[/red]")
            console.print("Available: roxy, default")
            return
        
        profile_name = args[0].lower()
        if profile_name not in reaction_system.profiles:
            console.print(f"[red]Unknown profile: {profile_name}[/red]")
            return
        
        # Очищаем состояние при смене профиля
        reaction_system.clear_body_state(ctx.active_body)
        ctx.active_body.character_name = profile_name
        console.print(f"[green]Set uterus reaction profile to: {profile_name}[/green]")
    
    def cmd_uterus_status(args: List[str], ctx: CommandContext):
        """Показать статус активных состояний матки."""
        if not ctx.active_body:
            console.print("[red]No body selected[/red]")
            return
        
        body = ctx.active_body
        active_events = reaction_system.get_active_events(body)
        
        if not active_events:
            console.print("[dim]No active uterus states[/dim]")
            return
        
        console.print("[bold cyan]Active Uterus States:[/bold cyan]")
        for event in sorted(active_events, key=lambda x: x.name):
            console.print(f"  [magenta]•[/magenta] {event.name}")
    
    registry.register(Command(
        "uterus_reactions", ["ut_react"],
        "Show current uterus reactions (force)",
        "uterus_reactions",
        cmd_uterus_reactions,
        "uterus"
    ))
    
    registry.register(Command(
        "uterus_profile", ["ut_prof"],
        "Set uterus reaction profile",
        "uterus_profile <name>",
        cmd_uterus_profile,
        "uterus"
    ))
    
    registry.register(Command(
        "uterus_states", ["ut_stat"],
        "Show active uterus states",
        "uterus_states",
        cmd_uterus_status,
        "uterus"
    ))


def integrate_with_tick(bodies: List, dt: float = 1.0, console=None):
    """Интеграция реакций с tick командой (вызывать при каждом тике)."""
    if not bodies:
        return
    
    reaction_system = get_uterus_reaction_system()
    
    for body in bodies:
        if not hasattr(body, 'uterus_system') or not body.uterus_system:
            continue
        
        reactions = reaction_system.update(body, dt)
        # Выводим реакции если они есть и есть консоль
        if reactions and console:
            for reaction in reactions:
                console.print(f"[magenta]♀ {reaction.text}[/magenta]")
                if reaction.sound_effect:
                    console.print(f"  [dim]{reaction.sound_effect}[/dim]")

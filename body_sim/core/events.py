# === core/events.py ===
from __future__ import annotations
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


class EventType(Enum):
    # Системные
    TICK = auto()
    STATE_CHANGE = auto()
    MODIFIER_APPLIED = auto()
    COMPONENT_ADDED = auto()

    # Анатомические
    PENETRATION = auto()
    FLUID_TRANSFER = auto()
    FLUID_ADDED = auto()
    FLUID_REMOVED = auto()
    LEAK = auto()

    # Физиологические
    ORGASM = auto()
    OVULATION = auto()
    TRANSFORMATION = auto()
    MUSCLE_CONTRACTION = auto()
    PRESSURE_CHANGE = auto()
    PRESSURE_CRITICAL = auto()

    # Грудь специфичные
    LACTATION_START = auto()
    LACTATION_END = auto()
    LACTATION_ACTIVE = auto()
    ENGORGEMENT = auto()
    ENGORGEMENT_RELIEF = auto()
    INFLATION = auto()
    STRETCH_MARKS = auto()
    CUP_CHANGE = auto()
    NIPPLE_OPEN = auto()
    NIPPLE_CLOSE = auto()


@dataclass
class Event:
    type: EventType
    source: str
    target: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get(self, key: str, default=None):
        """Удобный доступ к данным события."""
        return self.data.get(key, default)


class EventBus:
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable[[Event], None]]] = {
            et: [] for et in EventType
        }
        self._global_handlers: List[Callable[[Event], None]] = []
        self._history: List[Event] = []

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """Подписаться на конкретный тип события."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[Event], None]):
        """Подписаться на все события."""
        self._global_handlers.append(handler)

    def emit(self, event: Event):
        """Вызвать событие."""
        self._history.append(event)

        # Глобальные обработчики
        for handler in self._global_handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in global handler: {e}")

        # Специфические обработчики
        for handler in self._handlers.get(event.type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"Error in handler for {event.type}: {e}")

    def get_history(self, component_id: str = None, limit: int = 100) -> List[Event]:
        events = self._history[-limit:]
        if component_id:
            events = [
                e
                for e in events
                if e.source == component_id or e.target == component_id
            ]
        return events

    def clear_history(self):
        """Очистить историю."""
        self._history.clear()

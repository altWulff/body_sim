# core/events.py


from __future__ import annotations
from typing import Dict, List, Callable, Any, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

class EventType(Enum):
    # Анатомические события
    PENETRATION = auto()
    FLUID_TRANSFER = auto()
    ORGASM = auto()
    OVULATION = auto()
    TRANSFORMATION = auto()
    MUSCLE_CONTRACTION = auto()
    
    # Состояния
    STATE_CHANGE = auto()
    MODIFIER_APPLIED = auto()
    
    # Системные
    COMPONENT_ADDED = auto()
    TICK = auto()

@dataclass
class Event:
    type: EventType
    source: str  # component_id
    target: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

class EventBus:
    """Централизованная шина событий для decoupling компонентов"""
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable[[Event], None]]] = {
            et: [] for et in EventType
        }
        self._history: List[Event] = []
        
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        self._handlers[event_type].append(handler)
        
    def emit(self, event: Event):
        self._history.append(event)
        for handler in self._handlers[event.type]:
            handler(event)
            
    def get_history(self, component_id: str = None, limit: int = 100) -> List[Event]:
        events = self._history[-limit:]
        if component_id:
            events = [e for e in events if e.source == component_id or e.target == component_id]
        return events
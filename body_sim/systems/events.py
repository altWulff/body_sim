# body_sim/systems/events.py
"""
Система событий для взаимодействий.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional, Set
from datetime import datetime
import uuid

from body_sim.core.enums import EventType, Sex


@dataclass
class Event:
    event_type: EventType
    source_id: str
    target_id: Optional[str]
    timestamp: float
    intensity: float = 1.0
    data: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def __post_init__(self):
        if 'timestamp' not in self.data:
            self.data['timestamp'] = self.timestamp


@dataclass
class EventHandler:
    event_types: Set[EventType]
    callback: Callable[[Event], None]
    priority: int = 0
    condition: Optional[Callable[[Event], bool]] = None
    once: bool = False
    active: bool = True
    
    def should_handle(self, event: Event) -> bool:
        if not self.active:
            return False
        if event.event_type not in self.event_types:
            return False
        if self.condition and not self.condition(event):
            return False
        return True


class EventBus:
    def __init__(self):
        self.handlers: List[EventHandler] = []
        self.event_history: List[Event] = []
        self.max_history = 1000
    
    def subscribe(self, event_types: List[EventType],
                  callback: Callable[[Event], None],
                  priority: int = 0,
                  condition: Optional[Callable[[Event], bool]] = None,
                  once: bool = False) -> EventHandler:
        handler = EventHandler(
            event_types=set(event_types),
            callback=callback,
            priority=priority,
            condition=condition,
            once=once
        )
        self.handlers.append(handler)
        self.handlers.sort(key=lambda h: h.priority, reverse=True)
        return handler
    
    def unsubscribe(self, handler: EventHandler) -> None:
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def emit(self, event: Event) -> None:
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        handled_once = []
        for handler in self.handlers:
            if handler.should_handle(event):
                try:
                    handler.callback(event)
                    if handler.once:
                        handled_once.append(handler)
                except Exception as e:
                    print(f"Event handler error: {e}")
        
        for handler in handled_once:
            self.unsubscribe(handler)
    
    def emit_simple(self, event_type: EventType, source_id: str,
                   target_id: Optional[str] = None,
                   intensity: float = 1.0, **data) -> None:
        event = Event(
            event_type=event_type,
            source_id=source_id,
            target_id=target_id,
            timestamp=datetime.now().timestamp(),
            intensity=intensity,
            data=data
        )
        self.emit(event)
    
    def get_history(self, event_type: Optional[EventType] = None,
                   source_id: Optional[str] = None,
                   limit: int = 100) -> List[Event]:
        filtered = self.event_history
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if source_id:
            filtered = [e for e in filtered if e.source_id == source_id]
        return filtered[-limit:]


class ReactionSystem:
    """Автоматические реакции на события."""
    
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.setup_default_reactions()
    
    def setup_default_reactions(self) -> None:
        self.bus.subscribe([EventType.PENETRATION_START], self.on_penetration_start, priority=10)
        self.bus.subscribe([EventType.PENETRATION_DEEP], self.on_deep_penetration, priority=10)
        self.bus.subscribe([EventType.PARTNER_EJACULATE], self.on_partner_ejaculate, priority=5)
        self.bus.subscribe([EventType.PAIN_THRESHOLD], self.on_pain, priority=20)
        self.bus.subscribe([EventType.ORGASM], self.on_orgasm, priority=15)
    
    def on_penetration_start(self, event: Event) -> None:
        body = event.data.get('body')
        if not body:
            return
        body.stats.arousal = min(1.0, body.stats.arousal + 0.1 * event.intensity)
        body.stats.pleasure += 0.05 * event.intensity
        
        if 'vagina_idx' in event.data and body.vaginas:
            v_idx = event.data['vagina_idx']
            if v_idx < len(body.vaginas):
                body.vaginas[v_idx].lubrication = min(1.0, body.vaginas[v_idx].lubrication + 0.1)
    
    def on_deep_penetration(self, event: Event) -> None:
        body = event.data.get('body')
        if not body:
            return
        body.stats.arousal = min(1.0, body.stats.arousal + 0.15 * event.intensity)
        body.stats.pleasure += 0.2 * event.intensity
        
        if event.intensity > 0.8:
            self.bus.emit_simple(EventType.DISCOMFORT, event.target_id or event.source_id, intensity=0.3)
    
    def on_partner_ejaculate(self, event: Event) -> None:
        body = event.data.get('body')
        if not body:
            return
        body.stats.arousal = min(1.0, body.stats.arousal + 0.2)
        body.stats.pleasure += 0.3
        
        if body.stats.arousal > 0.7:
            self.bus.emit_simple(EventType.SATISFACTION, body.name, intensity=0.8)
    
    def on_pain(self, event: Event) -> None:
        body = event.data.get('body')
        if not body:
            return
        body.stats.pleasure -= event.intensity * 0.5
        body.stats.pain = min(1.0, body.stats.pain + event.intensity)
        
        if 'vagina_idx' in event.data and body.vaginas:
            v_idx = event.data['vagina_idx']
            if v_idx < len(body.vaginas):
                body.vaginas[v_idx].contract(0.3)
    
    def on_orgasm(self, event: Event) -> None:
        body = event.data.get('body')
        if not body:
            return
        body.stats.pleasure = 1.0
        
        if 'vagina_idx' in event.data and body.vaginas:
            v_idx = event.data['vagina_idx']
            if v_idx < len(body.vaginas):
                for _ in range(5):
                    body.vaginas[v_idx].contract(0.5)
                    body.vaginas[v_idx].relax(0.3)
        
        for penis in body.penises:
            if penis.is_erect:
                body.ejaculate(body.penises.index(penis), force=1.0)


# Интеграция с Body через обёртку
@dataclass
class EventfulBody:
    """Body с интегрированной системой событий."""
    
    body: Any  # Forward reference to avoid circular import
    event_bus: EventBus = field(init=False)
    reactions: ReactionSystem = field(init=False)
    
    def __post_init__(self):
        self.event_bus = EventBus()
        self.reactions = ReactionSystem(self.event_bus)
    
    def __getattr__(self, name: str):
        return getattr(self.body, name)
    
    def tick(self, dt: float) -> None:
        self.body.tick(dt)
    
    def stimulate(self, region: str, index: int = 0, intensity: float = 0.1) -> None:
        self.body.stimulate(region, index, intensity)
        self.event_bus.emit_simple(
            EventType.STIMULATION,
            self.body.name,
            intensity=intensity,
            region=region,
            index=index,
            body=self.body
        )
        
        if region == "vagina" and intensity > 0.7:
            self.event_bus.emit_simple(
                EventType.PENETRATION_DEEP,
                self.body.name,
                intensity=intensity,
                vagina_idx=index,
                body=self.body
            )
    
    def penetrate(self, target_region: str, target_index: int, penis_index: int = 0) -> bool:
        success = self.body.penetrate(target_region, target_index, penis_index)
        if success:
            self.event_bus.emit_simple(
                EventType.PENETRATION_START,
                self.body.name,
                intensity=0.5,
                region=target_region,
                target_idx=target_index,
                penis_idx=penis_index,
                body=self.body
            )
        return success
        
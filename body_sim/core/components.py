# === core/components.py ===
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set
from datetime import datetime
import uuid

from body_sim.core.events import EventBus, Event, EventType

class ComponentInterface(ABC):
    @property
    @abstractmethod
    def component_id(self) -> str:
        pass
    
    @property
    @abstractmethod
    def component_type(self) -> str:
        pass
    
    @abstractmethod
    def update(self, delta_time: float, event_bus: EventBus):
        pass
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        pass

class BaseComponent(ComponentInterface):
    def __init__(self, name: str):
        self._id = f"{name}_{uuid.uuid4().hex[:8]}"
        self._name = name
        self._modifiers: Dict[str, Any] = {}
        self._connections: Set[str] = set()
        self._parent_body: Optional['Body'] = None
        self._event_listeners: List[callable] = []
        
    @property
    def component_id(self) -> str:
        return self._id
        
    @property
    def component_type(self) -> str:
        return self.__class__.__name__
        
    def connect_to(self, other: ComponentInterface):
        self._connections.add(other.component_id)
        
    def apply_modifier(self, key: str, value: Any, duration: float = None):
        self._modifiers[key] = {
            'value': value,
            'duration': duration,
            'applied_at': datetime.now()
        }
        
    def get_modifier(self, key: str, default=None):
        mod = self._modifiers.get(key)
        if mod and (mod['duration'] is None or 
                   (datetime.now() - mod['applied_at']).seconds < mod['duration']):
            return mod['value']
        return default
        
    def update(self, delta_time: float, event_bus: EventBus):
        expired = [k for k, m in self._modifiers.items() 
                  if m['duration'] and (datetime.now() - m['applied_at']).seconds > m['duration']]
        for k in expired:
            del self._modifiers[k]
            
    def get_state(self) -> Dict[str, Any]:
        return {
            'id': self._id,
            'type': self.component_type,
            'modifiers': list(self._modifiers.keys()),
            'connections': list(self._connections)
        }
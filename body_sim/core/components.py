# core/components.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set
import uuid

from body_sim.core.events import EventBus

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
        """Serialize state for rendering/saving"""
        pass

class BaseComponent(ComponentInterface):
    def __init__(self, name: str):
        self._id = f"{name}_{uuid.uuid4().hex[:8]}"
        self._name = name
        self._modifiers: Dict[str, Any] = {}
        self._connections: Set[str] = set()  # IDs связанных компонентов
        self._parent_body: Optional[Body] = None
        
    @property
    def component_id(self) -> str:
        return self._id
        
    @property
    def component_type(self) -> str:
        return self.__class__.__name__
        
    def connect_to(self, other: ComponentInterface):
        self._connections.add(other.component_id)
        
    def disconnect_from(self, other: ComponentInterface):
        self._connections.discard(other.component_id)
        
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

    def get_state(self) -> Dict[str, Any]:
        return {
            'id': self._id,
            'type': self.component_type,
            'modifiers': list(self._modifiers.keys()),
            'connections': list(self._connections)
        }
        
    def update(self, delta_time: float, event_bus: EventBus):
        # Cleanup expired modifiers
        expired = []
        for key, mod in self._modifiers.items():
            if mod['duration'] and (datetime.now() - mod['applied_at']).seconds > mod['duration']:
                expired.append(key)
        for key in expired:
            del self._modifiers[key]

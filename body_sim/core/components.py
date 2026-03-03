# === core/components.py ===
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set, List
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
        self._created_at = datetime.now()
        self._last_update = datetime.now()
        
    @property
    def component_id(self) -> str:
        return self._id
        
    @property
    def component_type(self) -> str:
        return self.__class__.__name__
        
    @property
    def name(self) -> str:
        return self._name
        
    def connect_to(self, other: ComponentInterface):
        """Создать связь с другим компонентом."""
        self._connections.add(other.component_id)
        
    def disconnect_from(self, other: ComponentInterface):
        """Разорвать связь."""
        self._connections.discard(other.component_id)
        
    def apply_modifier(self, key: str, value: Any, duration: float = None):
        """Применить модификатор."""
        self._modifiers[key] = {
            'value': value,
            'duration': duration,
            'applied_at': datetime.now()
        }
        
    def remove_modifier(self, key: str):
        """Удалить модификатор."""
        if key in self._modifiers:
            del self._modifiers[key]
        
    def get_modifier(self, key: str, default=None):
        """Получить активный модификатор."""
        mod = self._modifiers.get(key)
        if mod:
            if mod['duration'] is None:
                return mod['value']
            elapsed = (datetime.now() - mod['applied_at']).total_seconds()
            if elapsed < mod['duration']:
                return mod['value']
            else:
                del self._modifiers[key]
        return default
        
    def has_modifier(self, key: str) -> bool:
        """Проверить наличие активного модификатора."""
        return self.get_modifier(key) is not None
        
    def emit_event(self, event_bus: EventBus, event_type: EventType, data: Dict[str, Any] = None, target: str = None):
        """Удобный метод для эмиссии событий."""
        event_bus.emit(Event(
            type=event_type,
            source=self._id,
            target=target,
            data=data or {}
        ))
        
    def update(self, delta_time: float, event_bus: EventBus):
        """Базовое обновление - очистка истекших модификаторов."""
        self._last_update = datetime.now()
        
        # Очистка истекших модификаторов
        expired = []
        for k, m in self._modifiers.items():
            if m['duration'] is not None:
                elapsed = (datetime.now() - m['applied_at']).total_seconds()
                if elapsed > m['duration']:
                    expired.append(k)
        
        for k in expired:
            del self._modifiers[k]
            
    def get_state(self) -> Dict[str, Any]:
        """Базовое состояние."""
        return {
            'id': self._id,
            'type': self.component_type,
            'name': self._name,
            'modifiers': list(self._modifiers.keys()),
            'connections': list(self._connections),
            'created_at': self._created_at.isoformat(),
            'last_update': self._last_update.isoformat()
        }
        
    def __repr__(self):
        return f"{self.component_type}[{self._name}]({self._id[:8]})"

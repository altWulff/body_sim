# body_sim/anatomy/base.py
"""
Базовый класс для всех анатомических структур.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any


@dataclass
class Genital:
    """Базовый класс для всех гениталий."""
    name: str = "unnamed"
    sensitivity: float = 1.0
    arousal: float = 0.0
    pleasure: float = 0.0
    
    _listeners: Dict[str, List[Callable]] = field(default_factory=dict, repr=False)
    
    def stimulate(self, intensity: float = 0.1) -> None:
        """Базовая стимуляция."""
        self.arousal = min(1.0, self.arousal + intensity)
        self.pleasure += intensity * self.sensitivity
    
    def tick(self, dt: float) -> None:
        """Обновление состояния."""
        self.arousal = max(0.0, self.arousal - 0.1 * dt)
        self.pleasure = max(0.0, self.pleasure - 0.2 * dt)
    
    def on(self, event: str, callback: Callable[..., Any]) -> None:
        """Подписаться на событие."""
        self._listeners.setdefault(event, []).append(callback)
    
    def _emit(self, event: str, **data: Any) -> None:
        """Вызвать обработчики события."""
        for cb in self._listeners.get(event, []):
            cb(self, **data)
            
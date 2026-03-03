from typing import List, Optional, Dict, Any
from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus, EventType, Event
from .cup_size import CupSize
from .breast_row import BreastRow

class Breasts(AnatomicalComponent):
    """
    Контейнер для всех рядов груди.
    Поддерживает стандартную пару (left/right) и кросс-стимуляцию
    из старого кода.
    """
    
    def __init__(self, cup_size: CupSize = CupSize.C):
        super().__init__("breasts")
        self.cup_size = cup_size
        self.rows: List[BreastRow] = []
        
        # Стандартная пара
        self.add_row(side="left", cup_size=cup_size)
        self.add_row(side="right", cup_size=cup_size)
        
        self._event_bus: Optional[EventBus] = None
        self._cross_factor = 0.3  # Коэффициент перекрестной стимуляции
        
        # Грудная клетка
        self.chest_circumference: float = 85.0
        self.intermammary_distance: float = 18.0
    
    def add_row(self, side: str = "aux", cup_size: CupSize = None, size_factor: float = 1.0) -> BreastRow:
        """Добавить ряд груди."""
        cs = cup_size or self.cup_size
        # Дополнительные ряды обычно меньше
        if side.startswith("aux"):
            cs = CupSize.from_volume(cs.base_volume * size_factor)
        
        row = BreastRow(
            index=len(self.rows),
            side=side,
            cup_size=cs
        )
        self.rows.append(row)
        return row
    
    def set_event_bus(self, event_bus: EventBus):
        """Установить EventBus для кросс-стимуляции."""
        self._event_bus = event_bus
        self._setup_cross_stimulation()
    
    def _setup_cross_stimulation(self):
        """Перекрестная стимуляция left <-> right из старого кода."""
        if not self._event_bus:
            return
        
        left = self.get_by_side("left")
        right = self.get_by_side("right")
        
        if not left or not right:
            return
        
        def on_stimulation(event):
            if event.type != EventType.MODIFIER_APPLIED:
                return
            
            # Left -> Right
            if event.source == left.component_id:
                intensity = event.data.get('intensity', 0) if event.data else 0
                if intensity > 0.5:
                    right.stimulate(intensity * self._cross_factor)
            
            # Right -> Left
            elif event.source == right.component_id:
                intensity = event.data.get('intensity', 0) if event.data else 0
                if intensity > 0.5:
                    left.stimulate(intensity * self._cross_factor)
        
        self._event_bus.subscribe(EventType.MODIFIER_APPLIED, on_stimulation)
    
    def get_by_side(self, side: str) -> Optional[BreastRow]:
        """Получить грудь по стороне."""
        side_lower = side.lower()
        for row in self.rows:
            if row.side.lower() == side_lower:
                return row
        return None
    
    @property
    def left(self) -> Optional[BreastRow]:
        return self.get_by_side("left")
    
    @property
    def right(self) -> Optional[BreastRow]:
        return self.get_by_side("right")
    
    def stimulate(self, side: str, intensity: float = 1.0) -> Optional[dict]:
        """
        Стимулировать одну грудь с эмиссией события
        (для кросс-стимуляции).
        """
        breast = self.get_by_side(side)
        if not breast:
            return None
        
        result = breast.stimulate(intensity)
        
        # Эмитируем событие
        if self._event_bus:
            event = Event(
                type=EventType.MODIFIER_APPLIED,
                source=breast.component_id,
                data={
                    'intensity': intensity,
                    'action': 'stimulate',
                    'result': result
                }
            )
            self._event_bus.emit(event)
        
        return result
    
    def stimulate_both(self, intensity: float = 1.0):
        """Стимулировать обе основные груди."""
        self.stimulate("left", intensity)
        self.stimulate("right", intensity)
    
    def express(self, side: Optional[str] = None, amount: float = None, pressure: float = 1.0) -> float:
        """Сцеживание."""
        total = 0.0
        
        if side:
            breast = self.get_by_side(side)
            if breast:
                amt = amount or breast.get_total_milk() if hasattr(breast, 'get_total_milk') else amount or 100
                total += breast.express(amt, pressure)
        else:
            # Все ряды
            for row in self.rows:
                amt = amount or row.get_total_milk() if hasattr(row, 'get_total_milk') else amount or 100
                total += row.express(amt, pressure)
        
        return total
    
    def update(self, delta_time: float, event_bus: EventBus):
        """Обновление всех рядов."""
        if not self._event_bus and event_bus:
            self.set_event_bus(event_bus)
        
        for row in self.rows:
            row.update(delta_time, event_bus)
    
    def get_state(self) -> Dict[str, Any]:
        """Состояние всех рядов."""
        return {
            'cup_size': self.cup_size.name,
            'rows_count': len(self.rows),
            'rows': {row.side: row.get_full_state() for row in self.rows}
        }
    
    def get_full_state(self) -> Dict[str, Any]:
        """Для совместимости."""
        return self.get_state()

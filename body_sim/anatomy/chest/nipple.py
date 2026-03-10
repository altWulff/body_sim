from dataclasses import dataclass, field
from typing import Optional, Callable, List
from enum import Enum, auto
import math

class NippleState(Enum):
    SOFT = "soft"
    ERECT = "erect"
    INVERTED = "inverted"

@dataclass
class NipplePlug:
    name: str
    diameter: float
    length: float
    material: str = "silicone"
    has_hole: bool = False
    fluid_type: Optional[str] = None
    leak_reduction: float = 0.0  # 0-1, уменьшение утечки

@dataclass
class Nipple:
    name: str = "nipple"
    diameter: float = 1.0
    length: float = 0.8
    base_diameter: float = 1.0
    base_length: float = 0.8
    
    state: NippleState = NippleState.SOFT
    is_erect: bool = False
    sensitivity: float = 1.5
    
    gape_diameter: float = 0.0
    is_open: bool = False
    max_gape: float = 3.0
    
    plug: Optional[NipplePlug] = None
    duct_prolapse: float = 0.0
    current_width: float = field(init=False)  # Для совместимости со старым кодом
    
    # Слушатели событий
    _listeners: List = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        # Если base_поля имеют дефолтные значения, но diameter/length кастомные
        if self.base_diameter == 1.0 and self.diameter != 1.0:
            self.base_diameter = self.diameter
        if self.base_length == 0.8 and self.length != 0.8:
            self.base_length = self.length
        self.current_width = self.diameter
    
    def on(self, event: str, callback: Callable):
        self._listeners.append((event, callback))
    
    def _emit(self, event: str, **data):
        for ev, cb in self._listeners:
            if ev == event:
                cb(self, **data)
    
    def erect(self):
        if self.state != NippleState.INVERTED:
            self.state = NippleState.ERECT
            self.is_erect = True
            self.diameter = self.base_diameter * 1.2
            self.length = self.base_length * 1.3
            self.current_width = self.diameter
            self._emit("erect")
    
    def relax(self):
        self.state = NippleState.SOFT
        self.is_erect = False
        self.diameter = self.base_diameter
        self.length = self.base_length
        self.current_width = self.diameter
    
    def open(self, amount: Optional[float] = None):
        target = amount if amount is not None else self.diameter * 0.5
        self.gape_diameter = min(target, self.max_gape, self.diameter)
        self.is_open = self.gape_diameter > 0.01
        if self.is_open:
            self._emit("open", gape=self.gape_diameter)
    
    def close(self):
        self.gape_diameter = 0.0
        self.is_open = False
        self._emit("close")
    
    def stretch(self, diameter: float):
        self.gape_diameter = min(diameter, self.max_gape)
        self.is_open = self.gape_diameter > 0.01
    
    @property
    def effective_gape(self) -> float:
        """Эффективное отверстие с учетом плага."""
        if self.plug and not self.plug.has_hole:
            return 0.0
        base = self.gape_diameter if self.is_open else 0.0
        if self.plug and self.plug.has_hole:
            return min(base, self.plug.diameter * 0.8)
        return base
    
    def insert_plug(self, plug: NipplePlug) -> bool:
        if self.gape_diameter >= plug.diameter or self.plug is None:
            self.plug = plug
            self._emit("plug_inserted", plug=plug)
            return True
        return False
    
    def remove_plug(self) -> Optional[NipplePlug]:
        plug = self.plug
        self.plug = None
        if plug:
            self._emit("plug_removed", plug=plug)
        return plug
    
    def stimulate(self, intensity: float = 1.0):
        if not self.is_erect:
            self.erect()
        self.sensitivity = min(3.0, self.sensitivity * (1 + intensity * 0.1))
        self._emit("stimulate", intensity=intensity)
    
    def open_from_pressure(self, pressure: float, max_pressure: float = 3.0):
        """Открытие от давления (как в старом коде)."""
        if pressure > max_pressure * 0.3:
            target = self.diameter * 0.3 * (pressure / max_pressure)
            self.open(min(target, self.diameter * 0.5))
    
    def get_state(self) -> dict:
        return {
            'diameter': self.diameter,
            'length': self.length,
            'gape_diameter': self.gape_diameter,
            'effective_gape': self.effective_gape,
            'is_erect': self.is_erect,
            'is_open': self.is_open,
            'sensitivity': self.sensitivity,
            'has_plug': self.plug is not None
        }

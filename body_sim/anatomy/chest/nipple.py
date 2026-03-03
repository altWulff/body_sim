from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto

class NippleState(Enum):
    SOFT = "soft"
    ERECT = "erect"
    INVERTED = "inverted"

@dataclass
class NipplePlug:
    """Плаг для соска."""
    name: str
    diameter: float  # см
    length: float    # см
    material: str = "silicone"
    has_hole: bool = False  # Для сцеживания сквозь плаг
    fluid_type: Optional[str] = None  # Если трубка для жидкости

@dataclass
class Nipple:
    """
    Соска с поддержкой:
    - Эрекции (из старого NippleState)
    - Растяжения отверстия (gape)
    - Пенетрации и плагов
    """
    name: str = "nipple"
    
    # Размеры (из старого кода)
    diameter: float = 1.0  # см
    length: float = 0.8    # см
    base_diameter: float = 1.0
    base_length: float = 0.8
    
    # Состояние
    state: NippleState = NippleState.SOFT
    is_erect: bool = False  # Для совместимости со старым кодом
    sensitivity: float = 1.5
    
    # Растяжение отверстия (gape из старого кода)
    gape_diameter: float = 0.0
    is_open: bool = False
    max_gape: float = 3.0   # Максимальное растяжение
    
    # Плаг
    plug: Optional[NipplePlug] = None
    
    # Пролапс протоков (из новой структуры)
    duct_prolapse: float = 0.0  # см выпавших протоков
    
    def erect(self):
        """Эрекция соска."""
        if self.state != NippleState.INVERTED:
            self.state = NippleState.ERECT
            self.is_erect = True
            self.diameter = self.base_diameter * 1.2
            self.length = self.base_length * 1.3
    
    def relax(self):
        """Расслабление."""
        self.state = NippleState.SOFT
        self.is_erect = False
        self.diameter = self.base_diameter
        self.length = self.base_length
    
    def open(self, amount: Optional[float] = None):
        """Открыть/растянуть отверстие."""
        target = amount if amount is not None else self.diameter * 0.5
        self.gape_diameter = min(target, self.max_gape, self.diameter)
        self.is_open = self.gape_diameter > 0.01
    
    def close(self):
        """Закрыть отверстие."""
        self.gape_diameter = 0.0
        self.is_open = False
    
    def stretch(self, diameter: float):
        """Растянуть до определенного диаметра."""
        self.gape_diameter = min(diameter, self.max_gape)
        self.is_open = self.gape_diameter > 0.01
    
    def insert_plug(self, plug: NipplePlug) -> bool:
        """Вставить плаг."""
        if self.gape_diameter >= plug.diameter or self.plug is None:
            self.plug = plug
            return True
        return False
    
    def remove_plug(self) -> Optional[NipplePlug]:
        """Удалить плаг."""
        plug = self.plug
        self.plug = None
        return plug
    
    def stimulate(self, intensity: float = 1.0):
        """Стимуляция."""
        if not self.is_erect:
            self.erect()
        # Увеличиваем чувствительность временно
        self.sensitivity = min(3.0, self.sensitivity * (1 + intensity * 0.1))
    
    def get_state(self) -> dict:
        """Состояние для совместимости со старым кодом."""
        return {
            'diameter': self.diameter,
            'length': self.length,
            'gape_diameter': self.gape_diameter,
            'is_erect': self.is_erect,
            'is_open': self.is_open,
            'sensitivity': self.sensitivity,
            'has_plug': self.plug is not None
        }

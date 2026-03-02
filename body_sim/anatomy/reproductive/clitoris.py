# === anatomy/reproductive/clitoris.py ===
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus

@dataclass
class Clitoris(AnatomicalComponent):
    base_length: float = 1.5
    base_diameter: float = 0.5
    is_enlarged: bool = False
    enlargement_ratio: float = 1.0
    is_erect: bool = False
    erection_multiplier: float = 2.0
    can_transform: bool = True
    is_transformed: bool = False
    transformed_penis: Optional['Penis'] = field(default=None, repr=False)

    def __post_init__(self):
        super().__init__("clitoris", max_volume=5)

    @property
    def current_length(self) -> float:
        if self.is_transformed and self.transformed_penis:
            return self.transformed_penis.current_length
        length = self.base_length
        if self.is_enlarged: 
            length *= self.enlargement_ratio
        if self.is_erect: 
            length *= self.erection_multiplier
        return length

    def stimulate(self, amount: float = 0.1, source: str = None) -> None:
        super().stimulate(amount * 1.5, source)
        if amount > 0.3: 
            self.is_erect = True

    def transform_to_penis(self, target_length: float = 10.0, target_girth: float = 8.0) -> 'Penis':
        from body_sim.anatomy.reproductive.penis import Penis
        if self.is_transformed: 
            return self.transformed_penis
        
        self.is_transformed = True
        self.transformed_penis = Penis(
            name=f"transformed_from_{self.component_id}",
            base_length=target_length, 
            base_girth=target_girth,
            is_transformed_clitoris=True, 
            original_clitoris_size=self.base_length,
            sensitivity=self.sensitivity * 1.5
        )
        return self.transformed_penis

    def revert_to_clitoris(self) -> None:
        self.is_transformed = False
        self.transformed_penis = None
        self.is_enlarged = False
        self.enlargement_ratio = 1.0
        
    def update(self, delta_time: float, event_bus: EventBus):
        super().update(delta_time, event_bus)
        if self.is_erect and self.arousal < 0.3:
            self.is_erect = False
            
    def get_state(self) -> Dict[str, Any]:
        base = super().get_state()
        base.update({
            'base_length': self.base_length,
            'current_length': self.current_length,
            'is_erect': self.is_erect,
            'is_transformed': self.is_transformed,
            'can_transform': self.can_transform
        })
        return base
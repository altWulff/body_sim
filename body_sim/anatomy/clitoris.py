"""
Клитор - женский половой орган, может трансформироваться в пенис.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from body_sim.anatomy.base import Genital

if TYPE_CHECKING:
    from .penis import Penis


@dataclass
class Clitoris(Genital):
    base_length: float = 1.5
    base_diameter: float = 0.5
    is_enlarged: bool = False
    enlargement_ratio: float = 1.0
    is_erect: bool = False
    erection_multiplier: float = 2.0
    can_transform: bool = True
    is_transformed: bool = False
    transformed_penis: Optional[Penis] = None

    @property
    def current_length(self) -> float:
        if self.is_transformed and self.transformed_penis:
            return self.transformed_penis.current_length
        length = self.base_length
        if self.is_enlarged: length *= self.enlargement_ratio
        if self.is_erect: length *= self.erection_multiplier
        return length

    def stimulate(self, intensity: float = 0.1) -> None:
        super().stimulate(intensity)
        if intensity > 0.3: self.is_erect = True

    def transform_to_penis(self, target_length: float = 10.0, target_girth: float = 8.0) -> Penis:
        from .penis import Penis
        if self.is_transformed: return self.transformed_penis
        
        self.is_transformed = True
        self.transformed_penis = Penis(
            name=f"transformed_from_{self.name}",
            base_length=target_length, base_girth=target_girth,
            is_transformed_clitoris=True, original_clitoris_size=self.base_length,
            sensitivity=self.sensitivity * 1.5
        )
        return self.transformed_penis

    def revert_to_clitoris(self) -> None:
        self.is_transformed = False
        self.transformed_penis = None
        self.is_enlarged = False
        self.enlargement_ratio = 1.0
# anatomy/reproductive/tubes.py

from typing import Optional

from body_sim.anatomy.base import AnatomicalComponent
from body_sim.anatomy.reproductive.ovaries import Gamete


class FallopianTube(AnatomicalComponent):
    def __init__(self, side: str):
        super().__init__(f"tube_{side}", max_volume=10)
        self.side = side
        self.length = 10.0  # cm
        self.cilia_activity = 1.0
        self.current_gamete: Optional[Gamete] = None
        
    def transport(self, gamete: Gamete, direction: str = "to_uterus"):
        """direction: to_uterus или to_ovary (редко)"""
        self.current_gamete = gamete
        # Симуляция транспорта через 1-2 дня
        return True

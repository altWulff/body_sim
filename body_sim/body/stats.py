# body_sim/body/stats.py
"""
Статистики тела.
"""

from dataclasses import dataclass, field


@dataclass
class BodyStats:
    height: float = 170.0
    weight: float = 65.0
    hip_width: float = 35.0
    waist_width: float = 28.0
    shoulder_width: float = 40.0
    flexibility: float = 0.5
    arousal: float = 0.0
    pleasure: float = 0.0
    pain: float = 0.0
    fatigue: float = 0.0
    
    def tick(self, dt: float) -> None:
        self.arousal = max(0.0, self.arousal - 0.1 * dt)
        self.pleasure = max(0.0, self.pleasure - 0.2 * dt)
        self.pain = max(0.0, self.pain - 0.15 * dt)
        self.fatigue = max(0.0, self.fatigue - 0.05 * dt)
        
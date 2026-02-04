# body_sim/systems/grid.py
"""
Сетка грудей для групповых операций.
"""

from typing import List, Optional, Callable, Dict, Any, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from body_sim.anatomy.breast import Breast
    from body_sim.core.fluids import BreastFluid
    from body_sim.core.enums import FluidType


class BreastGrid:
    def __init__(
        self,
        rows: List[List['Breast']],
        labels: Optional[List[List[str]]] = None,
        randomize_cups: bool = False,
    ):
        self.rows: List[List['Breast']] = rows

        if labels is None:
            self.labels = [
                [f"{r}.{c}" for c in range(len(row))]
                for r, row in enumerate(rows)
            ]
        else:
            self.labels = labels

        if randomize_cups:
            self._randomize_row_cups()

    def _randomize_row_cups(self) -> None:
        from body_sim.core.enums import CupSize
        
        for row in self.rows:
            base = random.choice(list(CupSize))
            for b in row:
                b.cup = base
                b._base_volume = base.base_volume
                b._max_volume = b._base_volume * 1.5
                b._last_dynamic_cup = base

    def all(self) -> List['Breast']:
        return [b for row in self.rows for b in row]

    def get(self, row: int, col: int) -> 'Breast':
        return self.rows[row][col]

    def get_label(self, row: int, col: int) -> str:
        return self.labels[row][col]

    def tick_all(self, defs: Dict['FluidType', 'BreastFluid'], dt: float = 1.0) -> List[List[Dict[str, Any]]]:
        return [
            [b.tick(defs, dt) for b in row]
            for row in self.rows
        ]

    def add_to_all(self, fluid: 'FluidType | BreastFluid', amount: float) -> Dict[str, Any]:
        total_added = 0.0
        total_inflated = 0
        max_stretch = 1.0
        
        for b in self.all():
            old_stretch = b.inflation.stretch_ratio
            added = b.add_fluid(fluid, amount)
            total_added += added
            
            new_stretch = b.inflation.stretch_ratio
            if new_stretch > old_stretch:
                total_inflated += 1
                max_stretch = max(max_stretch, new_stretch)
        
        return {
            "total_added": total_added,
            "breasts_inflated": total_inflated,
            "max_stretch": max_stretch,
        }

    def add_to_filled(self, fluid: 'FluidType | BreastFluid', amount: float) -> Dict[str, Any]:
        total_added = 0.0
        targets = [b for b in self.all() if b.filled > 0]
        
        for b in targets:
            total_added += b.add_fluid(fluid, amount)
        
        return {
            "total_added": total_added,
            "targets_count": len(targets),
        }

    def add_to_row(self, row: int, fluid: 'FluidType | BreastFluid', amount: float) -> Dict[str, Any]:
        total_added = 0.0
        for b in self.rows[row]:
            total_added += b.add_fluid(fluid, amount)
        
        return {"total_added": total_added, "row": row}

    def add_to_breast(self, row: int, col: int, fluid: 'FluidType | BreastFluid', 
                     amount: float) -> Dict[str, Any]:
        breast = self.rows[row][col]
        old_stretch = breast.inflation.stretch_ratio
        added = breast.add_fluid(fluid, amount)
        new_stretch = breast.inflation.stretch_ratio
        
        return {
            "added": added,
            "inflated": new_stretch > old_stretch,
            "stretch_ratio": new_stretch,
        }

    def drain_all(self, percentage: float = 100.0) -> Dict[str, Any]:
        total_removed = 0.0
        for b in self.all():
            to_remove = b.filled * (percentage / 100.0)
            total_removed += b.remove_fluid(to_remove)
        
        return {"total_removed": total_removed, "percentage": percentage}

    def on_all(self, event: str, callback: Callable[..., Any]) -> None:
        for b in self.all():
            b.on(event, callback)

    def stats(self) -> Dict[str, Any]:
        breasts = self.all()
        if not breasts:
            return {"count": 0}
        
        stretches = [b.inflation.stretch_ratio for b in breasts]
        avg_stretch = sum(stretches) / len(stretches)
        
        return {
            "count": len(breasts),
            "total_filled": sum(b.filled for b in breasts),
            "total_capacity": sum(b._max_volume for b in breasts),
            "avg_sag": round(sum(b.sag for b in breasts) / len(breasts), 2),
            "leaking": sum(1 for b in breasts if b._state.name == "LEAKING"),
            "avg_stretch": round(avg_stretch, 2),
            "max_stretch": round(max(stretches), 2),
        }
        
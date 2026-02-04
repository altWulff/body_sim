# body_sim/ui/render.py
"""
Базовый текстовый рендеринг (без зависимостей от rich).
"""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from body_sim.anatomy.breast import Breast
    from body_sim.systems.grid import BreastGrid
    from body_sim.core.fluids import BreastFluid


def render_breast_status(breast: 'Breast', defs: dict, label: str = "") -> str:
    """Базовый текстовый статус груди."""
    lines = [
        f"=== Breast {label} ===",
        f"Cup: {breast.cup.name} (dynamic: {breast.dynamic_cup.name})",
        f"Filled: {breast.filled:.1f}ml / {breast._max_volume:.1f}ml",
        f"State: {breast.state.name}",
        f"Pressure: {breast.pressure(defs):.2f}",
        f"Sag: {breast.sag:.3f}",
        f"Elasticity: {breast.elasticity:.2f}",
        f"Areola: {breast.areola.diameter:.1f}cm (base: {breast.areola.base_diameter:.1f}cm)",
        f"Nipples: {len(breast.areola.nipples)}",
    ]
    
    for i, nipple in enumerate(breast.areola.nipples):
        lines.append(f"  [{i}] {nipple.current_length:.1f}x{nipple.current_width:.1f}cm, "
                    f"gape={nipple.gape_diameter:.2f}cm, open={nipple.is_open}")
    
    if breast.insertion_manager.inserted_objects:
        lines.append(f"Inserted objects: {len(breast.insertion_manager)}")
        for obj in breast.insertion_manager.inserted_objects:
            lines.append(f"  - {obj.name}: {obj.effective_volume:.1f}ml")
    
    return "\n".join(lines)


def render_grid(grid: 'BreastGrid', defs: dict) -> str:
    """Рендер всей сетки грудей."""
    lines = ["=" * 50, "BREAST GRID STATUS", "=" * 50]
    
    for r_idx, row in enumerate(grid.rows):
        for c_idx, breast in enumerate(row):
            label = grid.get_label(r_idx, c_idx)
            lines.append("")
            lines.append(render_breast_status(breast, defs, label))
    
    lines.append("")
    lines.append("=" * 50)
    lines.append(f"Total: {len(grid.all())} breasts")
    stats = grid.stats()
    lines.append(f"Total filled: {stats.get('total_filled', 0):.1f}ml")
    lines.append(f"Leaking: {stats.get('leaking', 0)}")
    
    return "\n".join(lines)


def render_breast_compact(breast: 'Breast') -> str:
    """Компактное представление груди."""
    fill_pct = (breast.filled / breast._max_volume * 100) if breast._max_volume > 0 else 0
    state_indicator = {
        'EMPTY': '○',
        'NORMAL': '●',
        'TENSE': '◐',
        'LEAKING': '💧',
        'OVERPRESSURED': '⚠️'
    }.get(breast.state.name, '?')
    
    return f"{state_indicator} {breast.cup.name}: {fill_pct:.0f}% ({breast.filled:.0f}ml)"

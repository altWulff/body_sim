# body_sim/ui/render.py
"""
Базовый текстовый рендеринг (общие функции).
Импортируйте breast_render для рендеринга груди.
"""

# Реэкспорт для обратной совместимости
from body_sim.ui.breast_render import (
    render_breast_status,
    render_grid,
    render_breast_compact,
    BreastRenderer,
    render_breast_detailed,
    render_breast_rich,
    render_grid_rich,
    create_breast_renderer,
)

__all__ = [
    'render_breast_status',
    'render_grid', 
    'render_breast_compact',
    'BreastRenderer',
    'render_breast_detailed',
    'render_breast_rich',
    'render_grid_rich',
    'create_breast_renderer',
]

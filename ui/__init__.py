# body_sim/ui/__init__.py
"""
Интерфейс пользователя - консоль и рендеринг.
"""

from body_sim.ui.console import run_console
from body_sim.ui.rich_render import (
    render_body_list, render_full_body,
    render_breasts, render_genitals
)

__all__ = [
    "run_console",
    "render_body_list", "render_full_body",
    "render_breasts", "render_genitals",
]

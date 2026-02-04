# body_sim/ui/uterus_render.py
"""
Компактный Rich-рендеринг системы матки.
"""

from typing import Optional, List
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich.tree import Tree
from rich import box


class UterusRenderer:
    """Компактный рендерер системы матки."""
    
    COLORS = {
        'normal': 'green',
        'warning': 'yellow',
        'danger': 'red',
        'critical': 'bright_red',
        'info': 'cyan',
        'muted': 'dim',
    }
    
    STATE_EMOJI = {
        'NORMAL': '●',
        'DESCENDED': '◐',
        'PROLAPSED': '◉',
        'EVERTED': '◉',
        'INVERTED': '○',
    }
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def _get_state_emoji(self, state) -> str:
        if state is None:
            return '○'
        return self.STATE_EMOJI.get(getattr(state, 'name', str(state)), '○')
    
    def _bar(self, value: float, width: int = 6) -> str:
        value = value or 0
        filled = int(min(value, 1.0) * width)
        color = 'green' if value > 0.7 else 'yellow' if value > 0.4 else 'red'
        return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/{color}]"
    
    def render_uterus(self, uterus, title: str = "U") -> Panel:
        """Компактный рендер матки."""
        state = getattr(uterus, 'state', None)
        emoji = self._get_state_emoji(state)
        state_name = getattr(state, 'name', 'Unknown')[:4]
        
        # Компактная строка
        length = getattr(uterus, 'current_length', 0) or 0
        volume = getattr(uterus, 'current_volume', 0) or 0
        
        line1 = f"{emoji} {state_name} | {length:.1f}cm | {volume:.0f}ml"
        
        # Физиология
        tone = getattr(uterus, 'muscle_tone', 0) or 0
        ligaments = getattr(uterus, 'ligament_integrity', 0) or 0
        pelvic = getattr(uterus, 'pelvic_floor_strength', 0) or 0
        
        line2 = f"T:{self._bar(tone)} L:{self._bar(ligaments)} P:{self._bar(pelvic)}"
        
        content = f"{line1}\\n{line2}"
        
        # Пролапс
        if getattr(uterus, 'is_prolapsed', False):
            stage = getattr(uterus, 'prolapse_stage', 0) or 0
            content += f"\\n[red]Prolapse: {stage:.0%}[/red]"
        
        return Panel(
            content,
            title=title,
            box=box.SIMPLE,
            border_style='red' if getattr(uterus, 'is_everted', False) else 'green',
            padding=(0, 1)
        )
    
    def render_ovary_compact(self, ovary) -> str:
        """Компактный рендер яичника."""
        state = getattr(ovary, 'state', None)
        state_name = getattr(state, 'name', 'Unknown')[:4]
        side = getattr(ovary, 'side', '?')[:1].upper()
        return f"{side}:{state_name}"
    
    def render_tube_compact(self, tube) -> str:
        """Компактный рендер трубы."""
        state = getattr(tube, 'state', None)
        state_name = getattr(state, 'name', 'Unknown')[:4]
        side = getattr(tube, 'side', '?')[:1].upper()
        length = getattr(tube, 'current_length', 0) or 0
        return f"{side}:{state_name} {length:.1f}cm"
    
    def render_full_system(self, system, title: str = "U") -> Panel:
        """Компактный рендер системы."""
        uteri = getattr(system, 'uteri', [])
        
        if not uteri:
            return Panel("[dim]No uterus[/dim]", title=title, box=box.SIMPLE)
        
        if len(uteri) == 1:
            uterus = uteri[0]
            
            # Основная информация
            panels = [self.render_uterus(uterus, "U")]
            
            # Трубы и яичники компактно
            tubes = getattr(uterus, 'tubes', [])
            if tubes:
                tube_lines = []
                for tube in tubes:
                    tube_str = self.render_tube_compact(tube)
                    ovary = getattr(tube, 'ovary', None)
                    if ovary:
                        tube_str += f" | {self.render_ovary_compact(ovary)}"
                    tube_lines.append(tube_str)
                
                panels.append(Panel(
                    "\\n".join(tube_lines),
                    title="T&O",
                    box=box.SIMPLE,
                    border_style="magenta",
                    padding=(0, 1)
                ))
            
            return Panel(
                Columns(panels),
                title=f"🌸 {title}",
                box=box.SIMPLE,
                border_style="bright_cyan",
                padding=(0, 1)
            )
        
        # Множественные матки
        uterus_panels = [self.render_uterus(u, f"U{i+1}") for i, u in enumerate(uteri)]
        
        return Panel(
            Columns(uterus_panels),
            title=f"🌸 {title} ({len(uteri)})",
            box=box.SIMPLE,
            border_style="bright_cyan",
            padding=(0, 1)
        )
    
    def render_tree_view(self, system) -> Tree:
        """Компактное древовидное представление."""
        root = Tree("🌸 U")
        
        uteri = getattr(system, 'uteri', [])
        for i, uterus in enumerate(uteri):
            state = getattr(uterus, 'state', None)
            emoji = self._get_state_emoji(state)
            state_name = getattr(state, 'name', 'Unknown')[:4]
            
            volume = getattr(uterus, 'current_volume', 0) or 0
            u_node = root.add(f"{emoji}U{i+1}:{state_name} {volume:.0f}ml")
            
            tubes = getattr(uterus, 'tubes', [])
            if tubes:
                for tube in tubes:
                    side = getattr(tube, 'side', '?')[:1].upper()
                    t_state = getattr(getattr(tube, 'state', None), 'name', '?')[:4]
                    t_node = u_node.add(f"{side}:{t_state}")
                    
                    ovary = getattr(tube, 'ovary', None)
                    if ovary:
                        o_state = getattr(getattr(ovary, 'state', None), 'name', '?')[:4]
                        t_node.add(f"O:{o_state}")
        
        return root
    
    def print(self, renderable: RenderableType):
        self.console.print(renderable)
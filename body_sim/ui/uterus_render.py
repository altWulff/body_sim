# body_sim/ui/uterus_render.py
"""
Улучшенный Rich-рендеринг системы матки с детальной визуализацией пролапса,
яичников и фаллопиевых труб.
"""

from typing import Optional, List, Dict, Any, Tuple
from rich.console import Console, RenderableType, Group
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich.tree import Tree
from rich.layout import Layout
from rich.align import Align
from rich import box


class UterusRenderer:
    """Улучшенный рендерер системы матки с визуализацией пролапса и придатков."""
    
    COLORS = {
        'normal': 'green',
        'warning': 'yellow',
        'danger': 'red',
        'critical': 'bright_red',
        'info': 'cyan',
        'muted': 'dim',
        'magic': 'magenta',
        'migurdian': 'blue',
    }
    
    STATE_STYLES = {
        'NORMAL': ('🟢', 'green', 'Норма'),
        'DESCENDED': ('🟡', 'yellow', 'Опущена'),
        'PROLAPSED': ('🟠', 'bright_red', 'Пролапс'),
        'EVERTED': ('🔴', 'red', 'ВЫВОРОТ'),
        'INVERTED': ('⚫', 'dim', 'Инверсия'),
    }
    
    # Состояния яичника
    OVARY_STATE_STYLES = {
        'NORMAL': ('🟢', 'green', 'Норма'),
        'ENLARGED': ('🟡', 'yellow', 'Увеличен'),
        'PROLAPSED': ('🟠', 'bright_red', 'Пролапс'),
        'EVERTED': ('🔴', 'red', 'ВЫВОРОТ'),
        'TORSION': ('⛔', 'bright_red', 'Перекрут'),
    }
    
    # Состояния фаллопиевой трубы
    TUBE_STATE_STYLES = {
        'NORMAL': ('🟢', 'green', 'Норма'),
        'DILATED': ('🟡', 'yellow', 'Расширена'),
        'BLOCKED': ('⛔', 'red', 'Заблокирована'),
        'PROLAPSED': ('🟠', 'bright_red', 'Пролапс'),
        'EVERTED_WITH_OVARY': ('🔴', 'red', 'ВЫВОРОТ'),
    }
    
    SIDE_EMOJIS = {
        'left': '🌙',
        'right': '☀️',
        'unknown': '⚪'
    }
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def _get_state_style(self, state) -> Tuple[str, str, str]:
        """Получить стиль для состояния матки."""
        if state is None:
            return ('⚪', 'dim', 'None')
        state_name = getattr(state, 'name', str(state))
        return self.STATE_STYLES.get(state_name, ('⚪', 'dim', state_name))
    
    def _get_ovary_state_style(self, state) -> Tuple[str, str, str]:
        """Получить стиль для состояния яичника."""
        if state is None:
            return ('⚪', 'dim', 'None')
        state_name = getattr(state, 'name', str(state))
        return self.OVARY_STATE_STYLES.get(state_name, ('⚪', 'dim', state_name))
    
    def _get_tube_state_style(self, state) -> Tuple[str, str, str]:
        """Получить стиль для состояния трубы."""
        if state is None:
            return ('⚪', 'dim', 'None')
        state_name = getattr(state, 'name', str(state))
        return self.TUBE_STATE_STYLES.get(state_name, ('⚪', 'dim', state_name))
    
    def _bar(self, value: float, width: int = 8, color_map: Dict[str, str] = None) -> Text:
        """Улучшенный прогресс-бар с градиентом."""
        value = max(0.0, min(1.0, value or 0))
        filled = int(value * width)
        
        if color_map:
            if value > 0.7:
                color = color_map.get('high', 'green')
            elif value > 0.4:
                color = color_map.get('medium', 'yellow')
            else:
                color = color_map.get('low', 'red')
        else:
            color = 'green' if value > 0.7 else 'yellow' if value > 0.4 else 'red'
        
        bar_text = f"{'█' * filled}{'░' * (width - filled)}"
        return Text.from_markup(f"[{color}]{bar_text}[/{color}]")
    
    def _format_volume(self, volume: float) -> str:
        """Форматировать объём с единицами."""
        if volume >= 1000:
            return f"{volume/1000:.1f}L"
        return f"{volume:.0f}ml"
    
    def _render_follicles_visual(self, sizes: List[float], max_display: int = 6) -> str:
        """Визуализация фолликулов."""
        if not sizes:
            return "[dim]Нет[/dim]"
        
        visual_parts = []
        for size in sizes[:max_display]:
            if size < 0.3:
                emoji, color = "•", "dim"
            elif size < 0.8:
                emoji, color = "○", "cyan"
            elif size < 1.5:
                emoji, color = "◐", "bright_cyan"
            else:
                emoji, color = "●", "bright_yellow"
            visual_parts.append(f"[{color}]{emoji}[/{color}]")
        
        if len(sizes) > max_display:
            visual_parts.append(f"[dim]+{len(sizes) - max_display}[/dim]")
        
        return " ".join(visual_parts)
    
    # ======================
    # UTERUS RENDER
    # ======================
    
    def render_uterus_detailed(self, uterus, title: str = "Матка") -> Panel:
        """Детальный рендер матки с визуализацией пролапса."""
        state = getattr(uterus, 'state', None)
        emoji, color, state_desc = self._get_state_style(state)
        
        # Основные параметры
        length = getattr(uterus, 'current_length', 0) or 0
        base_length = getattr(uterus, 'base_length', 7.0) or 7.0
        volume = getattr(uterus, 'current_volume', 0) or 0
        cavity = getattr(uterus, 'cavity_volume', 50.0) or 50.0
        
        # Содержимое
        fluids = getattr(uterus, 'fluids', {})
        fluid_total = sum(fluids.values()) if fluids else 0
        objects = getattr(uterus, 'inserted_objects', [])
        
        # Пролапс
        descent = getattr(uterus, 'descent_position', 0) or 0
        prolapse_stage = getattr(uterus, 'prolapse_stage', 0) or 0
        is_everted = getattr(uterus, 'is_everted', False)
        is_prolapsed = getattr(uterus, 'is_prolapsed', False)
        
        # Создаём таблицу
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Param", style="cyan", width=12)
        table.add_column("Value", style="white")
        
        # Состояние и размеры
        table.add_row("Состояние", f"[{color}]{emoji} {state_desc}[/{color}]")
        table.add_row("Длина", f"{length:.1f}cm / {base_length:.1f}cm база")
        table.add_row("Объём", f"{self._format_volume(volume)} / {self._format_volume(cavity)} полость")
        
        # Заполнение
        if fluid_total > 0 or objects:
            fill_info = []
            if fluid_total > 0:
                fluid_types = ", ".join([f"{k.name}:{v:.0f}ml" for k, v in fluids.items()])
                fill_info.append(f"💧 {fluid_total:.0f}ml ({fluid_types})")
            if objects:
                fill_info.append(f"📦 {len(objects)} предметов")
            table.add_row("Содержимое", "\\n".join(fill_info))
        
        # Физиология
        tone = getattr(uterus, 'muscle_tone', 0) or 0
        ligaments = getattr(uterus, 'ligament_integrity', 0) or 0
        pelvic = getattr(uterus, 'pelvic_floor_strength', 0) or 0
        walls = getattr(uterus, 'walls', None)
        
        phys_table = Table(box=None, show_header=False, padding=(0, 2))
        phys_table.add_column("Stat", width=8)
        phys_table.add_column("Bar", width=10)
        phys_table.add_column("Value", width=6)
        
        phys_table.add_row("Тонус", self._bar(tone), f"{tone:.0%}")
        phys_table.add_row("Связки", self._bar(ligaments), f"{ligaments:.0%}")
        phys_table.add_row("Таз.дно", self._bar(pelvic), f"{pelvic:.0%}")
        
        if walls:
            integrity = getattr(walls, 'integrity', 1.0) or 1.0
            fatigue = getattr(walls, 'fatigue', 0.0) or 0.0
            stretch = getattr(walls, 'stretch_ratio', 1.0) or 1.0
            phys_table.add_row("Целостность", self._bar(integrity), f"{integrity:.0%}")
            phys_table.add_row("Усталость", self._bar(fatigue, color_map={'high': 'red', 'medium': 'yellow', 'low': 'green'}), f"{fatigue:.0%}")
            phys_table.add_row("Растяжение", f"[cyan]×{stretch:.1f}[/cyan]", "")
        
        table.add_row("Физиология", phys_table)
        
        # Визуализация пролапса
        if is_prolapsed or is_everted:
            prolapse_viz = self._render_prolapse_visual(descent, is_everted)
            table.add_row("Пролапс", prolapse_viz)
        
        # При полном выворачивании - предупреждение
        if is_everted:
            everted_volume = getattr(uterus, 'everted_volume', 0) or 0
            table.add_row(
                "⚠️ ВНИМАНИЕ", 
                f"[bold red]ПОЛНЫЙ ВЫВОРОТ![/bold red]\\n"
                f"Внешний объём: {self._format_volume(everted_volume)}\\n"
                f"Всё содержимое вытолкнуто наружу!"
            )
        
        # Шейка матки
        cervix = getattr(uterus, 'cervix', None)
        if cervix:
            cerv_state = getattr(cervix, 'state', None)
            cerv_emoji, cerv_color, cerv_desc = self._get_state_style(cerv_state)
            dilation = getattr(cervix, 'current_dilation', 0) or 0
            max_dil = getattr(cervix, 'max_dilation', 10.0) or 10.0
            
            cerv_text = f"[{cerv_color}]{cerv_emoji} {cerv_desc}[/{cerv_color}] "
            cerv_text += f"Раскрытие: {dilation:.1f}cm / {max_dil:.1f}cm"
            table.add_row("Шейка", cerv_text)
        
        border = 'red' if is_everted else 'bright_red' if is_prolapsed else 'green'
        
        return Panel(
            table,
            title=f"[bold]{emoji} {title}[/bold]",
            box=box.ROUNDED,
            border_style=border,
            padding=(1, 2)
        )
    
    def _render_prolapse_visual(self, descent: float, is_everted: bool) -> Text:
        """Визуализация степени пролапса."""
        stages = 10
        current = int(descent * stages)
        
        colors = []
        for i in range(stages):
            if is_everted:
                colors.append("🔴")
            elif i < current:
                if i < 3:
                    colors.append("🟢")
                elif i < 5:
                    colors.append("🟡")
                elif i < 7:
                    colors.append("🟠")
                else:
                    colors.append("🔴")
            else:
                colors.append("⚪")
        
        bar = "".join(colors)
        percent = f"{descent:.0%}"
        
        return Text.from_markup(f"{bar} [{percent}]")
    
    # ======================
    # OVARY DETAILED RENDER
    # ======================
    
    def render_ovary_detailed(self, ovary, title: Optional[str] = None) -> Panel:
        """Детальный рендер яичника."""
        if ovary is None:
            return Panel("[dim]Яичник отсутствует[/dim]", 
                        title="Яичник", box=box.ROUNDED, border_style="dim")
        
        state = getattr(ovary, 'state', None)
        emoji, color, state_name = self._get_ovary_state_style(state)
        side = getattr(ovary, 'side', 'unknown')
        side_emoji = self.SIDE_EMOJIS.get(side, '⚪')
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Param", style="cyan", width=12)
        table.add_column("Value", style="white")
        
        table.add_row("Состояние", f"[{color}]{emoji} {state_name}[/{color}]")
        
        # Размеры
        length = getattr(ovary, 'length', 3.0)
        width = getattr(ovary, 'width', 2.0)
        thickness = getattr(ovary, 'thickness', 1.5)
        volume = ovary.calculate_volume() if hasattr(ovary, 'calculate_volume') else 0
        
        table.add_row("Размер", f"{length}×{width}×{thickness}cm")
        table.add_row("Объём", f"{volume:.1f}ml")
        
        # Пролапс
        prolapse = getattr(ovary, 'prolapse_degree', 0.0)
        if prolapse > 0:
            table.add_row("Выпадение", self._bar(prolapse))
        
        # Фолликулы
        follicles = getattr(ovary, 'follicle_count', 5)
        follicle_sizes = getattr(ovary, 'follicle_sizes', [])
        if follicle_sizes:
            avg = sum(follicle_sizes) / len(follicle_sizes)
            max_f = max(follicle_sizes)
            follicle_viz = self._render_follicles_visual(follicle_sizes)
            table.add_row("Фолликулы", f"{follicles}шт ~{avg:.1f}cm max:{max_f:.1f}cm\\n{follicle_viz}")
        
        # Физиология
        hormones = getattr(ovary, 'hormone_production', 1.0)
        blood = getattr(ovary, 'blood_supply', 1.0)
        
        phys_table = Table(box=None, show_header=False)
        phys_table.add_column("Stat", width=8)
        phys_table.add_column("Bar", width=10)
        
        phys_table.add_row("Гормоны", self._bar(hormones))
        phys_table.add_row("Кровь", self._bar(blood, color_map={'high': 'bright_red', 'medium': 'red', 'low': 'dim'}))
        
        table.add_row("Физиология", phys_table)
        
        # Внешний вид при выворачивании
        if getattr(ovary, 'is_everted', False):
            desc = getattr(ovary, 'external_description', '')
            table.add_row("⚠️ Виден", f"[red]{desc[:50]}...[/red]" if len(str(desc)) > 50 else f"[red]{desc}[/red]")
        
        border_color = 'red' if getattr(ovary, 'is_everted', False) else color
        panel_title = title or f"{side_emoji} {side.capitalize()} Ovary"
        
        return Panel(
            table,
            title=f"[bold]{emoji} {panel_title}[/bold]",
            box=box.ROUNDED,
            border_style=border_color,
            padding=(1, 2)
        )
    
    # ======================
    # TUBE DETAILED RENDER
    # ======================
    
    def render_tube_detailed(self, tube, title: Optional[str] = None) -> Panel:
        """Детальный рендер фаллопиевой трубы."""
        if tube is None:
            return Panel("[dim]Труба отсутствует[/dim]", 
                        title="Труба", box=box.ROUNDED, border_style="dim")
        
        state = getattr(tube, 'state', None)
        emoji, color, state_name = self._get_tube_state_style(state)
        side = getattr(tube, 'side', 'unknown')
        side_emoji = self.SIDE_EMOJIS.get(side, '⚪')
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Param", style="cyan", width=12)
        table.add_column("Value", style="white")
        
        table.add_row("Состояние", f"[{color}]{emoji} {state_name}[/{color}]")
        
        # Размеры
        base_length = getattr(tube, 'length', 10.0)
        current_length = getattr(tube, 'current_length', base_length)
        stretch = getattr(tube, 'current_stretch', 1.0)
        diameter = getattr(tube, 'diameter', 0.3)
        
        table.add_row("Длина", f"{current_length:.1f}cm / {base_length:.1f}cm база")
        table.add_row("Диаметр", f"{diameter:.1f}cm")
        
        if stretch > 1.0:
            table.add_row(f"Растяжение ×{stretch:.1f}", self._bar(min(stretch/3.0, 1.0)))
        
        # Отверстия
        uterine_opening = getattr(tube, 'uterine_opening', 0.1)
        ovarian_opening = getattr(tube, 'ovarian_opening', 0.5)
        opening_visible = getattr(tube, 'uterine_opening_visible', False)
        
        opening_text = f"Маточный: Ø{uterine_opening:.1f}cm"
        if opening_visible:
            opening_text += " [red]👁️ ВИДНО![/red]"
        opening_text += f"\\nЯичниковый: Ø{ovarian_opening:.1f}cm"
        
        table.add_row("Отверстия", opening_text)
        
        # Содержимое
        fluid = getattr(tube, 'contained_fluid', 0.0)
        ovum = getattr(tube, 'contained_ovum', None)
        if fluid > 0 or ovum:
            content = []
            if fluid > 0:
                content.append(f"💧 {fluid:.1f}ml")
            if ovum:
                content.append("🥚 Яйцеклетка")
            table.add_row("Содержимое", " | ".join(content))
        
        # Связь с яичником
        ovary = getattr(tube, 'ovary', None)
        if ovary:
            ovary_state = getattr(ovary, 'state', None)
            ovary_emoji, ovary_color, ovary_name = self._get_ovary_state_style(ovary_state)
            ovary_text = f"[{ovary_color}]{ovary_emoji} {ovary_name}[/{ovary_color}]"
            
            can_prolapse = getattr(tube, 'can_prolapse_ovary', False)
            if can_prolapse:
                ovary_text += "\\n[yellow]⚠️ Риск выпадения[/yellow]"
            
            table.add_row("Яичник", ovary_text)
        
        # Эластичность
        elasticity = getattr(tube, 'elasticity', 1.0)
        max_stretch = getattr(tube, 'max_stretch_ratio', 3.0)
        table.add_row("Эластичность", f"{self._bar(elasticity)} (макс ×{max_stretch:.1f})")
        
        border_color = 'red' if 'EVERTED' in str(state) else color
        panel_title = title or f"{side_emoji} {side.capitalize()} Tube"
        
        return Panel(
            table,
            title=f"[bold]{emoji} {panel_title}[/bold]",
            box=box.ROUNDED,
            border_style=border_color,
            padding=(1, 2)
        )
    
    # ======================
    # COMBINED SYSTEM RENDER
    # ======================
    
    def render_full_system(self, system, title: str = "Система матки", 
                          show_accessories: bool = True) -> Panel:
        """
        Полный рендер системы матки с придатками.
        
        Args:
            system: UterusSystem или объект с .uteri
            title: Заголовок панели
            show_accessories: Показывать ли трубы и яичники
        """
        uteri = getattr(system, 'uteri', [])
        
        if not uteri:
            return Panel("[dim]Матка отсутствует[/dim]", title=title, box=box.ROUNDED)
        
        if len(uteri) == 1:
            uterus = uteri[0]
            
            # Основная матка
            uterus_panel = self.render_uterus_detailed(uterus, "Матка")
            
            if not show_accessories:
                return uterus_panel
            
            # Трубы и яичники
            tubes = getattr(uterus, 'tubes', [])
            ovaries = getattr(uterus, 'ovaries', [])
            
            if tubes or ovaries:
                # Создаем панели для придатков
                accessory_panels = []
                
                # Группируем по сторонам
                for side in ['left', 'right']:
                    tube = next((t for t in tubes if getattr(t, 'side', '') == side), None)
                    ovary = next((o for o in ovaries if getattr(o, 'side', '') == side), None)
                    
                    if tube or ovary:
                        # Компактный рендер для боковой панели
                        side_panels = []
                        if tube:
                            side_panels.append(self.render_tube_detailed(tube))
                        if ovary:
                            side_panels.append(self.render_ovary_detailed(ovary))
                        
                        if len(side_panels) == 2:
                            # Объединяем трубу и яичник вертикально
                            combined = Table(box=None, show_header=False)
                            combined.add_row(side_panels[0])
                            combined.add_row(side_panels[1])
                            accessory_panels.append(combined)
                        else:
                            accessory_panels.append(side_panels[0])
                
                # Компоновка: матка слева, придатки справа
                layout = Table(box=None, show_header=False)
                layout.add_column("Main", ratio=2)
                layout.add_column("Accessories", ratio=3)
                
                accessories = Columns(accessory_panels, equal=True) if len(accessory_panels) > 1 else accessory_panels[0] if accessory_panels else Text("")
                layout.add_row(uterus_panel, accessories)
                
                content = layout
            else:
                content = uterus_panel
            
            # Проверяем критические состояния
            has_critical = (
                getattr(uterus, 'is_everted', False) or
                any(getattr(o, 'is_everted', False) for o in ovaries) or
                any('EVERTED' in str(getattr(t, 'state', '')) for t in tubes)
            )
            
            return Panel(
                content,
                title=f"[bold magenta]🌸 {title}[/bold magenta]",
                box=box.DOUBLE,
                border_style="red" if has_critical else "bright_magenta",
                padding=(1, 2)
            )
        
        # Множественные матки
        uterus_panels = []
        for i, uterus in enumerate(uteri):
            panel = self.render_uterus_detailed(uterus, f"Матка {i+1}")
            
            if show_accessories:
                tubes = getattr(uterus, 'tubes', [])
                ovaries = getattr(uterus, 'ovaries', [])
                
                if tubes or ovaries:
                    accessory_cols = []
                    for tube in tubes:
                        if tube:
                            accessory_cols.append(self.render_tube_detailed(tube))
                    for ovary in ovaries:
                        if ovary:
                            accessory_cols.append(self.render_ovary_detailed(ovary))
                    
                    if accessory_cols:
                        combined = Table(box=None, show_header=False)
                        combined.add_row(panel)
                        combined.add_row(Columns(accessory_cols, equal=True))
                        uterus_panels.append(combined)
                    else:
                        uterus_panels.append(panel)
                else:
                    uterus_panels.append(panel)
            else:
                uterus_panels.append(panel)
        
        return Panel(
            Columns(uterus_panels, equal=True),
            title=f"[bold magenta]🌸 {title} (×{len(uteri)})[/bold magenta]",
            box=box.DOUBLE,
            border_style="bright_magenta",
            padding=(1, 2)
        )
    
    def render_tree_view(self, system) -> Tree:
        """Древовидное представление системы."""
        root = Tree("🌸 [bold magenta]Система матки[/bold magenta]")
        
        uteri = getattr(system, 'uteri', [])
        for i, uterus in enumerate(uteri):
            state = getattr(uterus, 'state', None)
            emoji, color, desc = self._get_state_style(state)
            volume = getattr(uterus, 'current_volume', 0) or 0
            
            u_label = f"[{color}]{emoji} Матка {i+1}: {desc}[/{color}] "
            u_label += f"({self._format_volume(volume)})"
            
            is_everted = getattr(uterus, 'is_everted', False)
            if is_everted:
                u_label += " [bold red]⚠️ ВЫВОРОТ[/bold red]"
            
            u_node = root.add(u_label)
            
            # Шейка
            cervix = getattr(uterus, 'cervix', None)
            if cervix:
                c_state = getattr(cervix, 'state', None)
                c_emoji, c_color, c_desc = self._get_state_style(c_state)
                dilation = getattr(cervix, 'current_dilation', 0) or 0
                u_node.add(f"[{c_color}]{c_emoji} Шейка: {c_desc}, Ø{dilation:.1f}cm[/{c_color}]")
            
            # Трубы и яичники
            tubes = getattr(uterus, 'tubes', [])
            for tube in tubes:
                if not tube:
                    continue
                side = getattr(tube, 'side', '?')
                t_state = getattr(tube, 'state', None)
                t_emoji, t_color = self.TUBE_STATE_STYLES.get(getattr(t_state, 'name', 'Unknown'), ('⚪', 'dim'))
                t_stretch = getattr(tube, 'current_stretch', 1.0)
                
                t_label = f"[{t_color}]{t_emoji} Труба ({side}): ×{t_stretch:.1f}[/{t_color}]"
                
                opening = getattr(tube, 'uterine_opening_visible', False)
                if opening:
                    t_label += " [red]👁️ Видна![/red]"
                
                t_node = u_node.add(t_label)
                
                # Яичник
                ovary = getattr(tube, 'ovary', None)
                if ovary:
                    o_state = getattr(ovary, 'state', None)
                    o_emoji, o_color = self.OVARY_STATE_STYLES.get(getattr(o_state, 'name', 'Unknown'), ('⚪', 'dim'))
                    o_volume = ovary.calculate_volume() if hasattr(ovary, 'calculate_volume') else 0
                    
                    o_label = f"[{o_color}]{o_emoji} Яичник: {o_volume:.1f}ml[/{o_color}]"
                    
                    if getattr(ovary, 'is_everted', False):
                        o_label += " [bold red]⚠️ ВЫВЕРНУТ[/bold red]"
                    
                    t_node.add(o_label)
        
        return root
    
    def render_compact(self, system) -> Text:
        """Ультракомпактный рендер для статусной строки."""
        uteri = getattr(system, 'uteri', [])
        if not uteri:
            return Text("🌸 [dim]Н/Д[/dim]")
        
        parts = []
        for uterus in uteri:
            state = getattr(uterus, 'state', None)
            emoji, color, _ = self._get_state_style(state)
            volume = getattr(uterus, 'current_volume', 0) or 0
            
            part = f"[{color}]{emoji}[/{color}]"
            if getattr(uterus, 'is_everted', False):
                part += "[red]![/red]"
            parts.append(part)
            
            # Добавляем статус яичников компактно
            ovaries = getattr(uterus, 'ovaries', [])
            for ovary in ovaries:
                if ovary and getattr(ovary, 'is_everted', False):
                    parts.append("[red]⚠️O[/red]")
        
        return Text.from_markup(f"🌸 {' '.join(parts)}")
    
    def print(self, renderable: RenderableType):
        """Вывести в консоль."""
        self.console.print(renderable)

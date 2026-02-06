# body_sim/ui/ovary_tube_render.py
"""
Детальный Rich-рендеринг для яичников (ovaries) и фаллопиевых труб (fallopian tubes).
Визуализация фолликулов, состояний пролапса и физиологических параметров.
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


class OvaryTubeRenderer:
    """Детальный рендерер яичников и фаллопиевых труб."""
    
    COLORS = {
        'normal': 'green',
        'healthy': 'bright_green',
        'warning': 'yellow',
        'danger': 'red',
        'critical': 'bright_red',
        'info': 'cyan',
        'muted': 'dim',
        'magic': 'magenta',
        'hormone': 'bright_yellow',
        'blood': 'bright_red',
        'follicle': 'bright_cyan',
    }
    
    # Состояния яичника
    OVARY_STATE_STYLES = {
        'NORMAL': ('🟢', 'green', 'Норма', 'Здоровый'),
        'ENLARGED': ('🟡', 'yellow', 'Увеличен', 'Фолликулы увеличены'),
        'PROLAPSED': ('🟠', 'bright_red', 'Пролапс', 'Частично выпал'),
        'EVERTED': ('🔴', 'red', 'ВЫВОРОТ', 'ПОЛНОСТЬЮ ВЫВЕРНУТ'),
        'TORSION': ('⛔', 'bright_red', 'Перекрут', 'Ишемия! КРИТИЧЕСКИ!'),
    }
    
    # Состояния фаллопиевой трубы
    TUBE_STATE_STYLES = {
        'NORMAL': ('🟢', 'green', 'Норма', 'Проходима'),
        'DILATED': ('🟡', 'yellow', 'Расширена', 'Растянута'),
        'BLOCKED': ('⛔', 'red', 'Заблокирована', 'Не проходима!'),
        'PROLAPSED': ('🟠', 'bright_red', 'Пролапс', 'Выпала из матки'),
        'EVERTED_WITH_OVARY': ('🔴', 'red', 'ВЫВОРОТ', 'Яичник вывернут!'),
    }
    
    # Эмодзи для сторон
    SIDE_EMOJIS = {
        'left': '🌙',
        'right': '☀️',
        'unknown': '⚪'
    }
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def _get_ovary_state_style(self, state) -> Tuple[str, str, str, str]:
        """Получить стиль для состояния яичника."""
        if state is None:
            return ('⚪', 'dim', 'None', 'Неизвестно')
        state_name = getattr(state, 'name', str(state))
        return self.OVARY_STATE_STYLES.get(state_name, ('⚪', 'dim', state_name, ''))
    
    def _get_tube_state_style(self, state) -> Tuple[str, str, str, str]:
        """Получить стиль для состояния трубы."""
        if state is None:
            return ('⚪', 'dim', 'None', 'Неизвестно')
        state_name = getattr(state, 'name', str(state))
        return self.TUBE_STATE_STYLES.get(state_name, ('⚪', 'dim', state_name, ''))
    
    def _bar(self, value: float, width: int = 8, 
             color_map: Dict[str, str] = None,
             show_value: bool = True) -> Text:
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
        if show_value:
            bar_text += f" {value:.0%}"
        
        return Text.from_markup(f"[{color}]{bar_text}[/{color}]")
    
    def _gradient_bar(self, value: float, width: int = 10) -> str:
        """Визуальный градиентный бар с цветами."""
        value = max(0.0, min(1.0, value))
        filled = int(value * width)
        
        # Градиент от красного к зеленому
        if value < 0.3:
            color = 'red'
        elif value < 0.6:
            color = 'yellow'
        else:
            color = 'green'
        
        return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/{color}]"
    
    def _render_follicles_visual(self, sizes: List[float], max_display: int = 8) -> str:
        """Визуализация фолликулов как набор кругов разного размера."""
        if not sizes:
            return "[dim]Нет фолликулов[/dim]"
        
        visual_parts = []
        for i, size in enumerate(sizes[:max_display]):
            # Размер круга зависит от размера фолликула
            if size < 0.3:
                emoji = "•"
                color = "dim"
            elif size < 0.8:
                emoji = "○"
                color = "cyan"
            elif size < 1.5:
                emoji = "◐"
                color = "bright_cyan"
            else:
                emoji = "●"
                color = "bright_yellow"  # Доминантный фолликул
            
            visual_parts.append(f"[{color}]{emoji}[/{color}]")
        
        if len(sizes) > max_display:
            visual_parts.append(f"[dim]+{len(sizes) - max_display}[/dim]")
        
        return " ".join(visual_parts)
    
    def _render_size_comparison(self, current: float, base: float, label: str) -> str:
        """Сравнение текущего и базового размера."""
        ratio = current / base if base > 0 else 1.0
        if ratio > 1.5:
            color = 'red'
            indicator = '↑↑'
        elif ratio > 1.2:
            color = 'yellow'
            indicator = '↑'
        elif ratio < 0.8:
            color = 'blue'
            indicator = '↓'
        else:
            color = 'green'
            indicator = '→'
        
        return f"[{color}]{current:.1f}cm {indicator} ({base:.1f}cm)[/{color}]"
    
    # ======================
    # OVARY DETAILED RENDER
    # ======================
    
    def render_ovary_detailed(self, ovary, title: Optional[str] = None) -> Panel:
        """
        Детальный рендер яичника с полной визуализацией.
        """
        if ovary is None:
            return Panel("[dim]Яичник отсутствует[/dim]", 
                        title="Яичник", box=box.ROUNDED, border_style="dim")
        
        # Получаем состояние
        state = getattr(ovary, 'state', None)
        emoji, color, state_name, state_desc = self._get_ovary_state_style(state)
        side = getattr(ovary, 'side', 'unknown')
        side_emoji = self.SIDE_EMOJIS.get(side, '⚪')
        
        # Основная таблица
        main_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        main_table.add_column("Param", style="cyan", width=14)
        main_table.add_column("Value", style="white")
        
        # Заголовок состояния
        main_table.add_row(
            "Состояние", 
            f"[{color}]{emoji} {state_name}[/{color}]\\n[dim]{state_desc}[/dim]"
        )
        
        # Размеры
        length = getattr(ovary, 'length', 3.0)
        width = getattr(ovary, 'width', 2.0)
        thickness = getattr(ovary, 'thickness', 1.5)
        volume = ovary.calculate_volume() if hasattr(ovary, 'calculate_volume') else (length * width * thickness * 0.8)
        
        size_text = f"{length}×{width}×{thickness} cm"
        main_table.add_row("Размеры", f"[bright_white]{size_text}[/bright_white]")
        main_table.add_row("Объём", f"[cyan]{volume:.1f} ml[/cyan]")
        
        # Пролапс/выворачивание
        prolapse = getattr(ovary, 'prolapse_degree', 0.0)
        if prolapse > 0 or state_name in ['Пролапс', 'ВЫВОРОТ']:
            prolapse_bar = self._bar(prolapse, width=10, 
                                    color_map={'high': 'red', 'medium': 'yellow', 'low': 'green'})
            main_table.add_row("Степень выпадения", prolapse_bar)
            
            if getattr(ovary, 'visible_externally', False):
                main_table.add_row(
                    "⚠️ Видимость", 
                    "[bold red]ВИДЕН СНАРУЖИ![/bold red]"
                )
        
        # Фолликулы - детальная визуализация
        follicles = getattr(ovary, 'follicle_count', 5)
        follicle_sizes = getattr(ovary, 'follicle_sizes', [0.5] * 5)
        
        if follicle_sizes:
            avg_size = sum(follicle_sizes) / len(follicle_sizes)
            max_size = max(follicle_sizes) if follicle_sizes else 0
            
            # Визуализация фолликулов
            follicle_viz = self._render_follicles_visual(follicle_sizes)
            
            follicle_table = Table(box=None, show_header=False, padding=(0, 0))
            follicle_table.add_column("Info", width=20)
            follicle_table.add_column("Visual")
            
            follicle_table.add_row(
                f"[cyan]Количество:[/cyan] {follicles}\\n"
                f"[cyan]Средний:[/cyan] {avg_size:.1f}cm\\n"
                f"[cyan]Максимальный:[/cyan] {max_size:.1f}cm",
                follicle_viz
            )
            
            main_table.add_row("Фолликулы", follicle_table)
            
            # Статус овуляции
            if max_size > 1.5:
                main_table.add_row(
                    "🥚 Овуляция", 
                    "[bright_yellow]Готов к овуляции (доминантный фолликул)[/bright_yellow]"
                )
        
        # Разорванные фолликулы
        ruptured = getattr(ovary, 'ruptured_follicles', 0)
        if ruptured > 0:
            main_table.add_row(
                "Разорваны", 
                f"[yellow]{ruptured} фолликулов разорваны[/yellow]"
            )
        
        # Физиология
        phys_table = Table(box=None, show_header=False, padding=(0, 2))
        phys_table.add_column("Stat", width=12)
        phys_table.add_column("Bar", width=12)
        phys_table.add_column("Status", width=10)
        
        hormones = getattr(ovary, 'hormone_production', 1.0)
        blood = getattr(ovary, 'blood_supply', 1.0)
        
        # Гормоны
        hormone_color = 'bright_yellow' if hormones > 0.7 else 'yellow' if hormones > 0.4 else 'red'
        phys_table.add_row(
            "[yellow]Гормоны[/yellow]",
            self._bar(hormones, width=8),
            f"[{hormone_color}]{hormones:.0%}[/{hormone_color}]"
        )
        
        # Кровоснабжение
        blood_status = "Норма" if blood > 0.7 else "Снижено" if blood > 0.4 else "[red]ИШЕМИЯ![/red]"
        phys_table.add_row(
            "[red]Кровь[/red]",
            self._bar(blood, width=8, color_map={'high': 'bright_red', 'medium': 'red', 'low': 'dim'}),
            blood_status
        )
        
        main_table.add_row("Физиология", phys_table)
        
        # При выворачивании - внешний вид
        if getattr(ovary, 'is_everted', False):
            desc = getattr(ovary, 'external_description', '')
            if desc:
                main_table.add_row(
                    "👁️ Описание",
                    f"[red]{desc}[/red]"
                )
        
        # Определяем цвет границы
        border_color = 'red' if getattr(ovary, 'is_everted', False) else color
        panel_title = title or f"{side_emoji} {side.capitalize()} Ovary"
        
        return Panel(
            main_table,
            title=f"[bold]{emoji} {panel_title}[/bold]",
            box=box.ROUNDED,
            border_style=border_color,
            padding=(1, 2)
        )
    
    # ======================
    # TUBE DETAILED RENDER
    # ======================
    
    def render_tube_detailed(self, tube, title: Optional[str] = None) -> Panel:
        """
        Детальный рендер фаллопиевой трубы.
        """
        if tube is None:
            return Panel("[dim]Труба отсутствует[/dim]", 
                        title="Труба", box=box.ROUNDED, border_style="dim")
        
        # Состояние
        state = getattr(tube, 'state', None)
        emoji, color, state_name, state_desc = self._get_tube_state_style(state)
        side = getattr(tube, 'side', 'unknown')
        side_emoji = self.SIDE_EMOJIS.get(side, '⚪')
        
        # Основная таблица
        main_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        main_table.add_column("Param", style="cyan", width=14)
        main_table.add_column("Value", style="white")
        
        # Заголовок состояния
        main_table.add_row(
            "Состояние",
            f"[{color}]{emoji} {state_name}[/{color}]\\n[dim]{state_desc}[/dim]"
        )
        
        # Размеры
        base_length = getattr(tube, 'length', 10.0)
        current_length = getattr(tube, 'current_length', base_length)
        diameter = getattr(tube, 'diameter', 0.3)
        stretch = getattr(tube, 'current_stretch', 1.0)
        
        main_table.add_row(
            "Длина",
            self._render_size_comparison(current_length, base_length, "длина")
        )
        main_table.add_row("Диаметр", f"{diameter:.1f} cm")
        
        # Растяжение
        if stretch > 1.0:
            stretch_bar = self._bar(
                min(stretch / 3.0, 1.0),  # Нормализуем к 3x максимуму
                width=10,
                color_map={'high': 'red', 'medium': 'yellow', 'low': 'green'}
            )
            main_table.add_row(f"Растяжение ×{stretch:.1f}", stretch_bar)
            
            if stretch > 2.0:
                main_table.add_row(
                    "⚠️ Риск",
                    "[yellow]Высокий риск повреждения[/yellow]"
                )
        
        # Отверстия
        openings_table = Table(box=None, show_header=False, padding=(0, 1))
        openings_table.add_column("End", width=10)
        openings_table.add_column("Size", width=8)
        openings_table.add_column("Status")
        
        uterine_opening = getattr(tube, 'uterine_opening', 0.1)
        ovarian_opening = getattr(tube, 'ovarian_opening', 0.5)
        
        # Проверяем видимость отверстия в матке
        opening_visible = getattr(tube, 'uterine_opening_visible', False)
        uterine_status = "[red]👁️ ВИДНО![/red]" if opening_visible else "[dim]Внутри[/dim]"
        
        openings_table.add_row("Маточный", f"Ø{uterine_opening:.1f}cm", uterine_status)
        openings_table.add_row("Яичниковый", f"Ø{ovarian_opening:.1f}cm", "[dim]Фимбрии[/dim]")
        
        main_table.add_row("Отверстия", openings_table)
        
        # Содержимое
        fluid = getattr(tube, 'contained_fluid', 0.0)
        ovum = getattr(tube, 'contained_ovum', None)
        
        if fluid > 0 or ovum:
            content_parts = []
            if fluid > 0:
                content_parts.append(f"💧 {fluid:.1f}ml жидкости")
            if ovum:
                content_parts.append("🥚 Яйцеклетка внутри!")
            main_table.add_row("Содержимое", "\\n".join(content_parts))
        
        # Связь с яичником
        ovary = getattr(tube, 'ovary', None)
        if ovary:
            ovary_state = getattr(ovary, 'state', None)
            ovary_emoji, ovary_color, ovary_name, _ = self._get_ovary_state_style(ovary_state)
            
            ovary_text = f"[{ovary_color}]{ovary_emoji} {ovary_name}[/{ovary_color}]"
            
            # Проверяем может ли яичник выпасть
            can_prolapse = getattr(tube, 'can_prolapse_ovary', False)
            if can_prolapse:
                ovary_text += "\\n[yellow]⚠️ Может выпасть![/yellow]"
            
            main_table.add_row("Яичник", ovary_text)
        
        # При выворачивании
        if state_name == 'ВЫВОРОТ':
            desc = getattr(tube, 'external_description', '')
            if desc:
                main_table.add_row(
                    "👁️ Внешний вид",
                    f"[red]{desc}[/red]"
                )
        
        # Эластичность
        elasticity = getattr(tube, 'elasticity', 1.0)
        max_stretch = getattr(tube, 'max_stretch_ratio', 3.0)
        
        elastic_bar = self._bar(elasticity, width=8)
        main_table.add_row(
            "Эластичность",
            f"{elastic_bar} (макс ×{max_stretch:.1f})"
        )
        
        border_color = 'red' if state_name == 'ВЫВОРОТ' else color
        panel_title = title or f"{side_emoji} {side.capitalize()} Tube"
        
        return Panel(
            main_table,
            title=f"[bold]{emoji} {panel_title}[/bold]",
            box=box.ROUNDED,
            border_style=border_color,
            padding=(1, 2)
        )
    
    # ======================
    # COMBINED RENDERS
    # ======================
    
    def render_side_pair(self, tube, ovary, compact: bool = False) -> RenderableType:
        """
        Рендер пары труба+яичник для одной стороны.
        """
        if compact:
            return self._render_side_compact(tube, ovary)
        
        tube_panel = self.render_tube_detailed(tube)
        ovary_panel = self.render_ovary_detailed(ovary)
        
        # Объединяем в горизонтальную группу
        return Columns([tube_panel, ovary_panel], equal=True, expand=True)
    
    def _render_side_compact(self, tube, ovary) -> Panel:
        """Компактный рендер пары."""
        side = getattr(tube, 'side', getattr(ovary, 'side', 'unknown'))
        side_emoji = self.SIDE_EMOJIS.get(side, '⚪')
        
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Organ", width=8)
        table.add_column("Status", width=12)
        table.add_column("Key Info")
        
        # Труба
        if tube:
            t_state = getattr(tube, 'state', None)
            t_emoji, t_color, t_name, _ = self._get_tube_state_style(t_state)
            t_stretch = getattr(tube, 'current_stretch', 1.0)
            
            t_info = f"×{t_stretch:.1f}"
            if getattr(tube, 'uterine_opening_visible', False):
                t_info += " [red]👁️[/red]"
            
            table.add_row(
                "Труба",
                f"[{t_color}]{t_emoji} {t_name[:8]}[/{t_color}]",
                t_info
            )
        
        # Яичник
        if ovary:
            o_state = getattr(ovary, 'state', None)
            o_emoji, o_color, o_name, _ = self._get_ovary_state_style(o_state)
            o_volume = ovary.calculate_volume() if hasattr(ovary, 'calculate_volume') else 0
            
            o_info = f"{o_volume:.1f}ml"
            if getattr(ovary, 'is_everted', False):
                o_info += " [red]ВЫВ![/red]"
            
            table.add_row(
                "Яичник",
                f"[{o_color}]{o_emoji} {o_name[:8]}[/{o_color}]",
                o_info
            )
        
        return Panel(
            table,
            title=f"[bold]{side_emoji} {side.capitalize()}[/bold]",
            box=box.SIMPLE,
            border_style="cyan"
        )
    
    def render_full_reproductive_pair(self, uterus, title: str = "Репродуктивная система") -> Panel:
        """
        Полный рендер всех труб и яичников для матки.
        """
        tubes = getattr(uterus, 'tubes', [])
        ovaries = getattr(uterus, 'ovaries', [])
        
        if not tubes and not ovaries:
            return Panel("[dim]Репродуктивные органы отсутствуют[/dim]", 
                        title=title, box=box.ROUNDED)
        
        # Создаем панели для каждой стороны
        side_panels = []
        
        # Левая сторона
        left_tube = next((t for t in tubes if getattr(t, 'side', '') == 'left'), None)
        left_ovary = next((o for o in ovaries if getattr(o, 'side', '') == 'left'), None)
        
        if left_tube or left_ovary:
            left_panel = self.render_side_pair(left_tube, left_ovary, compact=False)
            side_panels.append(left_panel)
        
        # Правая сторона
        right_tube = next((t for t in tubes if getattr(t, 'side', '') == 'right'), None)
        right_ovary = next((o for o in ovaries if getattr(o, 'side', '') == 'right'), None)
        
        if right_tube or right_ovary:
            right_panel = self.render_side_pair(right_tube, right_ovary, compact=False)
            side_panels.append(right_panel)
        
        # Компоновка
        if len(side_panels) == 2:
            # Обе стороны - горизонтально
            content = Columns(side_panels, equal=True, expand=True)
        else:
            content = side_panels[0] if side_panels else "[dim]Нет данных[/dim]"
        
        # Проверяем есть ли вывернутые органы
        has_everted = any(
            getattr(o, 'is_everted', False) for o in ovaries
        ) or any(
            getattr(t, 'state', None) and 'EVERTED' in str(getattr(t, 'state', '')) 
            for t in tubes
        )
        
        border_style = 'red' if has_everted else 'bright_magenta'
        
        return Panel(
            content,
            title=f"[bold magenta]🌸 {title}[/bold magenta]",
            box=box.DOUBLE,
            border_style=border_style,
            padding=(1, 2)
        )
    
    def render_tree_view(self, uterus) -> Tree:
        """Древовидное представление труб и яичников."""
        root = Tree("🌸 [bold magenta]Придатки матки[/bold magenta]")
        
        tubes = getattr(uterus, 'tubes', [])
        ovaries = getattr(uterus, 'ovaries', [])
        
        for tube in tubes:
            if not tube:
                continue
                
            side = getattr(tube, 'side', 'unknown')
            t_state = getattr(tube, 'state', None)
            t_emoji, t_color, t_name, _ = self._get_tube_state_style(t_state)
            t_stretch = getattr(tube, 'current_stretch', 1.0)
            
            t_label = f"[{t_color}]{t_emoji} Труба ({side})[/{t_color}] ×{t_stretch:.1f}"
            
            if getattr(tube, 'uterine_opening_visible', False):
                t_label += " [red]👁️ Видна![/red]"
            
            t_node = root.add(t_label)
            
            # Яичник к этой трубе
            ovary = getattr(tube, 'ovary', None)
            if ovary:
                o_state = getattr(ovary, 'state', None)
                o_emoji, o_color, o_name, _ = self._get_ovary_state_style(o_state)
                o_volume = ovary.calculate_volume() if hasattr(ovary, 'calculate_volume') else 0
                
                o_label = f"[{o_color}]{o_emoji} Яичник: {o_volume:.1f}ml[/{o_color}]"
                
                if getattr(ovary, 'is_everted', False):
                    o_label += " [bold red]⚠️ ВЫВЕРНУТ[/bold red]"
                
                # Фолликулы
                follicles = getattr(ovary, 'follicle_sizes', [])
                if follicles:
                    follicle_viz = self._render_follicles_visual(follicles, max_display=5)
                    o_label += f"\\n    [dim]Фолликулы:[/dim] {follicle_viz}"
                
                t_node.add(o_label)
        
        return root
    
    def render_compact_status(self, uterus) -> Text:
        """Ультракомпактный статус для строки состояния."""
        ovaries = getattr(uterus, 'ovaries', [])
        tubes = getattr(uterus, 'tubes', [])
        
        parts = []
        
        # Яичники
        for ovary in ovaries:
            if not ovary:
                continue
            o_state = getattr(ovary, 'state', None)
            o_emoji, o_color, _, _ = self._get_ovary_state_style(o_state)
            
            part = f"[{o_color}]{o_emoji}[/{o_color}]"
            if getattr(ovary, 'is_everted', False):
                part += "[red]![/red]"
            parts.append(part)
        
        # Трубы
        for tube in tubes:
            if not tube:
                continue
            t_state = getattr(tube, 'state', None)
            t_emoji, t_color, _, _ = self._get_tube_state_style(t_state)
            
            part = f"[{t_color}]{t_emoji}[/{t_color}]"
            if getattr(tube, 'uterine_opening_visible', False):
                part += "[red]👁️[/red]"
            parts.append(part)
        
        return Text.from_markup(f"🌸 {' '.join(parts)}")
    
    def print(self, renderable: RenderableType):
        """Вывести в консоль."""
        self.console.print(renderable)


# ======================
# COMPATIBILITY EXPORTS
# ======================

def render_ovary_detailed(ovary, title: Optional[str] = None) -> Panel:
    """Функция-обёртка для детального рендера яичника."""
    renderer = OvaryTubeRenderer()
    return renderer.render_ovary_detailed(ovary, title)


def render_tube_detailed(tube, title: Optional[str] = None) -> Panel:
    """Функция-обёртка для детального рендера трубы."""
    renderer = OvaryTubeRenderer()
    return renderer.render_tube_detailed(tube, title)


def render_reproductive_system(uterus, title: str = "Репродуктивная система") -> Panel:
    """Функция-обёртка для полного рендера системы."""
    renderer = OvaryTubeRenderer()
    return renderer.render_full_reproductive_pair(uterus, title)

# body_sim/ui/uterus_render.py
"""
Улучшенный Rich-рендеринг системы матки с детальной визуализацией пролапса
и цветовой индикацией состояний.
"""

from typing import Optional, List, Dict, Any
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
    """Улучшенный рендерер системы матки с визуализацией пролапса."""
    
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
    INFLATION_STYLES = {
        'NORMAL': ('✓', 'green', 'Норма'),
        'STRETCHED': ('~', 'yellow', 'Растянута'),
        'DISTENDED': ('⚠', 'bright_red', 'Выпучена'),
        'HYPERDISTENDED': ('🔥', 'red', 'Гипер'),
        'RUPTURE_RISK': ('💀', 'red', 'Риск разрыва'),
        'RUPTURED': ('💥', 'bright_red', 'РАЗОРВАНА'),
    }

    
    OVARY_STATES = {
        'NORMAL': ('🟢', 'green'),
        'ENLARGED': ('🟡', 'yellow'),
        'PROLAPSED': ('🟠', 'bright_red'),
        'EVERTED': ('🔴', 'red'),
        'TORSION': ('⛔', 'bright_red'),
    }
    
    TUBE_STATES = {
        'NORMAL': ('🟢', 'green'),
        'DILATED': ('🟡', 'yellow'),
        'BLOCKED': ('⛔', 'red'),
        'PROLAPSED': ('🟠', 'bright_red'),
        'EVERTED_WITH_OVARY': ('🔴', 'red'),
    }
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def _get_state_style(self, state) -> tuple:
        """Получить стиль для состояния."""
        if state is None:
            return ('⚪', 'dim', 'None')
        state_name = getattr(state, 'name', str(state))
        return self.STATE_STYLES.get(state_name, ('⚪', 'dim', state_name))
    
    def _get_inflation_style(self, status) -> tuple:
        """Получить стиль для инфляции."""
        if status is None:
            return ('✓', 'green', 'Норма')
        status_name = getattr(status, 'name', str(status))
        return self.INFLATION_STYLES.get(status_name, ('?', 'white', status_name))

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
            table.add_row("Содержимое", "\n".join(fill_info))
        
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
                f"[bold red]ПОЛНЫЙ ВЫВОРОТ![/bold red]\n"
                f"Внешний объём: {self._format_volume(everted_volume)}\n"
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
        
        # Нормальное положение [🟢🟢🟢⚪⚪⚪⚪⚪⚪⚪]
        # Пролапс        [🟢🟢🟡🟡🟠🟠🔴🔴🔴🔴]
        # Выворот        [🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴]
        
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
    
    def render_ovary_detailed(self, ovary, compact: bool = False) -> Panel:
        """Детальный рендер яичника."""
        if ovary is None:
            return Panel("[dim]Н/Д[/dim]", title="Яичник", box=box.SIMPLE)
        
        state = getattr(ovary, 'state', None)
        state_name = getattr(state, 'name', 'Unknown')
        emoji, color = self.OVARY_STATES.get(state_name, ('⚪', 'dim'))
        
        side = getattr(ovary, 'side', 'unknown')
        side_emoji = "🌙" if side == "left" else "☀️" if side == "right" else "⚪"
        
        # Размеры
        length = getattr(ovary, 'length', 3.0)
        width = getattr(ovary, 'width', 2.0)
        thickness = getattr(ovary, 'thickness', 1.5)
        volume = ovary.calculate_volume() if hasattr(ovary, 'calculate_volume') else (length * width * thickness * 0.8)
        
        # Фолликулы
        follicles = getattr(ovary, 'follicle_count', 5)
        follicle_sizes = getattr(ovary, 'follicle_sizes', [0.5] * 5)
        avg_follicle = sum(follicle_sizes) / len(follicle_sizes) if follicle_sizes else 0
        
        # Пролапс
        prolapse = getattr(ovary, 'prolapse_degree', 0.0)
        is_everted = getattr(ovary, 'is_everted', False)
        visible = getattr(ovary, 'visible_externally', False)
        
        if compact:
            content = f"{emoji} {state_name[:4]} | {volume:.1f}ml"
            if is_everted:
                content += " [red]ВЫВОРОТ![/red]"
            return Panel(content, title=f"{side_emoji} {side[:1].upper()}", box=box.SIMPLE, border_style=color)
        
        # Детальный вид
        table = Table(box=None, show_header=False)
        table.add_column("Param", style="cyan")
        table.add_column("Value")
        
        table.add_row("Состояние", f"[{color}]{emoji} {state_name}[/{color}]")
        table.add_row("Размер", f"{length}×{width}×{thickness}cm")
        table.add_row("Объём", f"{volume:.1f}ml")
        table.add_row("Фолликулы", f"{follicles} шт, ~{avg_follicle:.1f}cm")
        
        if prolapse > 0:
            table.add_row("Пролапс", self._bar(prolapse, width=6))
        
        if is_everted:
            desc = getattr(ovary, 'external_description', '')
            table.add_row("⚠️ Виден снаружи", f"[red]{desc}[/red]" if desc else "[red]ПОЛНЫЙ ВЫВОРОТ[/red]")
        
        # Физиология
        hormones = getattr(ovary, 'hormone_production', 1.0)
        blood = getattr(ovary, 'blood_supply', 1.0)
        table.add_row("Гормоны", self._bar(hormones))
        table.add_row("Кровоснабжение", self._bar(blood))
        
        return Panel(
            table,
            title=f"[bold]{side_emoji} {side.capitalize()} Ovary[/bold]",
            box=box.ROUNDED,
            border_style='red' if is_everted else color
        )
    
    def render_tube_detailed(self, tube, compact: bool = False) -> Panel:
        """Детальный рендер фаллопиевой трубы."""
        if tube is None:
            return Panel("[dim]Н/Д[/dim]", title="Труба", box=box.SIMPLE)
        
        state = getattr(tube, 'state', None)
        state_name = getattr(state, 'name', 'Unknown')
        emoji, color = self.TUBE_STATES.get(state_name, ('⚪', 'dim'))
        
        side = getattr(tube, 'side', 'unknown')
        side_emoji = "🌙" if side == "left" else "☀️" if side == "right" else "⚪"
        
        length = getattr(tube, 'current_length', 10.0)
        base_length = getattr(tube, 'length', 10.0)
        stretch = getattr(tube, 'current_stretch', 1.0)
        diameter = getattr(tube, 'diameter', 0.3)
        
        # Содержимое
        fluid = getattr(tube, 'contained_fluid', 0.0)
        ovum = getattr(tube, 'contained_ovum', None)
        
        # Связь с яичником
        ovary = getattr(tube, 'ovary', None)
        can_prolapse = getattr(tube, 'can_prolapse_ovary', False)
        opening_visible = getattr(tube, 'uterine_opening_visible', False)
        
        if compact:
            content = f"{emoji} {state_name[:4]} | ×{stretch:.1f}"
            if opening_visible:
                content += " [red]👁️[/red]"
            return Panel(content, title=f"{side_emoji} {side[:1].upper()}", box=box.SIMPLE, border_style=color)
        
        table = Table(box=None, show_header=False)
        table.add_column("Param", style="cyan")
        table.add_column("Value")
        
        table.add_row("Состояние", f"[{color}]{emoji} {state_name}[/{color}]")
        table.add_row("Длина", f"{length:.1f}cm / {base_length:.1f}cm база")
        table.add_row("Растяжение", f"[yellow]×{stretch:.1f}[/yellow]" if stretch > 1.5 else f"×{stretch:.1f}")
        table.add_row("Диаметр", f"{diameter:.1f}cm")
        
        if fluid > 0:
            table.add_row("Жидкость", f"{fluid:.1f}ml")
        if ovum:
            table.add_row("Яйцеклетка", "🥚 Присутствует")
        
        if opening_visible:
            desc = getattr(tube, 'external_description', '')
            table.add_row("⚠️ Отверстие видно", f"[red]{desc}[/red]" if desc else "[red]Видно при инверсии![/red]")
        
        if can_prolapse and ovary:
            table.add_row("⚠️ Риск", "[yellow]Яичник может выпасть![/yellow]")
        
        return Panel(
            table,
            title=f"[bold]{side_emoji} {side.capitalize()} Tube[/bold]",
            box=box.ROUNDED,
            border_style=color
        )
    
    def render_full_system(self, system, title: str = "Система матки") -> Panel:
        """Полный рендер системы матки."""
        uteri = getattr(system, 'uteri', [])
        
        if not uteri:
            return Panel("[dim]Матка отсутствует[/dim]", title=title, box=box.ROUNDED)
        
        if len(uteri) == 1:
            uterus = uteri[0]
            
            # Основная матка
            uterus_panel = self.render_uterus_detailed(uterus, "Матка")
            
            # Трубы и яичники
            tubes = getattr(uterus, 'tubes', [])
            ovaries = getattr(uterus, 'ovaries', [])
            
            accessory_panels = []
            
            if tubes:
                for tube in tubes:
                    tube_panel = self.render_tube_detailed(tube, compact=True)
                    ovary = getattr(tube, 'ovary', None)
                    if ovary:
                        ovary_panel = self.render_ovary_detailed(ovary, compact=True)
                        # Объединяем трубу и яичник
                        combined = Table(box=None, show_header=False)
                        combined.add_row(tube_panel)
                        combined.add_row(ovary_panel)
                        accessory_panels.append(combined)
                    else:
                        accessory_panels.append(tube_panel)
            
            # Компоновка
            layout = Table(box=None, show_header=False)
            layout.add_column("Main")
            layout.add_column("Accessories")
            
            accessories = Columns(accessory_panels, equal=True) if accessory_panels else Text("")
            layout.add_row(uterus_panel, accessories)
            
            return Panel(
                layout,
                title=f"[bold magenta]🌸 {title}[/bold magenta]",
                box=box.DOUBLE,
                border_style="bright_magenta",
                padding=(1, 2)
            )
        
        # Множественные матки (фантастика)
        uterus_panels = []
        for i, uterus in enumerate(uteri):
            panel = self.render_uterus_detailed(uterus, f"Матка {i+1}")
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
                side = getattr(tube, 'side', '?')
                t_state = getattr(tube, 'state', None)
                t_emoji, t_color = self.TUBE_STATES.get(getattr(t_state, 'name', 'Unknown'), ('⚪', 'dim'))
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
                    o_emoji, o_color = self.OVARY_STATES.get(getattr(o_state, 'name', 'Unknown'), ('⚪', 'dim'))
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
        
        return Text.from_markup(f"🌸 {' '.join(parts)}")
    
    def print(self, renderable: RenderableType):
        """Вывести в консоль."""
        self.console.print(renderable)


    # ============ НОВЫЙ МЕТОД ДЛЯ ОТОБРАЖЕНИЯ ЗАПОЛНЕНИЯ ============

    def _create_fluid_bar(self, current: float, max_val: float, width: int = 20) -> str:
        """Создать визуальный индикатор заполнения."""
        if max_val <= 0:
            return "[dim]" + "░" * width + "[/dim]"

        ratio = min(1.0, current / max_val)
        filled = int(width * ratio)
        empty = width - filled

        if ratio < 0.5:
            color = "green"
        elif ratio < 0.8:
            color = "yellow"
        else:
            color = "red"

        return f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"

    def _render_fluid_mixture(self, mixture) -> str:
        """Отрендерить смесь жидкостей."""
        if not mixture or not hasattr(mixture, 'components'):
            return "[dim]Пусто[/dim]"

        components = mixture.components
        if not components:
            return "[dim]Пусто[/dim]"

        parts = []
        for fluid_type, amount in components.items():
            name = fluid_type.name if hasattr(fluid_type, 'name') else str(fluid_type)
            parts.append(f"{name}:{amount:.1f}ml")

        return " | ".join(parts)

    def render_fullness(self, uterus, title: str = "Заполнение системы") -> Panel:
        """
        Детальный рендер заполнения матки с распределением жидкости.
        Показывает: матку, трубы, яичники, предметы.
        """
        from rich.table import Table
        from rich import box

        # Получаем данные
        state = getattr(uterus, 'state', None)
        emoji, color, state_desc = self._get_state_style(state)

        inflation_status = getattr(uterus, 'inflation_status', None)
        inf_emoji, inf_color, inf_desc = self._get_inflation_style(inflation_status)
        inflation_ratio = getattr(uterus, 'inflation_ratio', 1.0)

        # Объёмы
        current_vol = getattr(uterus, 'current_volume', 50.0)
        uterus_filled = getattr(uterus, 'uterus_filled', 0.0)
        mixture = getattr(uterus, 'mixture', None)

        tubes_filled = getattr(uterus, 'tubes_filled', 0.0)
        ovaries_filled = getattr(uterus, 'ovaries_filled', 0.0)
        total_filled = getattr(uterus, 'filled', 0.0)

        objects = getattr(uterus, 'inserted_objects', [])

        # Создаём таблицу
        table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
        table.add_column("Param", style="cyan", width=18)
        table.add_column("Value", style="white")

        # Заголовок
        table.add_row(
            "[bold]СОСТОЯНИЕ[/bold]", 
            f"[{color}]{emoji} {state_desc}[/{color}] | "
            f"[{inf_color}]{inf_desc}[/{inf_color}] ({inflation_ratio:.1f}x)"
        )

        # === ЖИДКОСТЬ В МАТКЕ ===
        table.add_row("", "")
        table.add_row("[bold cyan]💧 МАТКА[/bold cyan]", "")

        fill_bar = self._create_fluid_bar(uterus_filled, current_vol)
        fill_pct = (uterus_filled / current_vol * 100) if current_vol > 0 else 0
        table.add_row(
            "Заполнение", 
            f"{fill_bar} {uterus_filled:.1f}/{current_vol:.1f}ml ({fill_pct:.0f}%)"
        )

        if mixture and hasattr(mixture, 'components') and mixture.components:
            fluid_info = self._render_fluid_mixture(mixture)
            table.add_row("Состав", fluid_info)

        # === ПРЕДМЕТЫ ===
        if objects:
            table.add_row("", "")
            table.add_row("[bold cyan]📦 ПРЕДМЕТЫ[/bold cyan]", f"{len(objects)} шт.")
            for i, obj in enumerate(objects):
                name = getattr(obj, 'name', f"Объект {i}")
                volume = getattr(obj, 'volume', 0) or getattr(obj, 'effective_volume', 0)
                diameter = getattr(obj, 'diameter', 0)
                table.add_row(
                    f"  [{i}]",
                    f"{name}: {volume:.1f}ml, Ø{diameter:.1f}cm"
                )

        # === ТРУБЫ ===
        table.add_row("", "")
        table.add_row("[bold magenta]🌊 ТРУБЫ[/bold magenta]", f"Всего: {tubes_filled:.1f}ml")

        for tube in getattr(uterus, 'tubes', []):
            if tube:
                side = getattr(tube, 'side', '?').upper()
                tube_fluid = getattr(tube, 'contained_fluid', 0.0)
                tube_capacity = getattr(tube, 'max_fluid_capacity', 15.0)
                tube_stretch = getattr(tube, 'current_stretch', 1.0)
                tube_inflate = getattr(tube, 'inflation_ratio', 1.0)

                tube_bar = self._create_fluid_bar(tube_fluid, tube_capacity, 15)
                table.add_row(
                    f"  {side}",
                    f"{tube_bar} {tube_fluid:.1f}/{tube_capacity:.1f}ml "
                    f"(×{tube_stretch:.1f}L ×{tube_inflate:.1f}W)"
                )

                tube_mixture = getattr(tube, 'fluid_mixture', None)
                if tube_mixture and hasattr(tube_mixture, 'components') and tube_mixture.components:
                    fluid_detail = self._render_fluid_mixture(tube_mixture)
                    table.add_row("", f"  └─ {fluid_detail}")

        # === ЯИЧНИКИ ===
        table.add_row("", "")
        table.add_row("[bold yellow]🥚 ЯИЧНИКИ[/bold yellow]", f"Всего: {ovaries_filled:.1f}ml")

        for ovary in getattr(uterus, 'ovaries', []):
            if ovary:
                side = getattr(ovary, 'side', '?').upper()
                ovary_fluid = getattr(ovary, 'fluid_content', 0.0)
                ovary_capacity = getattr(ovary, 'max_fluid_capacity', 20.0)
                follicles = getattr(ovary, 'follicle_sizes', [])

                # Инфляция и растяжение
                stretch = getattr(ovary, 'stretch_ratio', 1.0)
                inflate = getattr(ovary, 'inflation_ratio', 1.0)
                inf_status = getattr(ovary, 'inflation_status', None)
                inf_value = getattr(inf_status, 'value', 'normal') if inf_status else 'normal'

                ovary_bar = self._create_fluid_bar(ovary_fluid, ovary_capacity, 15)

                # Основная строка с размерами
                table.add_row(
                    f"  {side}",
                    f"{ovary_bar} {ovary_fluid:.1f}/{ovary_capacity:.1f}ml | "
                    f"Фолликулов: {len(follicles)}"
                )

                # Размеры и статус
                if stretch > 1.1 or inflate > 1.1:
                    table.add_row(
                        "",
                        f"  [dim]Size: {ovary.current_length:.1f}×{ovary.current_width:.1f}×{ovary.current_thickness:.1f}cm "
                        f"(×{stretch:.1f}S ×{inflate:.1f}I) [{inf_value.upper()}][/dim]"
                    )

                # Давление и натяжение
                pressure = getattr(ovary, 'internal_pressure', 0.0)
                if pressure > 0.5:
                    tension = ovary.get_skin_tension() if hasattr(ovary, 'get_skin_tension') else 0.0
                    table.add_row(
                        "",
                        f"  [dim]Pressure: {pressure:.2f} | Tension: {tension:.0%}[/dim]"
                    )

                # Состав жидкости в яичнике
                ovary_mixture = getattr(ovary, 'fluid_mixture', None)
                if ovary_mixture and hasattr(ovary_mixture, 'components') and ovary_mixture.components:
                    fluid_detail = self._render_fluid_mixture(ovary_mixture)
                    table.add_row("", f"  └─ {fluid_detail}")

                # Предупреждения
                if getattr(ovary, 'is_permanently_stretched', False):
                    table.add_row("", "  [yellow]⚠️ Permanently stretched[/yellow]")

        # === ИТОГО ===
        table.add_row("", "")
        total_capacity = current_vol + sum(
            getattr(t, 'max_fluid_capacity', 15.0) for t in getattr(uterus, 'tubes', []) if t
        ) + sum(
            getattr(o, 'max_fluid_capacity', 20.0) for o in getattr(uterus, 'ovaries', []) if o
        )
        total_bar = self._create_fluid_bar(total_filled, total_capacity, 20)
        table.add_row(
            "[bold]💧 ВСЕГО[/bold]",
            f"{total_bar} {total_filled:.1f}/{total_capacity:.1f}ml"
        )

        return Panel(table, title=f"[bold]{title}[/bold]", border_style="cyan")


# Для обратной совместимости
UterusRender = UterusRenderer

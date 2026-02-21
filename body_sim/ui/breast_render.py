# body_sim/ui/breast_render.py
"""
Рендеринг груди и сетки грудей (Rich + текстовый).
"""

from typing import List, TYPE_CHECKING, Optional, Dict, Any
from rich.console import Console, RenderableType, Group
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich.tree import Tree
from rich import box

if TYPE_CHECKING:
    from body_sim.anatomy.breast import Breast
    from body_sim.systems.grid import BreastGrid
    from body_sim.core.fluids import BreastFluid


# ============ Текстовый рендеринг (без зависимостей) ============

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
        f"Areola: {abs(breast.areola.diameter):.1f}cm (base: {breast.areola.base_diameter:.1f}cm)",
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
    """Рендер всей сетки грудей (текстовый)."""
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
    """Компактное текстовое представление груди."""
    fill_pct = (breast.filled / breast._max_volume * 100) if breast._max_volume > 0 else 0
    state_indicator = {
        'EMPTY': '○',
        'NORMAL': '●',
        'TENSE': '◐',
        'LEAKING': '💧',
        'OVERPRESSURED': '⚠️'
    }.get(breast.state.name, '?')
    
    return f"{state_indicator} {breast.cup.name}: {fill_pct:.0f}% ({breast.filled:.0f}ml)"


# ============ Rich рендеринг ============

class BreastRenderer:
    """Rich-рендерер для груди и сетки грудей."""
    
    STATE_STYLES = {
        'EMPTY': ('○', 'dim', 'Пустая'),
        'NORMAL': ('●', 'green', 'Норма'),
        'TENSE': ('◐', 'yellow', 'Напряжена'),
        'LEAKING': ('💧', 'blue', 'Течёт'),
        'OVERPRESSURED': ('⚠️', 'red', 'ПЕРЕПОЛНЕНА'),
    }
    
    CUP_COLORS = {
        'FLAT': 'dim',
        'MICRO': 'dim',
        'AAA': 'white',
        'AA': 'white',
        'A': 'green',
        'B': 'green',
        'C': 'cyan',
        'D': 'cyan',
        'E': 'blue',
        'F': 'blue',
        'G': 'magenta',
        'H': 'magenta',
        'I': 'bright_magenta',
        'J': 'bright_magenta',
    }
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def _get_state_style(self, state) -> tuple:
        """Получить стиль для состояния груди."""
        state_name = getattr(state, 'name', str(state))
        return self.STATE_STYLES.get(state_name, ('⚪', 'dim', state_name))
    
    def _get_cup_color(self, cup) -> str:
        """Получить цвет для размера чашки."""
        cup_name = getattr(cup, 'name', str(cup))
        return self.CUP_COLORS.get(cup_name, 'bright_red')
    
    def _bar(self, value: float, width: int = 8, 
             color_map: Dict[str, str] = None) -> Text:
        """Прогресс-бар с градиентом."""
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
    
    def _create_fluid_bar(self, current: float, max_val: float, width: int = 20) -> str:
        """Создать визуальный индикатор заполнения как в uterus."""
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
        """Отрендерить смесь жидкостей как в uterus."""
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
    
    def render_nipple(self, nipple, index: int = 0) -> Panel:
        """Рендер соска."""
        from body_sim.core.enums import NippleType
        
        nipple_type = nipple.nipple_type
        shape = nipple.shape
        
        # Определяем цвет по типу
        type_colors = {
            'TINY_FLAT': 'dim',
            'CUTE_SMALL': 'green',
            'PERKY_MEDIUM': 'cyan',
            'PUFFY': 'blue',
            'LARGE_THICK': 'magenta',
            'HYPER_LONG': 'bright_magenta',
            'GAPING_STRETCHED': 'red',
            'INVERTED': 'yellow',
        }
        color = type_colors.get(getattr(nipple_type, 'name', str(nipple_type)), 'white')
        
        table = Table(box=None, show_header=False)
        table.add_column("Param", style="cyan", width=10)
        table.add_column("Value")
        
        table.add_row("Тип", f"[{color}]{getattr(nipple_type, 'value', str(nipple_type))}[/{color}]")
        table.add_row("Форма", getattr(shape, 'value', str(shape)))
        table.add_row("Длина", f"{nipple.current_length:.1f}cm / {nipple.base_length:.1f}cm")
        table.add_row("Ширина", f"{nipple.current_width:.1f}cm / {nipple.base_width:.1f}cm")
        
        # Растяжение
        if nipple.stretch_ratio > 1.1:
            table.add_row("Растяжение", f"[yellow]×{nipple.stretch_ratio:.1f}[/yellow]")
        
        # Отверстие
        if nipple.is_open:
            table.add_row("Отверстие", f"[blue]Ø{nipple.gape_diameter:.2f}cm[/blue] "
                         f"(max: {nipple.max_gape_diameter:.2f}cm)")
        else:
            table.add_row("Отверстие", "[dim]Закрыто[/dim]")
        
        # Эрекция
        if nipple.current_length > nipple.base_length * 1.3:
            table.add_row("Состояние", "[magenta]Эрегирован[/magenta]")
        
        return Panel(
            table,
            title=f"[bold]Сосок {index}[/bold]",
            box=box.SIMPLE,
            border_style=color,
            padding=(0, 1)
        )
    
    def render_areola(self, areola) -> Panel:
        """Рендер ареолы."""
        table = Table(box=None, show_header=False)
        table.add_column("Param", style="cyan", width=12)
        table.add_column("Value")
        
        table.add_row("Диаметр", f"{abs(areola.diameter):.1f}cm / {areola.base_diameter:.1f}cm")
        table.add_row("Расширение", f"×{areola.expansion_ratio:.2f}")
        table.add_row("Чувствительность", self._bar(areola.sensitivity))
        table.add_row("Пухлость", self._bar(areola.puffiness))
        table.add_row("Сосков", str(len(areola.nipples)))
        
        # Цвет
        color = getattr(areola.color, 'value', str(areola.color))
        table.add_row("Цвет", f"[{color}]{color}[/{color}]")
        
        return Panel(
            table,
            title="[bold]Ареола[/bold]",
            box=box.SIMPLE,
            border_style="magenta",
            padding=(0, 1)
        )
    
    def render_fullness(self, breast: 'Breast', title: str = "Заполнение груди") -> Panel:
        """
        Детальный рендер заполнения груди с распределением жидкости.
        Аналог render_fullness из uterus_render.py
        """
        
        # Вспомогательная функция для безопасного преобразования в float
        def safe_float(val, default=0.0):
            if val is None:
                return default
            if isinstance(val, complex):
                return abs(val)
            try:
                return float(val)
            except (TypeError, ValueError):
                return default
        
        state = breast.state
        emoji, color, state_desc = self._get_state_style(state)
        cup_color = self._get_cup_color(breast.cup)
        
        # Получаем данные о заполнении
        current_vol = safe_float(breast.filled)
        max_vol = safe_float(breast._max_volume)
        fill_pct = (current_vol / max_vol * 100) if max_vol > 0 else 0
        
        # Смесь жидкостей
        mixture = getattr(breast, 'mixture', None)
        
        # Предметы
        objects = []
        if breast.insertion_manager and hasattr(breast.insertion_manager, 'inserted_objects'):
            objects = breast.insertion_manager.inserted_objects
        
        # Создаём таблицу как в uterus
        table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
        table.add_column("Param", style="cyan", width=18)
        table.add_column("Value", style="white")
        
        # Заголовок с состоянием
        table.add_row(
            "[bold]СОСТОЯНИЕ[/bold]", 
            f"[{color}]{emoji} {state_desc}[/{color}] | "
            f"[{cup_color}]{breast.cup.name}[/{cup_color}] → {breast.dynamic_cup.name}"
        )
        
        # === ОСНОВНОЕ ЗАПОЛНЕНИЕ ===
        table.add_row("", "")
        table.add_row("[bold cyan]💧 ОБЪЁМ[/bold cyan]", "")
        
        fill_bar = self._create_fluid_bar(current_vol, max_vol)
        table.add_row(
            "Заполнение", 
            f"{fill_bar} {current_vol:.1f}/{max_vol:.1f}ml ({fill_pct:.0f}%)"
        )
        
        # Состав жидкости
        if mixture and hasattr(mixture, 'components') and mixture.components:
            fluid_info = self._render_fluid_mixture(mixture)
            table.add_row("Состав", fluid_info)
        
        # === ПРЕДМЕТЫ ===
        if objects:
            table.add_row("", "")
            table.add_row("[bold cyan]📦 ПРЕДМЕТЫ[/bold cyan]", f"{len(objects)} шт.")
            total_obj_volume = 0
            for i, obj in enumerate(objects):
                name = getattr(obj, 'name', f"Объект {i}")
                volume = safe_float(getattr(obj, 'volume', 0) or getattr(obj, 'effective_volume', 0))
                diameter = safe_float(getattr(obj, 'diameter', 0))
                total_obj_volume += volume
                table.add_row(
                    f"  [{i}]",
                    f"{name}: {volume:.1f}ml, Ø{diameter:.1f}cm"
                )
            table.add_row("  Объём предметов", f"{total_obj_volume:.1f}ml")
        
        # === СОСКИ (аналогично трубам в uterus) ===
        if breast.areola and breast.areola.nipples:
            table.add_row("", "")
            table.add_row("[bold magenta]👁️ СОСКИ[/bold magenta]", f"{len(breast.areola.nipples)} шт.")
            
            for i, nipple in enumerate(breast.areola.nipples):
                # Статус отверстия
                nipple_length = safe_float(nipple.current_length)
                gape_diameter = safe_float(nipple.gape_diameter)
                
                if nipple.is_open:
                    status = f"[blue]Ø{gape_diameter:.2f}cm[/blue] [yellow]ОТКРЫТ[/yellow]"
                    # Если течёт
                    if state.name == 'LEAKING':
                        status += " [red]💧 ТЕЧЁТ[/red]"
                else:
                    status = "[dim]Закрыт[/dim]"
                
                # Растяжение
                stretch = safe_float(nipple.stretch_ratio, 1.0)
                stretch_str = f" ×{stretch:.1f}" if stretch > 1.1 else ""
                
                table.add_row(
                    f"  [{i}]",
                    f"{nipple_length:.1f}cm{stretch_str} | {status}"
                )
        
        # === АРЕОЛА ===
        if breast.areola:
            table.add_row("", "")
            table.add_row("[bold yellow]🟡 АРЕОЛА[/bold yellow]", "")
            
            areola = breast.areola
            areola_diameter = safe_float(areola.diameter)
            areola_base = safe_float(areola.base_diameter)
            
            areola_bar = self._create_fluid_bar(areola_diameter, areola_base * 2, 15)
            table.add_row(
                "  Диаметр",
                f"{areola_bar} {areola_diameter:.1f}cm (base: {areola_base:.1f}cm)"
            )
            expansion = safe_float(areola.expansion_ratio, 1.0)
            table.add_row("  Расширение", f"×{expansion:.2f}")
            
            sensitivity = safe_float(getattr(areola, 'sensitivity', 0.5))
            table.add_row("  Чувствительность", self._bar(sensitivity, width=15))
        
        # === ФИЗИЧЕСКИЕ ПАРАМЕТРЫ ===
        table.add_row("", "")
        table.add_row("[bold]⚙️ ПАРАМЕТРЫ[/bold]", "")
        
        # Давление
        from body_sim.core.fluids import FLUID_DEFS
        pressure = safe_float(breast.pressure(FLUID_DEFS))
        pressure_color = "red" if pressure > 1.0 else "yellow" if pressure > 0.5 else "green"
        table.add_row(
            "Давление",
            f"[{pressure_color}]{pressure:.2f}[/] (critical: >1.0)"
        )
        
        # Провисание
        sag = safe_float(breast.sag)
        sag_bar = self._bar(sag, width=15, 
                           color_map={'high': 'red', 'medium': 'yellow', 'low': 'green'})
        table.add_row("Провисание", f"{sag_bar} {sag:.3f}")
        
        # Упругость
        elasticity = safe_float(breast.elasticity, 0.5)
        table.add_row("Упругость", self._bar(elasticity, width=15))
        
        # === ЛАКТАЦИЯ ===
        if hasattr(breast, 'lactation') and breast.lactation:
            lact = breast.lactation
            lact_state = getattr(lact.state, 'name', 'OFF')
            if lact_state != 'OFF':
                table.add_row("", "")
                table.add_row("[bold blue]🥛 ЛАКТАЦИЯ[/bold blue]", f"[blue]{lact_state}[/blue]")
                if hasattr(lact, 'base_rate'):
                    base_rate = safe_float(lact.base_rate, 0.0)
                    table.add_row("  Потенциал", f"{base_rate:.2f}ml/tick")
        
        # === ИНФЛЯЦИЯ ===
        if hasattr(breast, 'inflation') and breast.inflation:
            inf = breast.inflation
            stretch = safe_float(getattr(inf, 'stretch_ratio', 1.0), 1.0)
            if stretch > 1.1:
                table.add_row("", "")
                table.add_row("[bold magenta]💨 ИНФЛЯЦИЯ[/bold magenta]", f"×{stretch:.1f}")
        
        return Panel(
            table, 
            title=f"[bold]{emoji} {title}[/bold]",
            border_style=color,
            padding=(1, 2)
        )
        
    def render_breast_detailed(self, breast: 'Breast', label: str = "Грудь") -> Panel:
        """Детальный рендер груди."""
        state = breast.state
        emoji, color, state_desc = self._get_state_style(state)
        cup_color = self._get_cup_color(breast.cup)
        dynamic_cup_color = self._get_cup_color(breast.dynamic_cup)
        
        # Основная таблица
        table = Table(box=None, show_header=False)
        table.add_column("Param", style="cyan", width=12)
        table.add_column("Value")
        
        # Состояние и размер
        table.add_row("Состояние", f"[{color}]{emoji} {state_desc}[/{color}]")
        table.add_row("Чашка", f"[{cup_color}]{breast.cup.name}[/{cup_color}] → "
                     f"[{dynamic_cup_color}]{breast.dynamic_cup.name}[/{dynamic_cup_color}]")
        
        # Заполнение
        fill_pct = (breast.filled / breast._max_volume * 100) if breast._max_volume > 0 else 0
        table.add_row("Заполнение", f"{breast.filled:.1f}ml / {breast._max_volume:.1f}ml "
                     f"({fill_pct:.0f}%)")
        table.add_row("Прогресс", self._bar(fill_pct / 100))
        
        # Физика
        table.add_row("Провисание", f"{breast.sag:.3f} / 1.0")
        table.add_row("Упругость", self._bar(breast.elasticity))
        
        # Давление
        from body_sim.core.fluids import FLUID_DEFS
        pressure = breast.pressure(FLUID_DEFS)
        table.add_row("Давление", f"{pressure:.2f}")
        if pressure > 0.5:
            table.add_row("⚠️ Давление", "[red]Высокое![/red]" if pressure > 1.0 else "[yellow]Повышенное[/yellow]")
        
        # Лактация
        if hasattr(breast, 'lactation') and breast.lactation:
            lact_state = getattr(breast.lactation.state, 'name', 'OFF')
            if lact_state != 'OFF':
                table.add_row("Лактация", f"[blue]{lact_state}[/blue]")
        
        # Инфляция
        if hasattr(breast, 'inflation') and breast.inflation:
            stretch = breast.inflation.stretch_ratio
            if stretch > 1.0:
                table.add_row("Растяжение", f"[magenta]×{stretch:.1f}[/magenta]")
        
        # Вставленные предметы
        if breast.insertion_manager and breast.insertion_manager.inserted_objects:
            obj_count = len(breast.insertion_manager.inserted_objects)
            obj_volume = breast.insertion_manager.total_volume
            table.add_row("Предметы", f"[yellow]{obj_count} шт, {obj_volume:.1f}ml[/yellow]")
        
        # Составляем панели
        panels = [table]
        
        # Ареола
        if breast.areola:
            panels.append(self.render_areola(breast.areola))
        
        # Соски
        if breast.areola and breast.areola.nipples:
            for i, nipple in enumerate(breast.areola.nipples):
                panels.append(self.render_nipple(nipple, i))
        
        return Panel(
            Columns(panels, equal=True) if len(panels) > 1 else panels[0],
            title=f"[bold {cup_color}]{emoji} {label} ({breast.cup.name})[/bold {cup_color}]",
            box=box.ROUNDED,
            border_style=color,
            padding=(1, 2)
        )
    
    def render_breast_compact(self, breast: 'Breast', label: str = "") -> Panel:
        """Компактный рендер груди для сетки."""
        state = breast.state
        emoji, color, state_desc = self._get_state_style(state)
        cup_color = self._get_cup_color(breast.cup)
        
        fill_pct = (breast.filled / breast._max_volume * 100) if breast._max_volume > 0 else 0
        
        content = Text.from_markup(
            f"[{cup_color}]{breast.cup.name}[/{cup_color}] "
            f"[{color}]{emoji}[/{color}]\n"
            f"{fill_pct:.0f}% ({breast.filled:.0f}ml)\n"
            f"S:{breast.sag:.2f} E:{breast.elasticity:.2f}"
        )
        
        return Panel(
            content,
            title=f"[bold]{label}[/bold]" if label else None,
            box=box.SIMPLE,
            border_style=color,
            padding=(0, 1)
        )
    
    def render_grid(self, grid: 'BreastGrid', title: str = "Сетка грудей") -> Panel:
        """Рендер всей сетки грудей."""
        if not grid.rows:
            return Panel("[dim]Нет грудей[/dim]", title=title, box=box.ROUNDED)
        
        # Создаём таблицу сетки
        table = Table(box=box.SIMPLE, show_header=False)
        
        # Определяем количество колонок по максимальной ширине ряда
        max_cols = max(len(row) for row in grid.rows) if grid.rows else 0
        
        for _ in range(max_cols):
            table.add_column()
        
        # Заполняем ряды
        for r_idx, row in enumerate(grid.rows):
            row_panels = []
            for c_idx in range(max_cols):
                if c_idx < len(row):
                    breast = row[c_idx]
                    label = grid.get_label(r_idx, c_idx) or f"[{r_idx},{c_idx}]"
                    row_panels.append(self.render_breast_detailed(breast, label))
                else:
                    row_panels.append(Text(""))
            
            table.add_row(*row_panels)
        
        # Статистика
        stats = grid.stats()
        stats_text = (
            f"Всего: {len(grid.all())} | "
            f"Заполнено: {stats.get('total_filled', 0):.1f}ml | "
            f"Текут: {stats.get('leaking', 0)}"
        )
        
        return Panel(
            Group(table, Text(stats_text, style="dim")),
            title=f"[bold magenta]{title}[/bold magenta]",
            box=box.DOUBLE,
            border_style="bright_magenta",
            padding=(1, 2)
        )
    
    def render_tree_view(self, grid: 'BreastGrid') -> Tree:
        """Древовидное представление сетки грудей."""
        root = Tree("🍈 [bold magenta]Сетка грудей[/bold magenta]")
        
        for r_idx, row in enumerate(grid.rows):
            row_node = root.add(f"Ряд {r_idx}")
            
            for c_idx, breast in enumerate(row):
                label = grid.get_label(r_idx, c_idx) or f"[{r_idx},{c_idx}]"
                state = breast.state
                emoji, color, state_desc = self._get_state_style(state)
                
                breast_node = row_node.add(
                    f"[{color}]{emoji} {label}: {breast.cup.name}[/{color}] "
                    f"({breast.filled:.0f}ml)"
                )
                
                # Ареола
                if breast.areola:
                    areola = breast.areola
                    breast_node.add(f"Ареола: {areola.diameter:.1f}cm, "
                                  f"чувств. {areola.sensitivity:.0%}")
                    
                    # Соски
                    for i, nipple in enumerate(areola.nipples):
                        nipple_node = breast_node.add(
                            f"Сосок {i}: {nipple.current_length:.1f}cm, "
                            f"{'открыт' if nipple.is_open else 'закрыт'}"
                        )
                        
                        if nipple.is_open:
                            nipple_node.add(f"[blue]Ø{nipple.gape_diameter:.2f}cm[/blue]")
        
        return root
    
    def print(self, renderable: RenderableType):
        """Вывести в консоль."""
        self.console.print(renderable)


# ============ Фабричные функции ============

def create_breast_renderer(console: Optional[Console] = None) -> BreastRenderer:
    """Создать рендерер груди."""
    return BreastRenderer(console)


# Обратная совместимость с render.py
def render_breast_rich(breast: 'Breast', label: str = "") -> RenderableType:
    """Быстрый Rich-рендер груди."""
    renderer = BreastRenderer()
    return renderer.render_breast_detailed(breast, label)


def render_grid_rich(grid: 'BreastGrid', title: str = "Сетка грудей") -> RenderableType:
    """Быстрый Rich-рендер сетки."""
    renderer = BreastRenderer()
    return renderer.render_grid(grid, title)


# Новая функция для fullness (совместимость с uterus style)
def render_breast_fullness(breast: 'Breast', title: str = "Заполнение груди") -> RenderableType:
    """Рендер заполнения груди в стиле uterus fullness."""
    renderer = BreastRenderer()
    return renderer.render_fullness(breast, title)

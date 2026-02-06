# body_sim/ui/body_list_render.py
"""
Улучшенный Rich-рендеринг списка тел/персонажей.
Компактное табличное представление с детальной информацией.
"""

from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
from rich.console import Console, RenderableType, Group
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text
from rich import box
from rich.style import Style
from rich.align import Align


@dataclass
class BodyListConfig:
    """Конфигурация отображения списка тел."""
    show_index: bool = True
    show_sex: bool = True
    show_name: bool = True
    show_body_type: bool = True
    show_genitals: bool = True
    show_stats: bool = True
    show_breasts: bool = True
    show_uterus: bool = True
    compact_mode: bool = False
    max_name_length: int = 15
    highlight_active: bool = True


class BodyListRenderer:
    """Улучшенный рендерер списка тел."""
    
    # Цвета для пола
    SEX_COLORS = {
        'MALE': 'bright_blue',
        'FEMALE': 'bright_magenta',
        'FUTANARI': 'bright_magenta',
        'NONE': 'gray',
        # Прямые значения enum
        1: 'bright_blue',   # MALE
        2: 'bright_magenta', # FEMALE
        3: 'bright_magenta', # FUTANARI
        4: 'gray',          # NONE
    }
    
    SEX_EMOJIS = {
        'MALE': '♂',
        'FEMALE': '♀',
        'FUTANARI': '⚧',
        'NONE': '○',
        1: '♂',
        2: '♀',
        3: '⚧',
        4: '○',
    }
    
    SEX_NAMES = {
        'MALE': 'M',
        'FEMALE': 'F',
        'FUTANARI': 'Fu',
        'NONE': '-',
        1: 'M',
        2: 'F',
        3: 'Fu',
        4: '-',
    }
    
    # Типы тел
    BODY_TYPE_EMOJIS = {
        'PETITE': 'p',
        'SLENDER': 's',
        'AVERAGE': 'a',
        'CURVY': 'c',
        'MUSCULAR': 'm',
        'HEAVY': 'h',
        'AMAZON': 'A',
    }
    
    BODY_TYPE_COLORS = {
        'PETITE': 'bright_cyan',
        'SLENDER': 'cyan',
        'AVERAGE': 'white',
        'CURVY': 'bright_yellow',
        'MUSCULAR': 'bright_red',
        'HEAVY': 'dim',
        'AMAZON': 'bright_green',
    }
    
    def __init__(self, console: Optional[Console] = None, config: Optional[BodyListConfig] = None):
        self.console = console or Console()
        self.config = config or BodyListConfig()
    
    def _get_sex_style(self, body) -> tuple:
        """Получить стиль для пола тела."""
        sex = getattr(body, 'sex', None)
        
        # Пробуем разные способы получения значения
        if hasattr(sex, 'name'):
            sex_key = sex.name
        elif hasattr(sex, 'value'):
            sex_key = sex.value
        else:
            sex_key = str(sex).upper() if sex else 'NONE'
        
        color = self.SEX_COLORS.get(sex_key, 'white')
        emoji = self.SEX_EMOJIS.get(sex_key, '?')
        name = self.SEX_NAMES.get(sex_key, '?')
        
        return color, emoji, name
    
    def _get_body_type_style(self, body) -> tuple:
        """Получить стиль для типа тела."""
        body_type = getattr(body, 'body_type', None)
        
        if hasattr(body_type, 'name'):
            type_key = body_type.name
        elif hasattr(body_type, 'value'):
            type_key = body_type.value
        else:
            type_key = str(body_type).upper() if body_type else 'AVERAGE'
        
        emoji = self.BODY_TYPE_EMOJIS.get(type_key, '?')
        color = self.BODY_TYPE_COLORS.get(type_key, 'white')
        
        return color, emoji
    
    def _make_bar(self, value: float, max_val: float = 1.0, width: int = 6, 
                  color_map: Dict[str, str] = None) -> str:
        """Создать мини-бар для таблицы."""
        if max_val <= 0:
            return "░" * width
        
        ratio = min(max(value / max_val, 0.0), 1.0)
        filled = int(ratio * width)
        
        if color_map:
            if ratio > 0.7:
                color = color_map.get('high', 'green')
            elif ratio > 0.4:
                color = color_map.get('medium', 'yellow')
            else:
                color = color_map.get('low', 'red')
        else:
            color = 'green' if ratio < 0.4 else 'yellow' if ratio < 0.7 else 'red'
        
        return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/{color}]"
    
    def _get_genitals_info(self, body) -> str:
        """Получить информацию о гениталиях."""
        parts = []
        
        # Пенисы
        if getattr(body, 'has_penis', False) or hasattr(body, 'penises'):
            penises = getattr(body, 'penises', [])
            if penises:
                erect_count = sum(1 for p in penises if getattr(p, 'is_erect', False))
                avg_length = sum(getattr(p, 'current_length', 0) for p in penises) / len(penises) if penises else 0
                
                penis_str = f"🍆{len(penises)}"
                if erect_count > 0:
                    penis_str += f"[red]🔥{erect_count}[/red]"
                if avg_length > 0:
                    penis_str += f" {avg_length:.1f}cm"
                parts.append(penis_str)
        
        # Влагалища
        if getattr(body, 'has_vagina', False) or hasattr(body, 'vaginas'):
            vaginas = getattr(body, 'vaginas', [])
            if vaginas:
                aroused = sum(1 for v in vaginas if getattr(v, 'is_aroused', False))
                depth = sum(getattr(v, 'current_depth', 0) for v in vaginas) / len(vaginas) if vaginas else 0
                
                vag_str = f"🌸{len(vaginas)}"
                if aroused > 0:
                    vag_str += f"[cyan]💧{aroused}[/cyan]"
                if depth > 0:
                    vag_str += f" {depth:.1f}cm"
                parts.append(vag_str)
        
        # Мошонки
        if getattr(body, 'has_scrotum', False) or hasattr(body, 'scrotums'):
            scrotums = getattr(body, 'scrotums', [])
            if scrotums:
                testicles = sum(len(getattr(s, 'testicles', [])) for s in scrotums)
                fullness = sum(getattr(s, 'fullness', 0) for s in scrotums) / len(scrotums) if scrotums else 0
                
                scr_str = f"🥚{testicles}"
                if fullness > 0.7:
                    scr_str += f"[yellow]F{fullness:.0%}[/yellow]"
                parts.append(scr_str)
        
        # Клитор
        if hasattr(body, 'clitorises') and body.clitorises:
            clit_count = len(body.clitorises)
            avg_size = sum(getattr(c, 'current_length', 0) for c in body.clitorises) / clit_count
            if avg_size > 2.0:
                parts.append(f"[magenta]C{clit_count} {avg_size:.1f}cm[/magenta]")
            else:
                parts.append(f"C{clit_count}")
        
        # Анус
        if hasattr(body, 'anuses') and body.anuses:
            anus_count = len(body.anuses)
            parts.append(f"🍩{anus_count}")
        
        return " | ".join(parts) if parts else "[dim]-[/dim]"
    
    def _get_breasts_info(self, body) -> str:
        """Получить информацию о груди."""
        if not getattr(body, 'has_breasts', False):
            return "[dim]-[/dim]"
        
        grid = getattr(body, 'breast_grid', None)
        if not grid:
            return "[dim]-[/dim]"
        
        breasts = []
        if hasattr(grid, 'all'):
            breasts = grid.all()
        elif hasattr(grid, 'rows'):
            for row in grid.rows:
                breasts.extend(row)
        
        if not breasts:
            return "[dim]-[/dim]"
        
        count = len(breasts)
        
        # Объём и заполнение
        total_filled = sum(getattr(b, 'filled', 0) or 0 for b in breasts)
        total_capacity = sum(getattr(b, '_max_volume', 0) or getattr(b, 'volume', 0) or 0 for b in breasts)
        fill_pct = (total_filled / total_capacity * 100) if total_capacity > 0 else 0
        
        # Состояния
        leaking = sum(1 for b in breasts if 'LEAKING' in str(getattr(b, 'state', '')))
        tense = sum(1 for b in breasts if 'TENSE' in str(getattr(b, 'state', '')) or 'OVERPRESSURED' in str(getattr(b, 'state', '')))
        
        # Размеры
        cups = set()
        for b in breasts:
            cup = getattr(b, 'cup', None)
            if cup:
                cup_name = cup.name if hasattr(cup, 'name') else str(cup)
                cups.add(cup_name)
        cup_str = "/".join(sorted(cups)) if cups else "?"
        
        result = f"🍼{count} {cup_str}"
        
        if fill_pct > 0:
            result += f" {fill_pct:.0f}%"
        if leaking > 0:
            result += f"[red]💧{leaking}[/red]"
        if tense > 0:
            result += f"[yellow]⚡{tense}[/yellow]"
        
        return result
    
    def _get_uterus_info(self, body) -> str:
        """Получить информацию о матке."""
        if not hasattr(body, 'uterus_system') or not body.uterus_system:
            return "[dim]-[/dim]"
        
        system = body.uterus_system
        uteri = getattr(system, 'uteri', [])
        
        if not uteri:
            return "[dim]-[/dim]"
        
        count = len(uteri)
        
        # Собираем статусы
        statuses = []
        for uterus in uteri:
            state = getattr(uterus, 'state', None)
            state_name = state.name if hasattr(state, 'name') else str(state)
            
            if 'EVERTED' in state_name:
                statuses.append("[red]ВЫВ![/red]")
            elif 'PROLAPSED' in state_name:
                statuses.append("[orange]ПРОЛ[/orange]")
            elif 'DESCENDED' in state_name:
                statuses.append("[yellow]ОПУЩ[/yellow]")
        
        # Яичники
        ovaries = []
        for uterus in uteri:
            for ovary in getattr(uterus, 'ovaries', []):
                if ovary and getattr(ovary, 'is_everted', False):
                    ovaries.append("[red]⚠️O[/red]")
        
        result = f"🌸{count}"
        if statuses:
            result += f" ({''.join(statuses)})"
        if ovaries:
            result += f" {''.join(ovaries)}"
        
        return result
    
    def _get_stats_info(self, body) -> str:
        """Получить информацию о статах."""
        stats = getattr(body, 'stats', None)
        if not stats:
            return "[dim]-[/dim]"
        
        parts = []
        
        # Возбуждение
        arousal = getattr(stats, 'arousal', 0)
        if arousal > 0:
            parts.append(f"A{self._make_bar(arousal, 1.0, 4)}")
        
        # Удовольствие
        pleasure = getattr(stats, 'pleasure', 0)
        if pleasure > 0:
            parts.append(f"P{self._make_bar(pleasure, 1.0, 4)}")
        
        # Боль
        pain = getattr(stats, 'pain', 0)
        if pain > 0.3:
            parts.append(f"[red]💔{self._make_bar(pain, 1.0, 4, {'high': 'red', 'medium': 'red', 'low': 'yellow'})}[/red]")
        
        # Усталость
        fatigue = getattr(stats, 'fatigue', 0)
        if fatigue > 0.5:
            parts.append(f"[yellow]😴{self._make_bar(fatigue, 1.0, 4, {'high': 'red', 'medium': 'yellow', 'low': 'green'})}[/yellow]")
        
        return " ".join(parts) if parts else "[dim]-[/dim]"
    
    def render_body_list(self, bodies: List, active_idx: int = 0, 
                        title: str = "Персонажи") -> Panel:
        """
        Основной метод рендера списка тел.
        
        Args:
            bodies: Список тел
            active_idx: Индекс активного/выбранного тела
            title: Заголовок панели
        """
        if not bodies:
            return Panel("[dim]Нет персонажей[/dim]", title=title, box=box.ROUNDED)
        
        # Определяем колонки
        table = Table(
            box=box.SIMPLE_HEAD if len(bodies) > 1 else box.SIMPLE,
            show_header=True,
            header_style="bold cyan",
            row_styles=["", "dim"],
            padding=(0, 1)
        )
        
        # Добавляем колонки
        if self.config.show_index:
            table.add_column("#", width=3, justify="center")
        
        if self.config.show_sex:
            table.add_column("Пол", width=4, justify="center")
        
        if self.config.show_name:
            table.add_column("Имя", min_width=10, max_width=self.config.max_name_length)
        
        if self.config.show_body_type:
            table.add_column("Тип", width=5, justify="center")
        
        if self.config.show_genitals:
            table.add_column("Гениталии", min_width=15)
        
        if self.config.show_breasts:
            table.add_column("Грудь", min_width=12)
        
        if self.config.show_uterus:
            table.add_column("Матка", min_width=10)
        
        if self.config.show_stats:
            table.add_column("Статусы", min_width=20)
        
        # Заполняем строки
        for i, body in enumerate(bodies):
            row = []
            
            # Маркер активного
            is_active = i == active_idx
            marker = ">" if is_active else " "
            
            # Индекс
            if self.config.show_index:
                row.append(f"[bold cyan]{marker}{i}[/bold cyan]" if is_active else f"{marker}{i}")
            
            # Пол
            if self.config.show_sex:
                sex_color, sex_emoji, sex_name = self._get_sex_style(body)
                if is_active and self.config.highlight_active:
                    row.append(f"[bold {sex_color}]{sex_emoji}[/bold {sex_color}]")
                else:
                    row.append(f"[{sex_color}]{sex_emoji}[/{sex_color}]")
            
            # Имя
            if self.config.show_name:
                name = getattr(body, 'name', f"Body {i}")
                sex_color, _, _ = self._get_sex_style(body)
                if is_active and self.config.highlight_active:
                    row.append(f"[bold {sex_color}]{name[:self.config.max_name_length]}[/bold {sex_color}]")
                else:
                    row.append(f"[{sex_color}]{name[:self.config.max_name_length]}[/{sex_color}]")
            
            # Тип тела
            if self.config.show_body_type:
                type_color, type_emoji = self._get_body_type_style(body)
                row.append(f"[{type_color}]{type_emoji}[/{type_color}]")
            
            # Гениталии
            if self.config.show_genitals:
                row.append(self._get_genitals_info(body))
            
            # Грудь
            if self.config.show_breasts:
                row.append(self._get_breasts_info(body))
            
            # Матка
            if self.config.show_uterus:
                row.append(self._get_uterus_info(body))
            
            # Статусы
            if self.config.show_stats:
                row.append(self._get_stats_info(body))
            
            table.add_row(*row)
        
        # Создаем панель
        border_style = "bright_blue" if len(bodies) > 0 else "dim"
        
        # Добавляем легенду если много тел
        footer = None
        if len(bodies) > 3:
            footer_text = (
                f"[dim]Всего: {len(bodies)} | "
                f"♂ Мужской ♀ Женский ⚧ Футанари | "
                f"🔥 Эрекция 💧 Возбуждение[/dim]"
            )
            footer = Text.from_markup(footer_text)
        
        content = Group(table, footer) if footer else table
        
        return Panel(
            content,
            title=f"[bold]{title} ({len(bodies)})[/bold]",
            box=box.ROUNDED,
            border_style=border_style,
            padding=(1, 1)
        )
    
    def render_compact_list(self, bodies: List, active_idx: int = 0) -> Panel:
        """Ультракомпактный рендер для маленьких экранов."""
        if not bodies:
            return Panel("[dim]Нет[/dim]", title="Тела", box=box.SIMPLE)
        
        table = Table(box=None, show_header=False, padding=(0, 1))
        table.add_column("#", width=3)
        table.add_column("Info", width=40)
        
        for i, body in enumerate(bodies[:10]):  # Лимит 10
            marker = ">" if i == active_idx else " "
            
            sex_color, sex_emoji, _ = self._get_sex_style(body)
            name = getattr(body, 'name', f"B{i}")[:12]
            
            # Компактная инфо
            info_parts = [f"[{sex_color}]{sex_emoji} {name}[/{sex_color}]"]
            
            # Гениталии компактно
            if getattr(body, 'has_penis', False):
                penises = getattr(body, 'penises', [])
                if penises:
                    erect = sum(1 for p in penises if getattr(p, 'is_erect', False))
                    info_parts.append(f"🍆{len(penises)}{'🔥' if erect else ''}")
            
            if getattr(body, 'has_vagina', False):
                vaginas = getattr(body, 'vaginas', [])
                if vaginas:
                    info_parts.append(f"🌸{len(vaginas)}")
            
            # Статус
            stats = getattr(body, 'stats', None)
            if stats:
                arousal = getattr(stats, 'arousal', 0)
                if arousal > 0.5:
                    info_parts.append(f"[red]A{arousal:.0%}[/red]")
            
            table.add_row(f"{marker}{i}", " ".join(info_parts))
        
        if len(bodies) > 10:
            table.add_row("", f"[dim]... и ещё {len(bodies) - 10}[/dim]")
        
        return Panel(table, title=f"Тела ({len(bodies)})", box=box.SIMPLE, border_style="blue")
    
    def render_body_grid(self, bodies: List, cols: int = 3) -> Panel:
        """Рендер тел в виде сетки карточек."""
        if not bodies:
            return Panel("[dim]Нет персонажей[/dim]", title="Сетка", box=box.ROUNDED)
        
        cards = []
        
        for i, body in enumerate(bodies):
            sex_color, sex_emoji, sex_name = self._get_sex_style(body)
            name = getattr(body, 'name', f"Body {i}")
            
            # Карточка
            card_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            card_table.add_column("Param", style="cyan", width=8)
            card_table.add_column("Value")
            
            card_table.add_row("Имя", f"[bold {sex_color}]{name[:15]}[/bold {sex_color}]")
            card_table.add_row("Пол", f"[{sex_color}]{sex_emoji} {sex_name}[/{sex_color}]")
            
            # Тип тела
            type_color, type_emoji = self._get_body_type_style(body)
            card_table.add_row("Тип", f"[{type_color}]{type_emoji}[/{type_emoji}]")
            
            # Гениталии коротко
            gen_info = self._get_genitals_info(body)
            if gen_info != "[dim]-[/dim]":
                card_table.add_row("Генит.", gen_info[:25])
            
            card = Panel(
                card_table,
                box=box.ROUNDED,
                border_style=sex_color,
                padding=(0, 1)
            )
            cards.append(card)
        
        # Распределяем по колонкам
        grid = Columns(cards, equal=True, expand=True)
        
        return Panel(
            grid,
            title=f"[bold]Персонажи ({len(bodies)})[/bold]",
            box=box.DOUBLE,
            border_style="bright_blue",
            padding=(1, 2)
        )
    
    def print(self, renderable: RenderableType):
        """Вывести в консоль."""
        self.console.print(renderable)


# ======================
# ФУНКЦИИ-ОБЁРТКИ
# ======================

def render_body_list(bodies: List, active_idx: int = 0, 
                    title: str = "Персонажи",
                    config: Optional[BodyListConfig] = None) -> Panel:
    """Функция-обёртка для рендера списка тел."""
    renderer = BodyListRenderer(config=config)
    return renderer.render_body_list(bodies, active_idx, title)


def render_compact_body_list(bodies: List, active_idx: int = 0) -> Panel:
    """Функция-обёртка для компактного рендера."""
    renderer = BodyListRenderer()
    return renderer.render_compact_list(bodies, active_idx)


def render_body_grid(bodies: List, cols: int = 3) -> Panel:
    """Функция-обёртка для сетки."""
    renderer = BodyListRenderer()
    return renderer.render_body_grid(bodies, cols)

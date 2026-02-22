from functools import wraps
from typing import Dict, Any, Optional, Callable, Union
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.console import Console
import time


class SexStats:
    """
    Класс-декоратор для отслеживания секс-статистики.
    Хранит все метрики внутри, предоставляет методы track() как декоратор.
    """
    
    def __init__(self):
        # Основные метрики по категориям
        self._data: Dict[str, Dict[str, Union[int, float]]] = {
            'vaginal': {
                'penetrations': 0,
                'thrusts': 0,
                'total_depth_cm': 0.0,
                'max_depth_cm': 0.0,
                'duration_sec': 0.0,
                'creampies': 0,
                'sperm_ml': 0.0,
                'orgasms': 0
            },
            'anal': {
                'penetrations': 0,
                'thrusts': 0,
                'gape_events': 0,
                'duration_sec': 0.0,
                'creampies': 0,
                'sperm_ml': 0.0,
                'orgasms': 0
            },
            'oral': {
                'sessions': 0,
                'deepthroat_count': 0,
                'swallowed_ml': 0.0,
                'facial_count': 0,
                'duration_sec': 0.0,
                'throatpie_count': 0
            },
            'manual': {
                'handjobs': 0,
                'fingering_vaginal': 0,
                'fingering_anal': 0,
                'fisting_events': 0
            },
            'breasts': {
                'titfuck_sessions': 0,
                'cum_on_breasts': 0
            },
            'orgasms': {
                'total': 0,
                'vaginal': 0,
                'clitoral': 0,
                'anal': 0,
                'oral': 0,
                'combined': 0,
                'squirting_ml': 0.0
            },
            'fluids': {
                'total_received_ml': 0.0,
                'retained_ml': 0.0,
                'spilled_ml': 0.0,
                'swallowed_ml': 0.0,
                'womb_filled_ml': 0.0,
                'stomach_filled_ml': 0.0
            }
        }
        
        # Детальная история событий (последние 100)
        self._history: list = []
        self._max_history = 100
        
        # Счетчики для уникальных значений (позиции, партнеры и т.д.)
        self._unique_positions: set = set()
        self._session_start = time.time()
    
    def record(self, category: str, metric: str, value: Union[int, float] = 1):
        """
        Прямая запись метрики в статистику.
        
        Args:
            category: Категория (vaginal, anal, oral, etc.)
            metric: Имя метрики
            value: Значение для добавления (по умолчанию 1)
        """
        if category in self._data and metric in self._data[category]:
            current = self._data[category][metric]
            if isinstance(current, (int, float)):
                self._data[category][metric] = current + value
    
    def track(self, category: str, metric: Optional[str] = None,
              extract_depth: bool = False,
              extract_volume: bool = False,
              extract_position: bool = False,
              only_on_success: bool = True,
              track_duration: bool = True):
        """
        Декоратор для отслеживания вызовов функций.
        
        Args:
            category: Категория действия ('vaginal', 'anal', 'oral', etc.)
            metric: Конкретная метрика для инкремента (если None - только duration/depth)
            extract_depth: Извлекать глубину из аргументов (depth, cm)
            extract_volume: Извлекать объем (ml, volume)
            extract_position: Извлекать позицию из kwargs['position']
            only_on_success: Записывать только если результат truthy
            track_duration: Отслеживать время выполнения
            
        Usage:
            @stats.track('vaginal', 'penetrations', extract_depth=True)
            def penetrate_vagina(depth=10):
                return True
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time() if track_duration else None
                
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Проверяем условие записи
                should_record = (not only_on_success) or (result if only_on_success else True)
                
                if should_record:
                    # Основная метрика
                    if metric:
                        self.record(category, metric)
                    
                    # Извлечение глубины
                    if extract_depth:
                        depth = kwargs.get('depth') or kwargs.get('cm') or 0
                        if depth:
                            self.record(category, 'total_depth_cm', depth)
                            # Обновляем максимум
                            current_max = self._data[category].get('max_depth_cm', 0)
                            if depth > current_max:
                                self._data[category]['max_depth_cm'] = depth
                    
                    # Извлечение объема жидкости
                    if extract_volume:
                        volume = kwargs.get('ml') or kwargs.get('volume') or 0
                        if volume:
                            # В категорию
                            if 'sperm_ml' in self._data[category]:
                                self.record(category, 'sperm_ml', volume)
                            # В общие жидкости
                            self.record('fluids', 'total_received_ml', volume)
                    
                    # Позиция
                    if extract_position:
                        pos = kwargs.get('position') or kwargs.get('pose')
                        if pos:
                            self._unique_positions.add(pos)
                    
                    # Длительность
                    if track_duration and start_time:
                        duration = time.time() - start_time
                        dur_key = 'duration_sec'
                        if dur_key in self._data[category]:
                            self.record(category, dur_key, duration)
                    
                    # Запись в историю
                    self._add_to_history(func.__name__, category, result)
                
                return result
            return wrapper
        return decorator
    
    def _add_to_history(self, action: str, category: str, success: bool):
        """Добавляет событие в историю (circular buffer)"""
        self._history.append({
            'action': action,
            'category': category,
            'timestamp': time.time(),
            'success': success
        })
        if len(self._history) > self._max_history:
            self._history.pop(0)
    
    def orgasm(self, type_: str = 'total', intensity: int = 1, squirt_ml: float = 0):
        """
        Ручная запись оргазма (можно вызывать из команд).
        
        Args:
            type_: Тип оргазма (vaginal, clitoral, anal, oral, combined)
            intensity: Интенсивность (1-10), влияет на счетчик
            squirt_ml: Объем сквирта, если есть
        """
        self.record('orgasms', 'total', intensity)
        if type_ in self._data['orgasms']:
            self.record('orgasms', type_, intensity)
        if squirt_ml > 0:
            self.record('orgasms', 'squirting_ml', squirt_ml)
    
    def fluid_transfer(self, ml: float, target: str = 'retained'):
        """
        Учет перемещения жидкостей.
        
        Args:
            ml: Объем в мл
            target: Куда ('retained', 'spilled', 'swallowed', 'womb', 'stomach')
        """
        if target == 'retained':
            self.record('fluids', 'retained_ml', ml)
        elif target == 'spilled':
            self.record('fluids', 'spilled_ml', ml)
        elif target == 'swallowed':
            self.record('fluids', 'swallowed_ml', ml)
            self.record('oral', 'swallowed_ml', ml)
        elif target == 'womb':
            self.record('fluids', 'womb_filled_ml', ml)
        elif target == 'stomach':
            self.record('fluids', 'stomach_filled_ml', ml)
    
    def get_stats(self, category: Optional[str] = None):
        """Получить данные статистики"""
        if category:
            return self._data.get(category, {}).copy()
        return {k: v.copy() for k, v in self._data.items()}
    
    def get_summary(self) -> dict:
        """Сводка ключевых показателей"""
        total_actions = sum(
            v for cat in self._data.values() 
            for k, v in cat.items() 
            if isinstance(v, int) and k not in ['duration_sec']
        )
        
        return {
            'session_duration_min': (time.time() - self._session_start) / 60,
            'total_actions': total_actions,
            'unique_positions': len(self._unique_positions),
            'total_orgasms': self._data['orgasms']['total'],
            'total_fluids_ml': self._data['fluids']['total_received_ml'],
            'history_count': len(self._history)
        }
    
    def render(self, detailed: bool = False) -> Panel:
        """
        Рендерит статистику через Rich.
        
        Args:
            detailed: Если True, показывает все метрики, иначе только ненулевые
            
        Returns:
            Panel с таблицей статистики
        """
        table = Table(
            title="[bold magenta]Sex Statistics[/bold magenta]",
            border_style="magenta",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("Category", style="cyan", width=12)
        table.add_column("Metric", style="white", width=20)
        table.add_column("Value", style="green", justify="right", width=10)
        table.add_column("Bar", style="bright_magenta", width=15)
        
        # Собираем данные для отображения
        for cat_name, metrics in self._data.items():
            row_added = False
            
            for metric_name, value in metrics.items():
                # Пропускаем нулевые если не detailed
                if not detailed and (value == 0 or value == 0.0):
                    continue
                
                # Форматируем значение
                if isinstance(value, float):
                    val_str = f"{value:.1f}"
                    # Прогресс-бар для значений
                    max_val = max(metrics.values()) if any(isinstance(v, (int, float)) and v > 0 for v in metrics.values()) else 1
                    if isinstance(max_val, (int, float)) and max_val > 0:
                        bar_len = int(15 * (value / max_val)) if value > 0 else 0
                        bar = "█" * bar_len + "░" * (15 - bar_len)
                    else:
                        bar = ""
                else:
                    val_str = str(value)
                    bar = ""
                
                # Первая строка категории выделяется
                cat_display = f"[bold]{cat_name}[/bold]" if not row_added else ""
                
                table.add_row(
                    cat_display,
                    metric_name.replace('_', ' ').title(),
                    val_str,
                    bar
                )
                row_added = True
            
            # Разделитель между категориями
            if row_added:
                table.add_row("", "", "", "")
        
        # Добавляем сводку
        summary = self.get_summary()
        table.add_row(
            "[bold yellow]Session[/bold yellow]",
            "Duration",
            f"{summary['session_duration_min']:.1f}m",
            ""
        )
        table.add_row(
            "",
            "Unique Positions",
            str(summary['unique_positions']),
            ""
        )
        
        return Panel(
            table,
            border_style="magenta",
            title="[bold]Session Stats[/bold]",
            subtitle=f"[dim]Total actions: {summary['total_actions']}[/dim]"
        )
    
    def render_history(self, limit: int = 10) -> Tree:
        """Рендерит последние события как дерево"""
        tree = Tree("[bold cyan]Recent Activity[/bold cyan]")
        
        for event in self._history[-limit:]:
            status = "✓" if event['success'] else "✗"
            time_str = time.strftime("%H:%M:%S", time.localtime(event['timestamp']))
            tree.add(f"[{time_str}] {status} [magenta]{event['action']}[/magenta] ([dim]{event['category']}[/dim])")
        
        return tree
    
    def reset(self):
        """Сброс всех счетчиков"""
        for cat in self._data:
            for key in self._data[cat]:
                if isinstance(self._data[cat][key], float):
                    self._data[cat][key] = 0.0
                else:
                    self._data[cat][key] = 0
        self._history.clear()
        self._unique_positions.clear()
        self._session_start = time.time()


# Глобальный экземпляр для использования во всем проекте
sex_stats = SexStats()

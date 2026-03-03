# body_sim/commands/base.py
from __future__ import annotations
from typing import Dict, List, Callable, Optional, Any, TYPE_CHECKING, Union
from dataclasses import dataclass, field
from collections import defaultdict

if TYPE_CHECKING:
    from body_sim.body.body import Body
    from rich.console import Console

@dataclass
class CommandContext:
    """Контекст выполнения команды."""
    body: 'Body'
    console: Optional['Console'] = None
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.console is None:
            try:
                from rich.console import Console
                self.console = Console()
            except ImportError:
                self.console = None

class CommandRegistry:
    """Реестр команд консоли."""
    
    def __init__(self):
        self._commands: Dict[str, Callable[[CommandContext], Any]] = {}
        self._aliases: Dict[str, str] = {}
        self._help_text: Dict[str, str] = {}
        self._categories: Dict[str, str] = {}  # command -> category
    
    def register(self, name: str, func: Callable[[CommandContext], Any], 
                 help_text: str = "", aliases: List[str] = None, 
                 category: str = "Общее"):
        """
        Зарегистрировать команду.
        
        Args:
            name: Имя команды
            func: Функция-обработчик
            help_text: Описание команды
            aliases: Список алиасов
            category: Категория для группировки (например: "Грудь", "Репродуктивная", "Системная")
        """
        self._commands[name] = func
        self._help_text[name] = help_text
        self._categories[name] = category
        
        if aliases:
            for alias in aliases:
                self._aliases[alias] = name
    
    def get(self, name: str) -> Optional[Callable[[CommandContext], Any]]:
        """Получить команду по имени или алиасу."""
        if name in self._commands:
            return self._commands[name]
        if name in self._aliases:
            return self._commands[self._aliases[name]]
        return None
    
    def execute(self, name: str, context: CommandContext) -> Any:
        """Выполнить команду."""
        command = self.get(name)
        if command:
            return command(context)
        return None
    
    def list_commands(self) -> List[str]:
        """Список всех команд."""
        return list(self._commands.keys())
    
    def get_help(self, name: str = None) -> Union[str, 'Table']:
        """
        Получить справку. 
        Без аргументов - возвращает Table со всеми командами по категориям.
        С аргументом - текст справки по конкретной команде.
        """
        if name is not None:
            # Конкретная команда
            if name in self._aliases:
                name = self._aliases[name]
            
            if name not in self._commands:
                return f"[red]Команда '{name}' не найдена[/]"
            
            category = self._categories.get(name, "Общее")
            aliases = [a for a, c in self._aliases.items() if c == name]
            help_text = self._help_text.get(name, "Нет описания")
            
            lines = [
                f"[bold cyan]Команда:[/] [green]{name}[/]",
                f"[bold]Категория:[/] {category}",
            ]
            if aliases:
                lines.append(f"[bold]Алиасы:[/] {', '.join(aliases)}")
            lines.append(f"[bold]Описание:[/] {help_text}")
            
            return "\n".join(lines)
        
        # Общая справка - таблица по категориям
        from rich.table import Table
        from rich import box
        
        table = Table(
            title="[bold magenta]📚 Справка по командам[/]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            padding=(0, 1)
        )
        
        table.add_column("Категория", style="cyan", width=16, no_wrap=True)
        table.add_column("Команда", style="green", width=20, no_wrap=True)
        table.add_column("Алиасы", style="dim", width=15)
        table.add_column("Описание", style="white", min_width=30)
        
        # Группируем по категориям
        cats = defaultdict(list)
        for cmd in self._commands.keys():
            cat = self._categories.get(cmd, "Общее")
            cats[cat].append(cmd)
        
        # Сортируем категории (Общее в конец)
        sorted_cats = sorted(cats.keys(), key=lambda x: (x == "Общее", x))
        
        for cat in sorted_cats:
            commands_in_cat = sorted(cats[cat])
            
            for idx, cmd in enumerate(commands_in_cat):
                # Алиасы для команды
                aliases = [a for a, c in self._aliases.items() if c == cmd]
                alias_str = "[dim]—[/]" if not aliases else ", ".join(aliases)
                
                # Описание (обрезаем если слишком длинное)
                help_txt = self._help_text.get(cmd, "Нет описания")
                if len(help_txt) > 50:
                    help_txt = help_txt[:47] + "..."
                
                # Показываем категорию только в первой строке группы
                cat_display = f"[bold]{cat}[/]" if idx == 0 else ""
                
                table.add_row(cat_display, cmd, alias_str, help_txt)
            
            # Добавляем пустую строку между категориями (кроме последней)
            if cat != sorted_cats[-1]:
                table.add_row("", "", "", "")
        
        return table
    
    def get_categories(self) -> List[str]:
        """Получить список всех категорий."""
        return list(set(self._categories.values()))
        
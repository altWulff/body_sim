# systems/commands.py

from rich.console import Console
from rich.table import Table

from body_sim.body.body import Body

class CommandContext:
    def __init__(self, body: Body, console: Console):
        self.body = body
        self.console = console
        self.last_result = None

class CommandRegistry:
    def __init__(self):
        self._commands: Dict[str, callable] = {}
        self._help_texts: Dict[str, str] = {}
        
    def register(self, name: str, func: callable, help_text: str = ""):
        self._commands[name] = func
        self._help_texts[name] = help_text
        
    def execute(self, ctx: CommandContext, cmd_line: str):
        parts = cmd_line.split()
        if not parts:
            return
        cmd, *args = parts
        if cmd in self._commands:
            try:
                ctx.last_result = self._commands[cmd](ctx, *args)
                return ctx.last_result
            except Exception as e:
                ctx.console.print(f"[red]Error: {e}[/red]")
        else:
            ctx.console.print(f"[red]Unknown command: {cmd}[/red]")
            
    def get_help(self) -> Table:
        table = Table(title="Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="green")
        for cmd, help_text in self._help_texts.items():
            table.add_row(cmd, help_text)
        return table

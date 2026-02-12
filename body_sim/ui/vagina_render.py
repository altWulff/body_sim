# body_sim/ui/vagina_render.py
from typing import TYPE_CHECKING
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

if TYPE_CHECKING:
    from body_sim.systems.penetration import PenetrableWithFluid

class VaginaRenderer:
    """Рендер статуса вагины (аналог uterus_render и breast_render)"""
    
    def render_fullness(self, vagina: 'PenetrableWithFluid', title: str = "Vagina Fullness") -> Panel:
        """Детальный рендер заполнения как у uterus"""
        fs = vagina.fluid_system
        
        # Цвет в зависимости от заполнения
        if fs.fill_percentage > 95:
            bar_color = "red"
            status = "LEAKING"
        elif fs.fill_percentage > 80:
            bar_color = "yellow"
            status = "TENSE"
        elif fs.fill_percentage > 40:
            bar_color = "green"
            status = "NORMAL"
        else:
            bar_color = "blue"
            status = "EMPTY"
            
        # Бар заполнения
        width = 30
        filled = int((fs.fill_percentage / 100) * width)
        filled = min(filled, width)
        bar = "█" * filled + "░" * (width - filled)
        
        # Состав жидкостей (из FluidMixture)
        composition = Table(show_header=False, box=None)
        composition.add_column("Type", style="cyan")
        composition.add_column("Amount", style="white", justify="right")
        
        for ft_name, amount in fs.get_composition().items():
            pct = (amount / fs.filled * 100) if fs.filled > 0 else 0
            composition.add_row(ft_name, f"{amount:.1f}ml ({pct:.0f}%)")
        
        # Инфо панель
        info = Table(show_header=False, box=None)
        info.add_column(style="dim")
        info.add_column()
        
        info.add_row("Total Volume:", f"{fs.filled:.1f}ml / {fs.max_volume:.1f}ml")
        info.add_row("Fill %:", f"[{bar_color}]{fs.fill_percentage:.1f}%[/{bar_color}]")
        info.add_row("Bar:", f"[{bar_color}]{bar}[/{bar_color}]")
        info.add_row("Status:", f"[bold {bar_color}]{status}[/bold {bar_color}]")
        info.add_row("Pressure:", f"{fs.pressure:.2f}")
        # Добавляем информацию о физических размерах
        info.add_row("Canal Length:", f"{vagina.canal_length:.1f}cm (base: {vagina._base_canal_length:.1f})")
        info.add_row("Rest Diameter:", f"{vagina.rest_diameter:.1f}cm (base: {vagina._base_rest_diameter:.1f})")
        
        # Масштаб увеличения
        if vagina.fluid_system.inflation_ratio > 1.01:
            linear_scale = vagina.fluid_system.inflation_ratio ** (1/3)
            info.add_row("Size Scale:", f"{linear_scale:.2f}x (volume: {vagina.fluid_system.inflation_ratio:.2f}x)")
        if fs.leakage > 0:
            info.add_row("[red]Leaked:[/red]", f"{fs.leakage:.1f}ml")
            
        if fs.inflation_ratio > 1.0:
            info.add_row("Inflation:", f"{fs.inflation_ratio:.2f}x")
            
        # Проникновение (если есть)
        penetration_info = ""
        if vagina.is_penetrated:
            pen_table = Table(title="[bold]Inserted Objects[/bold]", box=box.MINIMAL)
            pen_table.add_column("Name", style="cyan")
            pen_table.add_column("Depth", style="green")
            pen_table.add_column("Status")
            
            for data in vagina.inserted_objects:
                obj = data.object
                pct = (obj.inserted_depth / vagina.canal_length * 100)
                pen_table.add_row(
                    obj.name,
                    f"{obj.inserted_depth:.1f}/{vagina.canal_length}cm",
                    f"{pct:.0f}%"
                )
            penetration_info = pen_table
        else:
            penetration_info = "[dim]Empty[/dim]"
        
        # Сборка
        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_column()
        
        grid.add_row(info, composition)
        
        full_content = Table(show_header=False, box=None, expand=True)
        full_content.add_row(grid)
        full_content.add_row(Panel(penetration_info, title="Penetration", border_style="magenta"))
        
        return Panel(
            full_content,
            title=f"[bold magenta]{title}[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED
        )
    
    def render_compact(self, vagina: 'PenetrableWithFluid', label: str = "Vagina") -> str:
        """Компактный статус для списка"""
        fs = vagina.fluid_system
        fill = fs.fill_percentage
        
        # Цветной индикатор
        if fill > 95:
            color = "red"
            icon = "💧"
        elif fill > 80:
            color = "yellow"
            icon = "⚠️"
        elif fill > 40:
            color = "green"
            icon = "●"
        else:
            color = "dim"
            icon = "○"
            
        status = f"[{color}]{icon}[/{color}]"
        
        # Проникновение
        pen = "🔴" if vagina.is_penetrated else "⚪"
        
        return f"{label}: {status} {fs.filled:.0f}ml ({fill:.0f}%) {pen}"
        
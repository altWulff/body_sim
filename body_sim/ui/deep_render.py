# body_sim/ui/deep_render.py
"""
Rich-рендеринг для глубокого проникновения.
"""

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box


class DeepPenetrationRenderer:
    """Рендерер для отображения глубокого проникновения."""
    
    @staticmethod
    def render_depth_bar(current_depth: float, max_depth: float = 35.0, width: int = 40) -> str:
        """Создать ASCII-бар глубины."""
        filled = int((current_depth / max_depth) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {current_depth:.1f}см"
    
    @staticmethod
    def render_anatomy_path(encounter) -> Table:
        """Показать путь через анатомию."""
        table = Table(box=box.ROUNDED, title="Анатомический путь")
        table.add_column("Зона", style="cyan")
        table.add_column("Статус", style="green")
        table.add_column("Особенности", style="yellow")
        
        zones = [
            ("Вход", "✓ Пройдено" if encounter.state.current_depth > 0 else "➤ Текущее", ""),
            ("Влагалище", "✓" if encounter.state.current_depth > 5 else "○", ""),
            ("Шейка матки", "✓" if encounter.state.is_through_cervix else "○", 
             "Закрыта" if not encounter.state.is_through_cervix else "Проникновение"),
            ("Матка", "✓" if encounter.state.is_in_uterus else "○",
             f"{'Внутри' if encounter.state.is_in_uterus else ''}"),
            ("Трубы", "✓" if encounter.state.is_in_tube else "○",
             f"{encounter.state.tube_side}" if encounter.state.is_in_tube else ""),
            ("Яичники", "✓" if encounter.state.is_at_ovary else "○",
             "Контакт" if encounter.state.is_at_ovary else ""),
        ]
        
        for zone, status, note in zones:
            table.add_row(zone, status, note)
        
        return table
    
    @staticmethod
    def render_risk_assessment(encounter) -> Panel:
        """Оценка рисков."""
        from body_sim.systems.advanced_penetration import ProlapseRiskCalculator
        
        content = []
        
        if encounter.uterus_ref:
            risk, factors = ProlapseRiskCalculator.calculate_uterine_prolapse_risk(
                encounter.state, encounter.uterus_ref, 0.5
            )
            color = "red" if risk > 0.6 else "yellow" if risk > 0.3 else "green"
            content.append(f"[{color}]Риск пролапса матки: {risk:.0%}[/{color}]")
            if risk > 0.2:
                content.append(f"[dim]{factors}[/dim]")
        
        if encounter.ovary_ref and encounter.tube_ref:
            risk, factors = ProlapseRiskCalculator.calculate_ovary_eversion_risk(
                encounter.state, encounter.tube_ref, encounter.ovary_ref, 0.5
            )
            color = "red" if risk > 0.6 else "yellow" if risk > 0.3 else "green"
            content.append(f"[{color}]Риск выворота яичника: {risk:.0%}[/{color}]")
        
        return Panel("\n".join(content) if content else "[dim]Низкий риск[/dim]", 
                    title="⚠️ Оценка рисков", border_style="red")
    
    @staticmethod
    def render_full_status(encounter) -> Panel:
        """Полный статус."""
        depth_bar = DeepPenetrationRenderer.render_depth_bar(
            encounter.state.current_depth
        )
        
        text = Text()
        text.append(f"Глубина: {encounter.state.current_depth:.1f}см\n")
        text.append(f"Зона: {encounter.state.current_zone.name}\n\n")
        text.append(depth_bar + "\n\n")
        
        if encounter.state.is_in_uterus:
            text.append("[red]Внутри матки[/red]\n")
        if encounter.state.is_in_tube:
            text.append(f"[red]В {encounter.state.tube_side} трубе[/red]\n")
        if encounter.state.is_at_ovary:
            text.append("[magenta]Контакт с яичником[/magenta]\n")
        
        return Panel(text, title=f"{encounter.source_body.name} → {encounter.target_body.name}")
        
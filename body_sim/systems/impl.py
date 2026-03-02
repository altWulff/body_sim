# systems/impl.py

from rich.table import Table
from body_sim.systems.commands import CommandRegistry, CommandContext
from body_sim.core.events import Event, EventType  # Добавлен импорт


def register_all_commands(registry: CommandRegistry):
    
    # --- Reproductive commands ---
    def cmd_uterus_show(ctx: CommandContext):
        """Показать состояние всех маток"""
        if not ctx.body.reproductive_system or not ctx.body.reproductive_system.uteri:
            ctx.console.print("[red]No reproductive system or uteri[/red]")
            return
            
        for idx, u in enumerate(ctx.body.reproductive_system.uteri):
            table = Table(title=f"Uterus {idx}")
            table.add_column("Parameter", style="cyan")
            table.add_column("Value", style="yellow")
            table.add_row("Status", u.inflation_status.value)
            table.add_row("Wall Stretch", f"{u.walls.stretch_ratio:.1f}x")
            table.add_row("Inflation", f"{u.inflation_ratio:.1f}x")
            table.add_row("Fullness", f"{u.get_fullness()*100:.1f}%")
            table.add_row("Cervix Dilation", f"{u.cervix.current_dilation:.1f}cm")
            table.add_row("Cervix Open", str(u.cervix.is_open))
            table.add_row("Prolapse", u.state.name if u.state else "normal")
            ctx.console.print(table)
        
    def cmd_uterus_fullness(ctx: CommandContext, idx: str = "0"):
        """Детальная заполненность матки по индексу"""
        if not ctx.body.reproductive_system:
            return
            
        try:
            u = ctx.body.reproductive_system.uteri[int(idx)]
        except (IndexError, ValueError):
            ctx.console.print(f"[red]Invalid uterus index: {idx}[/red]")
            return
            
        if not u.fluids:
            ctx.console.print("[yellow]Empty[/yellow]")
            return
            
        table = Table(title=f"Uterus {idx} Contents")
        table.add_column("Type")
        table.add_column("Volume")
        table.add_column("Source")
        for f in u.fluids:
            table.add_row(f.fluid_type.value, f"{f.volume:.1f}ml", f.source_component)
        ctx.console.print(table)
        
    def cmd_uterus_inflate(ctx: CommandContext, ratio: str, idx: str = "0"):
        """Инфлировать матку: uterus.inflate <ratio> [index]"""
        if not ctx.body.reproductive_system:
            return
            
        try:
            u = ctx.body.reproductive_system.uteri[int(idx)]
            success = u.inflate(float(ratio))
            ctx.console.print(f"[green]Inflated uterus {idx}: {success}[/green]")
        except (IndexError, ValueError) as e:
            ctx.console.print(f"[red]Error: {e}[/red]")
        
    def cmd_ovaries_show(ctx: CommandContext):
        """Показать яичники"""
        if not ctx.body.reproductive_system:
            return
            
        for idx, u in enumerate(ctx.body.reproductive_system.uteri):
            if u.left_ovary:
                table = Table(title=f"Ovary (Uterus {idx}, Left)")
                table.add_row("Side", u.left_ovary.side)
                table.add_row("Follicles", str(u.left_ovary.follicle_count))
                table.add_row("Hormone", f"{u.left_ovary.hormone_production:.2f}")
                table.add_row("Everted", str(u.left_ovary.is_everted))
                ctx.console.print(table)
                
            if u.right_ovary:
                table = Table(title=f"Ovary (Uterus {idx}, Right)")
                table.add_row("Side", u.right_ovary.side)
                table.add_row("Follicles", str(u.right_ovary.follicle_count))
                table.add_row("Hormone", f"{u.right_ovary.hormone_production:.2f}")
                table.add_row("Everted", str(u.right_ovary.is_everted))
                ctx.console.print(table)
        
    def cmd_tubes_show(ctx: CommandContext):
        """Состояние маточных труб"""
        if not ctx.body.reproductive_system:
            return
            
        for idx, u in enumerate(ctx.body.reproductive_system.uteri):
            if u.left_tube:
                ctx.console.print(f"Uterus {idx} - Left Tube: {u.left_tube.current_length:.1f}cm, "
                                f"fluid: {u.left_tube.contained_fluid:.1f}ml")
            if u.right_tube:
                ctx.console.print(f"Uterus {idx} - Right Tube: {u.right_tube.current_length:.1f}cm, "
                                f"fluid: {u.right_tube.contained_fluid:.1f}ml")
            
    def cmd_vagina_show(ctx: CommandContext):
        """Показать влагалища"""
        if not ctx.body.reproductive_system or not ctx.body.reproductive_system.vaginas:
            ctx.console.print("[red]No vaginas[/red]")
            return
            
        for idx, v in enumerate(ctx.body.reproductive_system.vaginas):
            table = Table(title=f"Vagina {idx}")
            table.add_row("Type", v.vagina_type.type_name)
            table.add_row("Depth", f"{v.current_depth:.1f}cm")
            table.add_row("Width", f"{v.current_width:.1f}cm")
            table.add_row("Stretch", f"{v.current_stretch:.2f}x")
            table.add_row("Lubrication", f"{v.lubrication*100:.0f}%")
            table.add_row("Aroused", str(v.is_aroused))
            ctx.console.print(table)
            
    def cmd_vagina_stimulate(ctx: CommandContext, intensity: str = "0.5", idx: str = "0"):
        """Стимуляция вагины: vagina.stimulate [intensity] [index]"""
        if not ctx.body.reproductive_system:
            return
            
        try:
            v = ctx.body.reproductive_system.vaginas[int(idx)]
            v.stimulate(float(intensity))
            ctx.console.print(f"[green]Stimulated vagina {idx}, arousal: {v.arousal:.1%}[/green]")
        except (IndexError, ValueError):
            ctx.console.print(f"[red]Invalid vagina index: {idx}[/red]")
            
    def cmd_clitoris_show(ctx: CommandContext):
        """Показать клиторы"""
        if not ctx.body.reproductive_system or not ctx.body.reproductive_system.clitorises:
            return
            
        for idx, c in enumerate(ctx.body.reproductive_system.clitorises):
            table = Table(title=f"Clitoris {idx}")
            table.add_row("Length", f"{c.current_length:.1f}cm")
            table.add_row("Erect", str(c.is_erect))
            table.add_row("Enlarged", str(c.is_enlarged))
            table.add_row("Can Transform", str(c.can_transform))
            table.add_row("Transformed", str(c.is_transformed))
            ctx.console.print(table)
            
    def cmd_clitoris_transform(ctx: CommandContext, idx: str = "0", length: str = "10.0", girth: str = "8.0"):
        """Трансформация клитора в пенис: clitoris.transform [index] [length] [girth]"""
        if not ctx.body.reproductive_system:
            return
            
        try:
            c = ctx.body.reproductive_system.clitorises[int(idx)]
            if not c.can_transform:
                ctx.console.print("[red]This clitoris cannot transform[/red]")
                return
                
            penis = c.transform_to_penis(float(length), float(girth))
            ctx.body.reproductive_system.add_penis(penis)
            ctx.console.print(f"[green]Transformed clitoris {idx} into penis (length: {length}cm)[/green]")
        except (IndexError, ValueError) as e:
            ctx.console.print(f"[red]Error: {e}[/red]")
            
    def cmd_penis_show(ctx: CommandContext):
        """Показать пенисы"""
        if not ctx.body.reproductive_system or not ctx.body.reproductive_system.penises:
            ctx.console.print("[yellow]No penises[/yellow]")
            return
            
        for idx, p in enumerate(ctx.body.reproductive_system.penises):
            table = Table(title=f"Penis {idx}")
            table.add_row("Length", f"{p.current_length:.1f}cm")
            table.add_row("Girth", f"{p.current_girth:.1f}cm")
            table.add_row("Erect", str(p.is_erect))
            table.add_row("Transformed", str(p.is_transformed_clitoris))
            table.add_row("Has Scrotum", str(p.has_scrotum()))
            ctx.console.print(table)
            
    def cmd_penis_ejaculate(ctx: CommandContext, idx: str = "0"):
        """Эякуляция: penis.ejaculate [index]"""
        if not ctx.body.reproductive_system:
            return
            
        try:
            p = ctx.body.reproductive_system.penises[int(idx)]
            result = p.ejaculate()
            if result["amount"] > 0:
                ctx.console.print(f"[green]Ejaculate: {result['amount']:.1f}ml, "
                                f"{result['pulses']} pulses[/green]")
            else:
                ctx.console.print(f"[yellow]No ejaculate: {result['reason']}[/yellow]")
        except (IndexError, ValueError) as e:
            ctx.console.print(f"[red]Error: {e}[/red]")
            
    def cmd_scrotum_show(ctx: CommandContext):
        """Показать мошонки"""
        if not ctx.body.reproductive_system or not ctx.body.reproductive_system.scrotums:
            return
            
        for idx, s in enumerate(ctx.body.reproductive_system.scrotums):
            table = Table(title=f"Scrotum {idx}")
            table.add_row("Testicles", str(len(s.testicles)))
            table.add_row("Stored", f"{s.total_stored:.1f}ml")
            table.add_row("Internal", str(s.is_internal))
            ctx.console.print(table)
            
    # --- Appearance commands ---
    def cmd_appearance_show(ctx: CommandContext):
        if ctx.body.appearance:
            ctx.console.print(ctx.body.appearance.get_description())
            
    def cmd_body_state(ctx: CommandContext):
        """Общее состояние тела"""
        table = Table(title=f"Body: {ctx.body.name}")
        table.add_row("Sex", ctx.body.sex.name)
        table.add_row("Race", ctx.body.race.value)
        table.add_row("Arousal", f"{ctx.body.reproductive_system.vaginas[0].arousal:.1%}" 
                     if ctx.body.reproductive_system and ctx.body.reproductive_system.vaginas else "N/A")
        ctx.console.print(table)
        
    # Register all
    registry.register("uterus.show", cmd_uterus_show, "Show all uteri status")
    registry.register("uterus.fullness", cmd_uterus_fullness, "Show uterus contents by index")
    registry.register("uterus.inflate", cmd_uterus_inflate, "Inflate uterus (ratio) [index]")
    registry.register("ovaries.show", cmd_ovaries_show, "Show ovaries")
    registry.register("tubes.show", cmd_tubes_show, "Show fallopian tubes")
    registry.register("vagina.show", cmd_vagina_show, "Show vaginas")
    registry.register("vagina.stimulate", cmd_vagina_stimulate, "Stimulate vagina [intensity] [index]")
    registry.register("clitoris.show", cmd_clitoris_show, "Show clitorises")
    registry.register("clitoris.transform", cmd_clitoris_transform, "Transform clitoris to penis [index] [length] [girth]")
    registry.register("penis.show", cmd_penis_show, "Show penises")
    registry.register("penis.ejaculate", cmd_penis_ejaculate, "Ejaculate [index]")
    registry.register("scrotum.show", cmd_scrotum_show, "Show scrotums")
    registry.register("appearance.show", cmd_appearance_show, "Show appearance")
    registry.register("body.state", cmd_body_state, "Show body state")
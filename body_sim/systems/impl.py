# systems/impl.py

from rich.table import Table

from body_sim.systems.commands import CommandRegistry, CommandContext


def register_all_commands(registry: CommandRegistry):
    
    # --- Reproductive commands ---
    def cmd_uterus_show(ctx: CommandContext):
        """Показать состояние матки"""
        if not ctx.body.reproductive:
            return "No reproductive system"
        u = ctx.body.reproductive.uterus
        table = Table(title="Uterus")
        table.add_row("Fullness", f"{u.get_fullness()*100:.1f}%")
        table.add_row("Cervix Dilation", f"{u.cervix_dilation}cm")
        table.add_row("Inverted", str(u.is_inverted))
        table.add_row("Prolapse", str(u.prolapse_stage))
        ctx.body.stats.record("commands", "uterus_show")
        ctx.console.print(table)
        
    def cmd_uterus_fullness(ctx: CommandContext):
        """Детальная заполненность матки"""
        if not ctx.body.reproductive:
            return
        u = ctx.body.reproductive.uterus
        if not u.fluids:
            ctx.console.print("[yellow]Empty[/yellow]")
            return
        table = Table(title="Uterus Contents")
        table.add_column("Type")
        table.add_column("Volume")
        table.add_column("Source")
        for f in u.fluids:
            table.add_row(f.fluid_type.value, f"{f.volume:.1f}ml", f.source_component)
        ctx.console.print(table)
        
    def cmd_ovaries_show(ctx: CommandContext):
        """Показать яичники"""
        if not ctx.body.reproductive:
            return
        sys = ctx.body.reproductive
        table = Table(title="Ovaries")
        table.add_column("Side")
        table.add_column("Type")
        table.add_column("Gametes")
        table.add_column("Hormones")
        
        for ovary in [sys.left_ovary, sys.right_ovary]:
            t = "Testis" if ovary.is_testis else "Ovary"
            table.add_row(
                ovary.side, t, 
                str(len(ovary.gametes)),
                f"E:{ovary.hormone_estrogen:.1f}"
            )
        ctx.console.print(table)
        
    def cmd_ovaries_transform(ctx: CommandContext, side: str):
        """Трансформация яичника в яичко"""
        if not ctx.body.reproductive:
            return
        target = ctx.body.reproductive.left_ovary if side == "left" else ctx.body.reproductive.right_ovary
        target.transform_to_testis()
        ctx.body.event_bus.emit(Event(
            type=EventType.TRANSFORMATION,
            source=target.component_id,
            data={'to': 'testis'}
        ))
        ctx.console.print(f"[green]{side} ovary transformed to testis[/green]")
        
    def cmd_tubes_show(ctx: CommandContext):
        """Состояние маточных труб"""
        if not ctx.body.reproductive:
            return
        sys = ctx.body.reproductive
        for tube in [sys.left_tube, sys.right_tube]:
            ctx.console.print(f"{tube.side}: {tube.length}cm, activity: {tube.cilia_activity}")
            
    def cmd_vagina_penetration(ctx: CommandContext, depth: str, diameter: str = "3"):
        """Проникновение в вагину"""
        if not ctx.body.reproductive:
            return
        result = ctx.body.reproductive.vagina.penetrate(
            float(depth), float(diameter), "object", ctx.body.event_bus
        )
        ctx.console.print(f"Penetration: {result['depth']}cm, cervix: {result['cervix_contact']}")
        
    def cmd_vagina_stimulate(ctx: CommandContext, intensity: str = "10"):
        """Стимуляция вагины"""
        if ctx.body.reproductive:
            ctx.body.reproductive.vagina.stimulate(float(intensity))
            
    # --- Appearance commands ---
    def cmd_appearance_show(ctx: CommandContext):
        if ctx.body.appearance:
            ctx.console.print(ctx.body.appearance.get_description())
            
    # --- Breast commands ---
    def cmd_breasts_show(ctx: CommandContext):
        if not ctx.body.reproductive or not ctx.body.reproductive.breasts:
            return
        b = ctx.body.reproductive.breasts
        table = Table(title="Breasts")
        table.add_column("Row")
        table.add_column("Size")
        table.add_column("Milk")
        table.add_column("Plug")
        for row in b.rows:
            table.add_row(
                str(row.index), 
                f"{row.size:.1f}",
                f"{row.milk_volume:.0f}/{row.max_milk:.0f}ml",
                row.nipple_plug or "None"
            )
        ctx.console.print(table)
        
    def cmd_lactation_start(ctx: CommandContext, row: str = "0"):
        if ctx.body.reproductive and ctx.body.reproductive.breasts:
            ctx.body.reproductive.breasts.start_lactation(int(row))
            ctx.console.print(f"[green]Lactation started[/green]")
            
    def cmd_nipple_plug(ctx: CommandContext, row: str, plug_type: str):
        if ctx.body.reproductive and ctx.body.reproductive.breasts:
            idx = int(row)
            if 0 <= idx < len(ctx.body.reproductive.breasts.rows):
                ctx.body.reproductive.breasts.rows[idx].nipple_plug = plug_type
                
    # --- Digestive commands ---
    def cmd_anus_show(ctx: CommandContext):
        if ctx.body.digestive:
            a = ctx.body.digestive.anus
            ctx.console.print(f"Dilation: {a.diameter:.1f}cm, tone: {a.sphincter_tone}")
            
    def cmd_stomach_show(ctx: CommandContext):
        if ctx.body.digestive:
            s = ctx.body.digestive.stomach
            ctx.console.print(f"Fullness: {s.get_fullness()*100:.1f}%, pH: {s.ph_level}")
            
    def cmd_mouth_show(ctx: CommandContext):
        if ctx.body.digestive:
            m = ctx.body.digestive.mouth
            ctx.console.print(f"Opening: {m.jaw_opening:.1f}cm")
            
    # --- Stats ---
    def cmd_stats_show(ctx: CommandContext):
        ctx.console.print(ctx.body.stats.report())
        
    # Register all
    registry.register("uterus.show", cmd_uterus_show, "Show uterus status")
    registry.register("uterus.fullness", cmd_uterus_fullness, "Show uterus contents")
    registry.register("ovaries.show", cmd_ovaries_show, "Show ovaries")
    registry.register("ovaries.transform", cmd_ovaries_transform, "Transform ovary to testis (left|right)")
    registry.register("tubes.show", cmd_tubes_show, "Show fallopian tubes")
    registry.register("vagina.penetrate", cmd_vagina_penetration, "Penetrate vagina (depth) [diameter]")
    registry.register("vagina.stimulate", cmd_vagina_stimulate, "Stimulate vagina [intensity]")
    registry.register("appearance.show", cmd_appearance_show, "Show appearance")
    registry.register("breasts.show", cmd_breasts_show, "Show breasts")
    registry.register("breasts.lactate", cmd_lactation_start, "Start lactation [row]")
    registry.register("nipple.plug", cmd_nipple_plug, "Insert plug (row) (type)")
    registry.register("anus.show", cmd_anus_show, "Show anus status")
    registry.register("stomach.show", cmd_stomach_show, "Show stomach")
    registry.register("mouth.show", cmd_mouth_show, "Show mouth")
    registry.register("stats.show", cmd_stats_show, "Show statistics")

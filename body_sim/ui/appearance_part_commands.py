# body_sim/ui/appearance_part_commands.py
"""
Команды для управления внешностью анатомических частей:
рот (mouth), живот (belly), анус (anus).
"""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def _safe_enum_str(enum_val):
    """Безопасное преобразование Enum в строку."""
    if enum_val is None:
        return "none"
    if isinstance(enum_val, str):
        return enum_val
    # Пробуем получить .value
    val = getattr(enum_val, 'value', None)
    if val is not None:
        return str(val)
    # Пробуем получить .name если это Enum
    name = getattr(enum_val, 'name', None)
    if name is not None:
        return name.lower()
    return str(enum_val)


class AppearancePartCommands:
    """Команды для внешности частей тела."""
    
    def __init__(self, registry):
        self.registry = registry
        self._register_commands()
    
    def _register_commands(self):
        """Зарегистрировать все команды."""
        try:
            from body_sim.ui.commands import Command, CommandContext
            
            # Команда рта
            self.registry.register(Command(
                "mouth_appearance", ["mouth_app", "mapp"],
                "Show/change mouth appearance",
                "mouth_appearance [status|update|fullness|color|piercing]",
                self.cmd_mouth_appearance,
                "appearance"
            ))
            
            # Команда живота
            self.registry.register(Command(
                "belly_appearance", ["belly_app", "bapp"],
                "Show/change belly appearance",
                "belly_appearance [status|update|shape|button|size|muscle|tan]",
                self.cmd_belly_appearance,
                "appearance"
            ))
            
            # Команда ануса
            self.registry.register(Command(
                "anus_appearance", ["anus_app", "aapp"],
                "Show/change anus appearance",
                "anus_appearance [idx] [status|update|type|color|hair|piercing|reset]",
                self.cmd_anus_appearance,
                "appearance"
            ))
            
            # Общая команда для всех частей
            self.registry.register(Command(
                "body_parts_appearance", ["parts_app", "papp"],
                "Show all body parts appearance",
                "body_parts_appearance [update]",
                self.cmd_all_parts_appearance,
                "appearance"
            ))
        except Exception as e:
            console.print(f"[red]Error registering appearance commands: {e}[/red]")

    def _get_or_create_appearance_parts(self, body):
        """Получить или создать appearance_parts для тела."""
        if not hasattr(body, 'appearance_parts') or body.appearance_parts is None:
            try:
                # Пытаемся импортировать классы
                from body_sim.appearance.body_parts import (
                    MouthAppearance, BellyAppearance, AnusAppearance
                )
                body.appearance_parts = {
                    'mouth': MouthAppearance(),
                    'belly': BellyAppearance(),
                    'anus': AnusAppearance()
                }
            except ImportError:
                try:
                    from appearance.body_parts import (
                        MouthAppearance, BellyAppearance, AnusAppearance
                    )
                    body.appearance_parts = {
                        'mouth': MouthAppearance(),
                        'belly': BellyAppearance(),
                        'anus': AnusAppearance()
                    }
                except ImportError as e:
                    console.print(f"[red]Cannot import body_parts classes: {e}[/red]")
                    raise
        return body.appearance_parts

    # ============ MOUTH COMMANDS ============
    
    def cmd_mouth_appearance(self, args: List[str], ctx):
        """Управление внешностью рта."""
        if not ctx.active_body:
            console.print("[red]No body selected[/red]")
            return
        
        try:
            app_parts = self._get_or_create_appearance_parts(ctx.active_body)
            mouth_app = app_parts.get('mouth')
            
            if not args:
                self._show_mouth_status(mouth_app, ctx.active_body)
                return
            
            action = args[0].lower()
            action_args = args[1:]
            
            if action in ("status", "s"):
                self._show_mouth_status(mouth_app, ctx.active_body)
                
            elif action in ("update", "u"):
                self._update_mouth_from_anatomy(mouth_app, ctx.active_body)
                
            elif action == "fullness":
                self._set_mouth_fullness(mouth_app, action_args)
                    
            elif action == "color":
                self._set_mouth_color(mouth_app, action_args)
                
            elif action == "piercing":
                self._set_mouth_piercing(mouth_app, action_args)
            
            elif action == "lips":
                self._modify_lips(mouth_app, action_args)
                
            else:
                console.print(f"[red]Unknown action: {action}[/red]")
                console.print("[dim]Actions: status, update, fullness, color, piercing, lips[/dim]")
                
        except Exception as e:
            console.print(f"[red]Error in mouth_appearance: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")

    def _update_mouth_from_anatomy(self, mouth_app, body):
        """Обновить внешность рта из anatomy."""
        try:
            if hasattr(body, 'mouth_system') and body.mouth_system:
                mouth = body.mouth_system.primary if hasattr(body.mouth_system, 'primary') else body.mouth_system
                if mouth and hasattr(mouth_app, 'update_from_mouth'):
                    mouth_app.update_from_mouth(mouth)
                    console.print("[green]✓ Mouth appearance updated from anatomy[/green]")
                    self._show_mouth_status(mouth_app, body)
                else:
                    console.print("[yellow]No mouth anatomy found[/yellow]")
            else:
                console.print("[yellow]No mouth system found[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Update warning: {e}[/yellow]")

    def _set_mouth_fullness(self, mouth_app, action_args):
        """Установить полноту губ."""
        if not action_args:
            current = _safe_enum_str(getattr(mouth_app, 'lip_fullness', None))
            console.print(f"[cyan]Current lip fullness: {current}[/cyan]")
            console.print("[dim]Options: thin, average, full, very_full, inflated[/dim]")
            return
        
        try:
            # Пробуем разные пути импорта
            try:
                from body_sim.appearance.body_parts import LipFullness
            except ImportError:
                from appearance.body_parts import LipFullness
            
            fullness = LipFullness[action_args[0].upper()]
            mouth_app.lip_fullness = fullness
            console.print(f"[green]Lip fullness set to: {_safe_enum_str(fullness)}[/green]")
        except (KeyError, ImportError) as e:
            console.print(f"[red]Invalid fullness. Options: thin, average, full, very_full, inflated[/red]")

    def _set_mouth_color(self, mouth_app, action_args):
        """Установить цвет губ."""
        if not action_args:
            current = _safe_enum_str(getattr(mouth_app, 'lip_color', None))
            console.print(f"[cyan]Current lip color: {current}[/cyan]")
            return
        
        try:
            try:
                from body_sim.appearance.body_parts import LipColor
            except ImportError:
                from appearance.body_parts import LipColor
            
            color = LipColor[action_args[0].upper()]
            mouth_app.lip_color = color
            console.print(f"[green]Lip color set to: {_safe_enum_str(color)}[/green]")
        except (KeyError, ImportError):
            console.print(f"[red]Invalid color[/red]")

    def _set_mouth_piercing(self, mouth_app, action_args):
        """Установить пирсинги."""
        if not action_args:
            count = getattr(mouth_app, 'lip_piercing_count', 0)
            has = getattr(mouth_app, 'has_lip_piercing', False)
            console.print(f"[cyan]Lip piercing: {'Yes' if has else 'No'} ({count})[/cyan]")
            return
        
        try:
            count = int(action_args[0])
            mouth_app.lip_piercing_count = count
            mouth_app.has_lip_piercing = count > 0
            console.print(f"[green]Lip piercings set to: {count}[/green]")
        except ValueError:
            console.print("[red]Invalid number[/red]")

    def _show_mouth_status(self, mouth_app, body):
        """Показать статус внешности рта."""
        try:
            table = Table(show_header=True, box=box.ROUNDED, title="Mouth Appearance")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="magenta")
            
            fullness = _safe_enum_str(getattr(mouth_app, 'lip_fullness', None))
            color = _safe_enum_str(getattr(mouth_app, 'lip_color', None))
            upper = getattr(mouth_app, 'upper_lip_thickness', 0.8)
            lower = getattr(mouth_app, 'lower_lip_thickness', 1.0)
            softness = getattr(mouth_app, 'lip_softness', 0.7)
            stretch = getattr(mouth_app, 'max_stretch_ratio', 3.0)
            stretch_marks = getattr(mouth_app, 'stretch_marks', False)
            opening = getattr(mouth_app, 'current_opening', 0.0)
            is_open = getattr(mouth_app, 'is_open', False)
            is_stretched = getattr(mouth_app, 'is_stretched', False)
            piercing_count = getattr(mouth_app, 'lip_piercing_count', 0)
            has_piercing = getattr(mouth_app, 'has_lip_piercing', False)
            lipstick = getattr(mouth_app, 'lipstick_color', None)
            has_lipstick = getattr(mouth_app, 'lipstick_applied', False)
            
            table.add_row("Lip Fullness", fullness)
            table.add_row("Upper Lip", f"{upper:.1f}cm")
            table.add_row("Lower Lip", f"{lower:.1f}cm")
            table.add_row("Lip Color", color)
            table.add_row("Softness", f"{softness:.1%}")
            table.add_row("Max Stretch", f"×{stretch:.1f}")
            table.add_row("Stretch Marks", "Yes" if stretch_marks else "No")
            table.add_row("Current Opening", f"{opening:.1f}cm")
            table.add_row("State", f"{'Open' if is_open else 'Closed'}, {'Stretched' if is_stretched else 'Normal'}")
            table.add_row("Piercings", str(piercing_count) if has_piercing else "None")
            table.add_row("Lipstick", lipstick if has_lipstick and lipstick else "None")
            
            console.print(table)
            
            # Описание
            if hasattr(mouth_app, 'get_description'):
                desc = mouth_app.get_description()
                if desc:
                    console.print(f"\n[dim]Description: {desc}[/dim]")
        except Exception as e:
            console.print(f"[red]Error displaying mouth status: {e}[/red]")

    def _modify_lips(self, mouth_app, args):
        """Изменить параметры губ."""
        if len(args) < 2:
            console.print("[red]Usage: mouth_appearance lips <property> <value>[/red]")
            console.print("Properties: upper, lower, softness, stretch")
            return
        
        prop = args[0].lower()
        try:
            value = float(args[1])
            if prop == "upper":
                mouth_app.upper_lip_thickness = value
                console.print(f"[green]Upper lip thickness: {value}cm[/green]")
            elif prop == "lower":
                mouth_app.lower_lip_thickness = value
                console.print(f"[green]Lower lip thickness: {value}cm[/green]")
            elif prop == "softness":
                mouth_app.lip_softness = max(0.0, min(1.0, value))
                console.print(f"[green]Lip softness: {value}[/green]")
            elif prop == "stretch":
                mouth_app.max_stretch_ratio = value
                console.print(f"[green]Max stretch ratio: ×{value}[/green]")
            else:
                console.print(f"[red]Unknown property: {prop}[/red]")
        except ValueError:
            console.print("[red]Value must be a number[/red]")

    # ============ BELLY COMMANDS ============
    
    def cmd_belly_appearance(self, args: List[str], ctx):
        """Управление внешностью живота."""
        if not ctx.active_body:
            console.print("[red]No body selected[/red]")
            return
        
        try:
            app_parts = self._get_or_create_appearance_parts(ctx.active_body)
            belly_app = app_parts.get('belly')
            
            if not args:
                self._show_belly_status(belly_app, ctx.active_body)
                return
            
            action = args[0].lower()
            action_args = args[1:]
            
            if action in ("status", "s"):
                self._show_belly_status(belly_app, ctx.active_body)
                
            elif action in ("update", "u"):
                self._update_belly_from_anatomy(belly_app, ctx.active_body)
            
            elif action == "shape":
                self._set_belly_shape(belly_app, action_args)
                    
            elif action == "button":
                self._set_belly_button(belly_app, action_args)
                    
            elif action == "size":
                self._set_belly_size(belly_app, action_args)
                    
            elif action == "muscle":
                self._set_muscle_definition(belly_app, action_args)
                    
            elif action == "tan":
                self._toggle_tan(belly_app)
                
            else:
                console.print(f"[red]Unknown action: {action}[/red]")
                console.print("[dim]Actions: status, update, shape, button, size, muscle, tan[/dim]")
                
        except Exception as e:
            console.print(f"[red]Error in belly_appearance: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")

    def _update_belly_from_anatomy(self, belly_app, body):
        """Обновить внешность живота из anatomy."""
        try:
            if hasattr(body, 'stomach_system') and body.stomach_system:
                stomach = body.stomach_system.primary if hasattr(body.stomach_system, 'primary') else body.stomach_system
                if stomach and hasattr(belly_app, 'update_from_stomach'):
                    belly_app.update_from_stomach(stomach)
                    console.print("[green]✓ Belly appearance updated from stomach[/green]")
                    self._show_belly_status(belly_app, body)
                else:
                    console.print("[yellow]No stomach found[/yellow]")
            else:
                console.print("[yellow]No stomach system found[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Update warning: {e}[/yellow]")

    def _set_belly_shape(self, belly_app, action_args):
        """Установить форму живота."""
        if not action_args:
            base = _safe_enum_str(getattr(belly_app, 'base_shape', None))
            current = _safe_enum_str(getattr(belly_app, 'current_shape', None))
            console.print(f"[cyan]Base shape: {base}[/cyan]")
            console.print(f"[cyan]Current shape: {current}[/cyan]")
            console.print("[dim]Options: flat, slim, soft, rounded, pot, pregnant, inflated, distended, muscular[/dim]")
            return
        
        try:
            try:
                from body_sim.appearance.body_parts import BellyShape
            except ImportError:
                from appearance.body_parts import BellyShape
            
            shape = BellyShape[action_args[0].upper()]
            belly_app.base_shape = shape
            console.print(f"[green]Base belly shape set to: {_safe_enum_str(shape)}[/green]")
        except (KeyError, ImportError):
            console.print(f"[red]Invalid shape. Options: flat, slim, soft, rounded, pot, pregnant, inflated, distended, muscular[/red]")

    def _set_belly_button(self, belly_app, action_args):
        """Установить тип пупка."""
        if not action_args:
            btn = _safe_enum_str(getattr(belly_app, 'belly_button', None))
            depth = getattr(belly_app, 'belly_button_depth', 1.5)
            console.print(f"[cyan]Belly button: {btn} ({depth:.1f}cm)[/cyan]")
            return
        
        try:
            try:
                from body_sim.appearance.body_parts import BellyButtonType
            except ImportError:
                from appearance.body_parts import BellyButtonType
            
            btn_type = BellyButtonType[action_args[0].upper()]
            belly_app.belly_button = btn_type
            console.print(f"[green]Belly button set to: {_safe_enum_str(btn_type)}[/green]")
        except (KeyError, ImportError):
            console.print("[red]Invalid type. Options: innie, outie, flat[/red]")

    def _set_belly_size(self, belly_app, action_args):
        """Установить размер живота."""
        if not action_args:
            base = getattr(belly_app, 'base_size', 0.0)
            current = getattr(belly_app, 'current_size', 0.0)
            console.print(f"[cyan]Base size: {base:.1f}cm | Current: {current:.1f}cm[/cyan]")
            return
        
        try:
            size = float(action_args[0])
            belly_app.base_size = size
            console.print(f"[green]Base belly size: {size}cm protrusion[/green]")
        except ValueError:
            console.print("[red]Invalid number[/red]")

    def _set_muscle_definition(self, belly_app, action_args):
        """Установить рельеф мышц."""
        if not action_args:
            muscle = getattr(belly_app, 'muscle_definition', 0.0)
            console.print(f"[cyan]Muscle definition: {muscle:.1%}[/cyan]")
            return
        
        try:
            val = float(action_args[0])
            belly_app.muscle_definition = max(0.0, min(1.0, val))
            console.print(f"[green]Muscle definition: {val}[/green]")
        except ValueError:
            console.print("[red]Invalid number (0-1)[/red]")

    def _toggle_tan(self, belly_app):
        """Переключить загар."""
        current = getattr(belly_app, 'is_tanned', False)
        belly_app.is_tanned = not current
        status = "tanned" if belly_app.is_tanned else "not tanned"
        console.print(f"[green]Belly is now {status}[/green]")

    def _show_belly_status(self, belly_app, body):
        """Показать статус внешности живота."""
        try:
            table = Table(show_header=True, box=box.ROUNDED, title="Belly Appearance")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="magenta")
            
            base_shape = _safe_enum_str(getattr(belly_app, 'base_shape', None))
            current_shape = _safe_enum_str(getattr(belly_app, 'current_shape', None))
            base_size = getattr(belly_app, 'base_size', 0.0)
            current_size = getattr(belly_app, 'current_size', 0.0)
            inflation = getattr(belly_app, 'inflation_ratio', 1.0)
            fill = getattr(belly_app, 'fill_ratio', 0.0)
            btn = _safe_enum_str(getattr(belly_app, 'belly_button', None))
            btn_depth = getattr(belly_app, 'belly_button_depth', 1.5)
            skin = getattr(belly_app, 'skin_texture', 'smooth')
            marks = getattr(belly_app, 'stretch_marks', [])
            muscle = getattr(belly_app, 'muscle_definition', 0.0)
            tanned = getattr(belly_app, 'is_tanned', False)
            pierced = getattr(belly_app, 'has_piercing', False)
            circumference = getattr(belly_app, 'get_visual_circumference', lambda: 60.0)()
            if callable(circumference):
                circumference = circumference()
            
            table.add_row("Base Shape", base_shape)
            table.add_row("Current Shape", current_shape)
            table.add_row("Base Size", f"{base_size:.1f}cm")
            table.add_row("Current Size", f"{current_size:.1f}cm")
            table.add_row("Inflation Ratio", f"×{inflation:.2f}")
            table.add_row("Fill Ratio", f"{fill:.1%}")
            table.add_row("Belly Button", f"{btn} ({btn_depth:.1f}cm)")
            table.add_row("Skin", str(skin))
            table.add_row("Stretch Marks", str(len(marks)) if marks else "None")
            table.add_row("Muscle Definition", f"{muscle:.1%}")
            table.add_row("Tanned", "Yes" if tanned else "No")
            table.add_row("Piercing", "Yes" if pierced else "No")
            table.add_row("Visual Circumference", f"{circumference:.1f}cm")
            
            console.print(table)
            
            if hasattr(belly_app, 'get_description'):
                desc = belly_app.get_description()
                if desc:
                    console.print(f"\n[dim]Description: {desc}[/dim]")
        except Exception as e:
            console.print(f"[red]Error displaying belly status: {e}[/red]")

    # ============ ANUS COMMANDS ============
    
    def cmd_anus_appearance(self, args: List[str], ctx):
        """Управление внешностью ануса."""
        if not ctx.active_body:
            console.print("[red]No body selected[/red]")
            return
        
        try:
            app_parts = self._get_or_create_appearance_parts(ctx.active_body)
            anus_app = app_parts.get('anus')
            
            # Определяем индекс ануса
            anus_idx = 0
            remaining_args = args[:]
            
            if remaining_args and remaining_args[0].isdigit():
                anus_idx = int(remaining_args[0])
                remaining_args = remaining_args[1:]
            
            # Получаем anatomy для обновления
            anus_anatomy = None
            if hasattr(ctx.active_body, 'anuses') and ctx.active_body.anuses:
                if len(ctx.active_body.anuses) > anus_idx:
                    anus_anatomy = ctx.active_body.anuses[anus_idx]
            
            if not remaining_args:
                self._show_anus_status(anus_app, anus_idx, ctx.active_body)
                return
            
            action = remaining_args[0].lower()
            action_args = remaining_args[1:]
            
            if action in ("status", "s"):
                self._show_anus_status(anus_app, anus_idx, ctx.active_body)
                
            elif action in ("update", "u"):
                self._update_anus_from_anatomy(anus_app, anus_anatomy, anus_idx)
                    
            elif action == "type":
                self._set_anus_type(anus_app, action_args)
                    
            elif action == "color":
                self._set_anus_color(anus_app, action_args)
                
            elif action == "hair":
                self._set_anus_hair(anus_app, action_args)
                
            elif action == "piercing":
                self._toggle_piercing(anus_app)
                    
            elif action == "reset":
                self._reset_anus(anus_app)
                
            else:
                console.print(f"[red]Unknown action: {action}[/red]")
                console.print("[dim]Actions: status, update, type, color, hair, piercing, reset[/dim]")
                
        except Exception as e:
            console.print(f"[red]Error in anus_appearance: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")

    def _update_anus_from_anatomy(self, anus_app, anus_anatomy, idx):
        """Обновить внешность ануса из anatomy."""
        if anus_anatomy and hasattr(anus_app, 'update_from_anus'):
            try:
                anus_app.update_from_anus(anus_anatomy)
                console.print(f"[green]✓ Anus #{idx} appearance updated[/green]")
                self._show_anus_status(anus_app, idx, None)
            except Exception as e:
                console.print(f"[yellow]Update error: {e}[/yellow]")
        else:
            console.print(f"[yellow]No anus #{idx} found or no update method[/yellow]")

    def _set_anus_type(self, anus_app, action_args):
        """Установить тип ануса."""
        if not action_args:
            base = _safe_enum_str(getattr(anus_app, 'base_type', None))
            current = _safe_enum_str(getattr(anus_app, 'current_type', None))
            console.print(f"[cyan]Base type: {base}[/cyan]")
            console.print(f"[cyan]Current type: {current}[/cyan]")
            console.print("[dim]Options: tight, normal, relaxed, gaping, prolapsed, puffed, stretched[/dim]")
            return
        
        try:
            try:
                from body_sim.appearance.body_parts import AnusAppearanceType
            except ImportError:
                from appearance.body_parts import AnusAppearanceType
            
            atype = AnusAppearanceType[action_args[0].upper()]
            anus_app.base_type = atype
            console.print(f"[green]Base anus type set to: {_safe_enum_str(atype)}[/green]")
        except (KeyError, ImportError):
            console.print("[red]Invalid type. Options: tight, normal, relaxed, gaping, prolapsed, puffed, stretched[/red]")

    def _set_anus_color(self, anus_app, action_args):
        """Установить цвет ануса."""
        if not action_args:
            color = getattr(anus_app, 'base_color', 'pink')
            console.print(f"[cyan]Color: {color}[/cyan]")
            return
        
        anus_app.base_color = action_args[0]
        console.print(f"[green]Anus color set to: {action_args[0]}[/green]")

    def _set_anus_hair(self, anus_app, action_args):
        """Установить волосы."""
        if not action_args:
            has = getattr(anus_app, 'has_hair', True)
            density = getattr(anus_app, 'hair_density', 'sparse')
            console.print(f"[cyan]Hair: {density if has else 'None'}[/cyan]")
            return
        
        has = action_args[0].lower() in ("yes", "true", "1", "on")
        anus_app.has_hair = has
        if len(action_args) > 1:
            anus_app.hair_density = action_args[1]
        console.print(f"[green]Hair: {'Yes' if has else 'No'} ({getattr(anus_app, 'hair_density', 'none')})[/green]")

    def _toggle_piercing(self, anus_app):
        """Переключить пирсинг."""
        current = getattr(anus_app, 'has_piercing', False)
        anus_app.has_piercing = not current
        status = "yes" if anus_app.has_piercing else "no"
        console.print(f"[green]Piercing: {status}[/green]")

    def _reset_anus(self, anus_app):
        """Сбросить к базовому типу."""
        base = getattr(anus_app, 'base_type', None)
        anus_app.current_type = base
        anus_app.is_gaping = False
        anus_app.prolapse_degree = 0.0
        console.print("[green]Anus appearance reset to base type[/green]")

    def _show_anus_status(self, anus_app, idx, body):
        """Показать статус внешности ануса."""
        try:
            table = Table(show_header=True, box=box.ROUNDED, title=f"Anus #{idx} Appearance")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="magenta")
            
            base_type = _safe_enum_str(getattr(anus_app, 'base_type', None))
            current_type = _safe_enum_str(getattr(anus_app, 'current_type', None))
            color = getattr(anus_app, 'base_color', 'pink')
            base_diam = getattr(anus_app, 'base_diameter', 0.5)
            current_diam = getattr(anus_app, 'current_diameter', 0.5)
            max_visual = getattr(anus_app, 'max_visual_diameter', 2.0)
            is_gaping = getattr(anus_app, 'is_gaping', False)
            gaping_size = getattr(anus_app, 'gaping_size', 0.0)
            prolapse = getattr(anus_app, 'prolapse_degree', 0.0)
            loose = getattr(anus_app, 'is_permanently_loose', False)
            stretch_marks = getattr(anus_app, 'stretch_marks', False)
            discolor = getattr(anus_app, 'discoloration', False)
            has_hair = getattr(anus_app, 'has_hair', True)
            hair_density = getattr(anus_app, 'hair_density', 'sparse')
            has_piercing = getattr(anus_app, 'has_piercing', False)
            
            table.add_row("Base Type", base_type)
            table.add_row("Current Type", current_type)
            table.add_row("Color", str(color))
            table.add_row("Base Diameter", f"{base_diam:.1f}cm")
            table.add_row("Current Diameter", f"{current_diam:.1f}cm")
            table.add_row("Max Visual", f"{max_visual:.1f}cm")
            table.add_row("Gaping", f"{is_gaping} ({gaping_size:.1f}cm)" if is_gaping else "No")
            table.add_row("Prolapse", f"{prolapse:.0%}" if prolapse > 0 else "None")
            table.add_row("Permanently Loose", "Yes" if loose else "No")
            table.add_row("Stretch Marks", "Yes" if stretch_marks else "No")
            table.add_row("Discoloration", "Yes" if discolor else "No")
            table.add_row("Hair", f"{hair_density}" if has_hair else "None")
            table.add_row("Piercing", "Yes" if has_piercing else "No")
            
            console.print(table)
            
            if hasattr(anus_app, 'get_description'):
                desc = anus_app.get_description()
                if desc:
                    console.print(f"\n[dim]Description: {desc}[/dim]")
        except Exception as e:
            console.print(f"[red]Error displaying anus status: {e}[/red]")

    # ============ ALL PARTS ============
    
    def cmd_all_parts_appearance(self, args: List[str], ctx):
        """Показать внешность всех частей тела."""
        if not ctx.active_body:
            console.print("[red]No body selected[/red]")
            return
        
        try:
            app_parts = self._get_or_create_appearance_parts(ctx.active_body)
            
            if args and args[0].lower() == "update":
                # Обновить все из anatomy
                self._update_all_parts(app_parts, ctx.active_body)
                console.print()
            
            # Показать все
            console.print(Panel("[bold cyan]Body Parts Appearance Overview[/bold cyan]", box=box.DOUBLE))
            
            # Mouth
            mouth_app = app_parts.get('mouth')
            if mouth_app:
                console.print(f"\n[bold yellow]👄 Mouth:[/bold yellow]")
                desc = getattr(mouth_app, 'get_description', lambda: "No description")()
                console.print(f"  {desc}")
            
            # Belly
            belly_app = app_parts.get('belly')
            if belly_app:
                console.print(f"\n[bold yellow]🫃 Belly:[/bold yellow]")
                desc = getattr(belly_app, 'get_description', lambda: "No description")()
                console.print(f"  {desc}")
            
            # Anus
            anus_app = app_parts.get('anus')
            if anus_app:
                console.print(f"\n[bold yellow]🍑 Anus:[/bold yellow]")
                anus_count = len(ctx.active_body.anuses) if hasattr(ctx.active_body, 'anuses') and ctx.active_body.anuses else 0
                desc = getattr(anus_app, 'get_description', lambda: "No description")()
                if anus_count > 1:
                    console.print(f"  ({anus_count} anuses) {desc}")
                else:
                    console.print(f"  {desc}")
                    
        except Exception as e:
            console.print(f"[red]Error in body_parts_appearance: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")

    def _update_all_parts(self, app_parts, body):
        """Обновить все части из anatomy."""
        # Mouth
        try:
            if hasattr(body, 'mouth_system') and body.mouth_system:
                mouth = body.mouth_system.primary if hasattr(body.mouth_system, 'primary') else body.mouth_system
                if mouth and 'mouth' in app_parts:
                    app_parts['mouth'].update_from_mouth(mouth)
                    console.print("[green]✓ Mouth updated[/green]")
        except Exception as e:
            console.print(f"[dim]Mouth update skipped: {e}[/dim]")
        
        # Belly
        try:
            if hasattr(body, 'stomach_system') and body.stomach_system:
                stomach = body.stomach_system.primary if hasattr(body.stomach_system, 'primary') else body.stomach_system
                if stomach and 'belly' in app_parts:
                    app_parts['belly'].update_from_stomach(stomach)
                    console.print("[green]✓ Belly updated[/green]")
        except Exception as e:
            console.print(f"[dim]Belly update skipped: {e}[/dim]")
        
        # Anus
        try:
            if hasattr(body, 'anuses') and body.anuses and len(body.anuses) > 0:
                if 'anus' in app_parts:
                    app_parts['anus'].update_from_anus(body.anuses[0])
                    console.print("[green]✓ Anus updated[/green]")
        except Exception as e:
            console.print(f"[dim]Anus update skipped: {e}[/dim]")


# Функция для регистрации в основном реестре команд
def register_appearance_part_commands(registry):
    """Зарегистрировать команды внешности частей тела."""
    try:
        AppearancePartCommands(registry)
        console.print("[dim]Body parts appearance commands registered[/dim]")
    except Exception as e:
        console.print(f"[red]Failed to register appearance part commands: {e}[/red]")

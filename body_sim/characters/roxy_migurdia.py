# body_sim/characters/roxy_migurdia.py
"""
Рокси Мигурдия - мигурдийская демон-люд из Mushoku Tensei.
Особенности: голубые волосы, ахроматические глаза (без зрачков), 
низкий рост, маленькая грудь, повышенная чувствительность к боли и прикосновениям.
"""

from dataclasses import dataclass, field
from typing import Dict, Any

from body_sim.body.body import FemaleBody
from body_sim.body.stats import BodyStats
from body_sim.core.enums import Sex, BodyType, CupSize, Color, VaginaType, NippleType, NippleShape
from body_sim.anatomy.nipple import Nipple, Areola
from body_sim.anatomy.breast import Breast
from body_sim.systems.grid import BreastGrid
from body_sim.appearance import Race, EyeType, EarType


@dataclass
class RoxyMigurdia(FemaleBody):
    """
    Рокси Мигурдия - мигурдийская маг из расы демон-людей.
    
    Расовые особенности:
    - Голубые волосы, ахроматические красные глаза без зрачков (видят в темноте)
    - Низкий рост (~150 см), подростковое телосложение
    - Медленное старение (40+ лет, выглядит на 14-15)
    - Повышенная чувствительность кожи и болевой чувствительности
    - Телепатические способности (дальность ~1000 км между мигурдийцами)
    - Низкий болевой порог (мигурдийцы болезненно реагируют на повреждения)
    """
    
    # Основные характеристики
    name: str = "Roxy Migurdia"
    sex: Sex = field(default=Sex.FEMALE, init=False)
    body_type: BodyType = BodyType.PETITE  # Миниатюрное телосложение
    race: Race = Race.MIGURDIAN
    
    name: str = "Roxy Migurdia"
    sex: Sex = field(default=Sex.FEMALE, init=False)
    body_type: BodyType = BodyType.PETITE
    
    # === ВНЕШНОСТЬ (из AppearanceMixin) ===
    race: Race = Race.MIGURDIAN  # Мигурдийцы - подвид демонов
    
    # Переопределяем возраст (мигурдийцы стареют медленно)
    age: float = 44.0  # Реальный возраст
    apparent_age: float = 15.0  # Внешний вид
    
    # === ФИЗИЧЕСКИЕ ПАРАМЕТРЫ ===
    stats: BodyStats = field(default_factory=lambda: BodyStats(
        height=150.0,
        weight=42.0,
        hip_width=28.0,
        waist_width=22.0,
        shoulder_width=32.0,
        flexibility=0.7,
        arousal=0.0,
        pleasure=0.0,
        pain=0.0,
        fatigue=0.0
    ))
    
    # === МИГУРДИЙСКИЕ ОСОБЕННОСТИ ===
    migurdian_traits: Dict[str, float] = field(default_factory=lambda: {
        "pain_sensitivity": 1.6,      # +60% к боли
        "tactile_sensitivity": 1.4,   # +40% к тактильным ощущениям
        "thermal_sensitivity": 1.3,   # +30% к температуре
        "pleasure_sensitivity": 1.3,  # +30% к удовольствию
        "age_appearance_ratio": 0.35, # Выглядит на 35% от возраста
        "telepathy_range_km": 1000.0, # Телепатия
    })
    
    character_info: Dict[str, Any] = field(default_factory=lambda: {
        "race_name": "Migurdian Demon-Human",
        "occupation": "Mage, Former Magic Tutor",
        "personality_traits": [
            "tsundere", "prideful", "diligent", 
            "insecure_about_appearance", "alcoholic_tendencies"
        ],
        "magic_affinity": ["water", "ice"],
        "hair_color": "blue",           # Специфично для Рокси
        "hair_style": "long_braid",     # Традиционная коса
    })
    
    # Гениталии - компактные, подростковые пропорции
    vagina_count: int = 1
    vagina_depth: float = 8.0   # Меньше среднего (10 см)
    vagina_width: float = 2.2   # Уже среднего (3 см)
    vagina_type: VaginaType = VaginaType.HUMAN
    clitoris_count: int = 1
    clitoris_size: float = 1.0  # Маленький клитор
    
    # Грудь - маленькая (AA), характерна для её телосложения
    breast_cup: str = "AA"

    def __post_init__(self):
        super().__post_init__()
        self._apply_migurdian_physiology()
        self._customize_migurdian_appearance()
    
    def _customize_migurdian_appearance(self):
        """Настроить специфичную для мигурдийцев внешность."""
        # Глаза - ахроматические красные без зрачков (особенность Рокси)
        self.eyes = type(self.eyes)(
            type=EyeType.DEMONIC,
            color=Color.CRIMSON,  # Красные без зрачков
            glow=True,            # Свечение в темноте
            pupil_shape="none"    # Ахроматические (нет зрачков)
        )
        
        # Уши - острые но короткие (не как у эльфов)
        self.ears = type(self.ears)(
            type=EarType.POINTED,
            length=3.5,           # Короче эльфийских (6см)
            mobility=0.2          # Немного подвижны
        )
        
        # Кожа - очень бледная, чувствительная
        self.skin_color = Color.PALE_IVORY
        self.skin_texture = "smooth_sensitive"
        
        # Рост уже установлен через stats, но проверим
        if self.stats.height == 0:
            self.stats.height = 150.0
    
    def _apply_migurdian_physiology(self) -> None:
        """Применить физиологические модификаторы."""
        if self.breast_grid:
            for breast in self.breast_grid.all():
                # Усиливаем чувствительность груди
                breast.areola.sensitivity = min(1.0, breast.areola.sensitivity * 1.3)
                breast.sensitivity = 1.4
                
                # Добавляем слушатель для расовых реакций
                breast.on("state_change", self._on_breast_state_change)
        
        # Настройка влагалища
        if self.vaginas:
            for vagina in self.vaginas:
                vagina.sensitivity = 1.4
                vagina.elasticity = 0.95  # Высокая эластичность при компактности
    
    def _on_breast_state_change(self, breast, old, new):
        """Расовая реакция на изменение состояния груди."""
        if new.name == "OVERPRESSURED":
            # Мигурдийцы сильнее реагируют на дискомфорт
            pain_amount = 0.15 * self.migurdian_traits["pain_sensitivity"]
            self.stats.pain = min(1.0, self.stats.pain + pain_amount)
            self._emit("migurdian_pain_reaction", source="breast_pressure", intensity=pain_amount)
    
    def stimulate(self, region: str, index: int = 0, intensity: float = 0.1) -> None:
        """Стимуляция с учетом мигурдийской чувствительности."""
        # Усиливаем интенсивность
        modified_intensity = intensity * self.migurdian_traits["tactile_sensitivity"]
        
        # Базовая стимуляция (через AppearanceMixin не идет, но через Body)
        super().stimulate(region, index, modified_intensity)
        
        # Боль при высокой интенсивности (низкий болевой порог)
        if modified_intensity > 0.5:
            pain_amount = (modified_intensity - 0.5) * 0.3 * self.migurdian_traits["pain_sensitivity"]
            self.stats.pain = min(1.0, self.stats.pain + pain_amount)
            
            # Уши прижимаются при боли
            if pain_amount > 0.1:
                self.flatten_ears()
    
    def tick(self, dt: float = 1.0) -> None:
        """Обновление с расовыми особенностями."""
        super().tick(dt)
        
        # Мигурдийцы быстрее восстанавливаются от усталости (молодой организм)
        if self.stats.fatigue > 0:
            self.stats.fatigue = max(0.0, self.stats.fatigue - 0.02 * dt)
        
        # Боль проходит медленнее (высокая чувствительность)
        if self.stats.pain > 0:
            self.stats.pain = max(0.0, self.stats.pain - 0.08 * dt)
        
        # Возврат ушей в нейтральное положение происходит автоматически
        # через AppearanceMixin.tick(), но можно добавить логику здесь
    
    def get_rich_description(self) -> str:
        """Получить форматированное описание для Rich."""
        traits = self.migurdian_traits
        
        return f"""[bold cyan]╔══════════════════════════════════════════════════════════╗
║           ROXY MIGURDIA - ロキシー・ミグルディア          ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]

[bold]Race:[/bold] {self.character_info['race']}
[bold]Age:[/bold] {self.character_info['age_real']} years (appears {self.character_info['age_appearance']})
[bold]Height:[/bold] {self.stats.height:.0f} cm | [bold]Weight:[/bold] {self.stats.weight:.0f} kg

[bold yellow]Migurdian Traits:[/bold yellow]
  • Pain Sensitivity: [red]×{traits['pain_sensitivity']:.1f}[/red] (low pain threshold)
  • Tactile Sensitivity: [magenta]×{traits['tactile_sensitivity']:.1f}[/magenta]
  • Thermal Sensitivity: [blue]×{traits['thermal_sensitivity']:.1f}[/blue]
  • Telepathy Range: [cyan]{traits['telepathy_range_km']:.0f} km[/cyan]

[bold green]Appearance:[/bold green]
  • Hair: Long [blue]blue[/blue] hair (traditional Migurdian braid)
  • Eyes: [red]Achromatic crimson[/red] (no pupils, night vision)
  • Skin: Pale, smooth, highly sensitive
  • Figure: Petite, slender, [magenta]{self.breast_cup}-cup[/magenta] breasts

[bold]Personality:[/bold] {', '.join(self.character_info['personality_traits'][:3])}
[bold]Magic:[/bold] Water & Ice affinity
"""

    def __str__(self) -> str:
        return f"RoxyMigurdia({self.name}, {self.character_info['age_real']}y/~{self.character_info['age_appearance']}y, {self.breast_cup}-cup, Migurdian)"


# Фабричная функция
def create_roxy() -> RoxyMigurdia:
    """Создать Рокси Мигурдию с дефолтными параметрами."""
    from body_sim.systems.events import EventfulBody
    return EventfulBody(RoxyMigurdia(race=Race.MIGURDIAN))


# Для интеграции с консолью
def register_roxy_command(registry):
    """Добавить команду создания Рокси в реестр команд."""
    from body_sim.ui.commands import Command, console
    
    def cmd_create_roxy(args, ctx):
        roxy = create_roxy()
        ctx.bodies.append(roxy)
        console.print(f"[bold cyan]Created {roxy.name} - Migurdian Mage![/bold cyan]")
        console.print(f"[dim]{roxy.character_info['age_real']} years old, appears {roxy.character_info['age_appearance']}[/dim]")
    
    registry.register(Command(
        "roxy", ["migurdia"], 
        "Create Roxy Migurdia character", 
        "roxy", 
        cmd_create_roxy, 
        "characters"
    ))

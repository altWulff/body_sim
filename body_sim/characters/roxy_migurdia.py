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
    
    # Физические параметры (откорректированы для роста 150 см)
    stats: BodyStats = field(default_factory=lambda: BodyStats(
        height=150.0,      # Низкий рост
        weight=42.0,       # Лёгкая
        hip_width=28.0,    # Узкие бёдра
        waist_width=22.0,  # Тонкая талия
        shoulder_width=32.0,  # Узкие плечи
        flexibility=0.7,   # Гибкая (маг/путешественник)
        arousal=0.0,
        pleasure=0.0,
        pain=0.0,
        fatigue=0.0
    ))
    
    # Гениталии - компактные, подростковые пропорции
    vagina_count: int = 1
    vagina_depth: float = 8.0   # Меньше среднего (10 см)
    vagina_width: float = 2.2   # Уже среднего (3 см)
    vagina_type: VaginaType = VaginaType.HUMAN
    clitoris_count: int = 1
    clitoris_size: float = 1.0  # Маленький клитор
    
    # Грудь - маленькая (AA), характерна для её телосложения
    breast_cup: str = "AA"
    
    # Внешность (для рендеринга/описания)
    appearance: Dict[str, Any] = field(default_factory=lambda: {
        "hair_color": "blue",           # Голубые волосы (классика мигурдийцев)
        "hair_length": "long",          # Длинные волосы (обычно в косе)
        "eye_color": "achromatic_red",  # Ахроматические красные глаза без зрачков
        "eye_feature": "no_pupils",     # Отсутствуют зрачки
        "skin_tone": "pale",            # Бледная кожа
        "skin_texture": "smooth",       # Гладкая чувствительная кожа
        "distinctive_features": [
            "ahcromatic_vision",        # Видение в темноте
            "telepathy_capable",        # Телепатия с другими мигурдийцами
            "slow_aging",               # Медленное старение
        ]
    })
    
    # Расовые модификаторы чувствительности
    migurdian_traits: Dict[str, float] = field(default_factory=lambda: {
        "pain_sensitivity": 1.6,      # +60% к боли (низкий болевой порог)
        "tactile_sensitivity": 1.4,   # +40% к тактильным ощущениям
        "thermal_sensitivity": 1.3,   # +30% к температурным ощущениям
        "pleasure_sensitivity": 1.3,  # +30% к удовольствию (чувствительная кожа)
        "age_appearance_ratio": 0.35, # Выглядит на 35% от реального возраста
        "telepathy_range_km": 1000.0, # Дальность телепатии
    })
    
    # Ролевая информация
    character_info: Dict[str, Any] = field(default_factory=lambda: {
        "age_real": 44,               # Реальный возраст (родилась ~50 году K)
        "age_appearance": 15,         # Внешний вид (~15 лет)
        "race": "Migurdian Demon-Human",
        "occupation": "Mage, Former Magic Tutor",
        "personality_traits": [
            "tsundere", "prideful", "diligent", 
            "insecure_about_appearance", "alcoholic_tendencies"
        ],
        "magic_affinity": ["water", "ice"],
    })

    def __post_init__(self):
        super().__post_init__()
        self._apply_migurdian_physiology()
    
    def _setup_breasts(self) -> None:
        """
        Настройка маленькой чувствительной груди Рокси.
        AA-cup, маленькие соски, высокая чувствительность ареол.
        """
        
        # Создаём сетку из двух грудей
        left_breast = Breast(
            cup=CupSize.AA,
            areola=Areola(
                base_diameter=2.8,
                color=Color.PALE_PINK,
                nipples=[Nipple(
                    base_length=0.35,
                    base_width=0.55,
                    color=Color.PALE_PINK,
                    erect_multiplier=1.6
                )],
                puffiness=0.2,
                sensitivity=0.9
            ),
            base_elasticity=1.2,
            leak_factor=15.0
        )
        
        right_breast = Breast(
            cup=CupSize.AA,
            areola=Areola(
                base_diameter=2.8,
                color=Color.PALE_PINK,
                nipples=[Nipple(
                    base_length=0.35,
                    base_width=0.55,
                    color=Color.PALE_PINK,
                    erect_multiplier=1.6
                )],
                puffiness=0.2,
                sensitivity=0.9
            ),
            base_elasticity=1.2,
            leak_factor=15.0
        )
        
        self.breast_grid = BreastGrid(
            rows=[[left_breast], [right_breast]],
            labels=[["left_breast"], ["right_breast"]]
        )
    
    def _apply_migurdian_physiology(self) -> None:
        """Применить физиологические особенности мигурдийцев."""
        # Модифицируем реакцию на стимуляцию через переопределение методов
        # или добавление слушателей событий
        
        if self.breast_grid:
            for row in self.breast_grid.rows:
                for breast in row:
                    # Усиливаем реакцию груди на стимуляцию
                    breast.areola.sensitivity = min(1.0, breast.areola.sensitivity * 1.3)
                    
                    # Добавляем слушатель для расовых реакций
                    breast.on("state_change", self._on_breast_state_change)
    
    def _on_breast_state_change(self, breast, old, new):
        """Расовая реакция на изменение состояния груди."""
        # Мигурдийцы более чувствительны к дискомфорту
        if new.name == "OVERPRESSURED":
            # Более сильная реакция на переполнение
            self.stats.pain += 0.15 * self.migurdian_traits["pain_sensitivity"]
    
    def stimulate(self, region: str, index: int = 0, intensity: float = 0.1) -> None:
        """
        Переопределенная стимуляция с учётом мигурдийской чувствительности.
        """
        # Усиливаем интенсивность из-за чувствительной кожи
        modified_intensity = intensity * self.migurdian_traits["tactile_sensitivity"]
        
        # Базовая стимуляция
        super().stimulate(region, index, modified_intensity)
        
        # Дополнительная боль при высокой интенсивности (низкий болевой порог)
        if modified_intensity > 0.5:
            pain_amount = (modified_intensity - 0.5) * 0.3 * self.migurdian_traits["pain_sensitivity"]
            self.stats.pain = min(1.0, self.stats.pain + pain_amount)
    
    def tick(self, dt: float = 1.0) -> None:
        """Обновление с расовыми особенностями."""
        super().tick(dt)
        
        # Мигурдийцы быстрее восстанавливаются от усталости (молодой организм)
        # но медленнее от боли (чувствительность)
        if self.stats.fatigue > 0:
            self.stats.fatigue = max(0.0, self.stats.fatigue - 0.02 * dt)
        
        # Боль проходит медленнее
        if self.stats.pain > 0:
            self.stats.pain = max(0.0, self.stats.pain - 0.08 * dt)  # Медленнее стандартных 0.15
    
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
    return RoxyMigurdia()


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

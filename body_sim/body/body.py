# body_sim/body/body.py
"""
Тело и его специализации.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import random

from body_sim.core.enums import Sex, BodyType, TesticleSize, CupSize, Color, FluidType, PenisType, VaginaType, ScrotumType, GenitalVisibility
from body_sim.body.stats import BodyStats
from body_sim.anatomy import *
from body_sim.systems.grid import BreastGrid
from body_sim.systems.penetration import CrossBodyPenetration
from body_sim.magic import MagicMixin
from body_sim.appearance import AppearanceMixin, Race, EyeAppearance, EarAppearance, EyeType, EarType, RACE_ANATOMY_PRESETS, get_race_preset, get_random_race_size


@dataclass
class Body(MagicMixin, AppearanceMixin):
    name: str = "Unnamed"
    sex: Sex = Sex.NONE
    body_type: BodyType = BodyType.AVERAGE
    stats: BodyStats = field(default_factory=BodyStats)
    race: Race = Race.HUMAN

    # Глаза (пара)
    eyes: EyeAppearance = field(default_factory=lambda: EyeAppearance(
        type=EyeType.HUMAN, color=Color.BROWN, glow=False
    ))
    
    # Уши
    ears: EarAppearance = field(default_factory=lambda: EarAppearance(
        type=EarType.HUMAN, length=2.0
    ))
    
    # Кожа/чешуя/слизь
    skin_color: Color = Color.LIGHT_BEIGE
    skin_texture: str = "smooth"  # smooth, scaly, slimy, fur, etc.
    
    # === ВИДИМОСТЬ ===
    genital_visibility: GenitalVisibility = GenitalVisibility.COVERED
    clothing_coverage: Dict[str, float] = field(default_factory=lambda: {
        "chest": 1.0, "groin": 1.0, "anus": 1.0
    })
    
    breast_grid: Optional[BreastGrid] = None
    penises: List[Penis] = field(default_factory=list)
    clitorises: List[Clitoris] = field(default_factory=list)
    vaginas: List[Vagina] = field(default_factory=list)
    scrotums: List[Scrotum] = field(default_factory=list)
    anuses: List[Anus] = field(default_factory=list)
    uterus_system: Optional[UterusSystem] = None
    # Новые системы
    mouth_system: MouthSystem = field(default_factory=MouthSystem)
    stomach_system: StomachSystem = field(default_factory=StomachSystem)
    rectum_system: RectumSystem = field(default_factory=RectumSystem)
    
    # Связи
    esophagus: Optional['Esophagus'] = field(default=None)

    active_sex: Optional[CrossBodyPenetration] = field(default=None, init=False)
    
    _listeners: Dict[str, List] = field(default_factory=dict, repr=False)

    
    def __post_init__(self):
        # Применяем пресет расы
        super().__post_init__()
        # Настройка анатомии по полу и расе
        self._setup_genitals()
        self._setup_uterus()
        self._setup_breasts()
        
        if self.esophagus is None:
            self.esophagus = Esophagus()
            
        # Связываем рот с пищеводом
        mouth = self.mouth_system.primary
        if mouth:
            mouth.throat.esophagus_connection = self.esophagus
        
        # Связываем пищевод с желудком
        stomach = self.stomach_system.primary
        if stomach:
            self.esophagus.stomach_connection = stomach
            stomach.cardia.esophagus_connection = self.esophagus
        
        # Анус есть у всех
        if not self.anuses:
            self.anuses.append(Anus())
        
        # === СВЯЗЬ АНУСОВ С ЖЕЛУДКОМ ЧЕРЕЗ RECTUM ===
        rectum = self.rectum_system.primary
        if rectum:
            # Каждый анус соединяется с прямой кишкой
            for anus in self.anuses:
                anus.rectum_connection = rectum
                rectum.anus_connection = anus
            
            # Прямая кишка соединяется с желудком
            if stomach:
                rectum.stomach_connection = stomach
        
        # Инициализация магии
        self.init_magic()

            
    def _setup_uterus(self) -> None:
        "Создание системы маток."
        pass
    
    def _setup_genitals(self) -> None:
        pass
    
    def _setup_breasts(self) -> None:
        pass

    def _create_breast(self, cup: CupSize, side: str) -> Breast:
        """Фабрика груди с расовыми параметрами."""
        preset = self._preset
        
        areola_size = preset.get("areola_size", 3.0) * (1 + cup.value * 0.1)
        nipple_color = preset.get("nipple_color", Color.LIGHT_PINK)
        
        nipple = Nipple(
            base_length=0.6 if cup != CupSize.FLAT else 0.3,
            base_width=0.8 + (cup.value * 0.1),
            color=nipple_color
        )
        
        areola = Areola(
            base_diameter=areola_size,
            color=nipple_color,
            nipples=[nipple],
            puffiness=0.2 if self.race == Race.ORC else 0.1
        )
        
        return Breast(
            cup=cup,
            areola=areola,
            base_elasticity=preset.get("elasticity", 0.8),
            name=f"breast_{side}",
            sensitivity=1.2 if self.sex == Sex.FEMALE else 0.8
        )

    def _get_penis_type(self) -> PenisType:
        """Определить тип пениса по расе."""
        return self._preset.get("penis_type", PenisType.HUMAN)
    
    def _get_vagina_type(self) -> VaginaType:
        """Определить тип влагалища по расе."""
        return self._preset.get("vagina_type", VaginaType.HUMAN)
    
    def _get_scrotum_type(self) -> ScrotumType:
        """Определить тип мошонки по расе."""
        return self._preset.get("scrotum_type", ScrotumType.STANDARD)
    
    def _get_random_size(self, param: str) -> float:
        """Получить случайный размер из диапазона пресета."""
        if param in self._preset:
            min_v, max_v = self._preset[param]
            return random.uniform(min_v, max_v)
        return 15.0  # default

    def change_race(self, new_race: Race, regenerate: bool = True):
        """Сменить расу с опциональной перегенерацией анатомии."""
        old_race = self.race
        self.race = new_race
        self._preset = RACE_ANATOMY_PRESETS.get(new_race, RACE_ANATOMY_PRESETS[Race.HUMAN])
        
        # Обновляем внешность
        self._setup_race_appearance()
        
        if regenerate:
            # Очищаем и пересоздаем гениталии
            self.penises.clear()
            self.vaginas.clear()
            self.clitorises.clear()
            self.scrotums.clear()
            self._setup_genitals()
            self._setup_breasts()
            
            if self.sex in (Sex.FEMALE, Sex.FUTANARI) and not self.uterus_system:
                self._setup_uterus()
        
        self._emit("race_changed", old=old_race, new=new_race)
    
    def change_sex(self, new_sex: Sex):
        """Сменить биологический пол."""
        self.sex = new_sex
        
        # Очищаем старое
        self.penises.clear()
        self.vaginas.clear()
        self.clitorises.clear()
        self.scrotums.clear()
        self.uterus_system = None
        self.breast_grid = None
        
        # Пересоздаем
        self._setup_genitals()
        self._setup_uterus()
        self._setup_breasts()
        
        self._emit("sex_changed", new_sex=new_sex)
    
    def on(self, event: str, callback) -> None:
        self._listeners.setdefault(event, []).append(callback)
    
    def _emit(self, event: str, **data) -> None:
        for cb in self._listeners.get(event, []):
            cb(self, **data)

    def start_sex_with(self, target: 'Body', target_organ: str = "vagina", 
                       source_organ: str = "penis") -> CrossBodyPenetration:
        """Начать половой акт с другим телом"""
        self.active_sex = CrossBodyPenetration(self, target, source_organ, target_organ)
        return self.active_sex
    
    @property
    def has_penis(self) -> bool:
        return len(self.penises) > 0
    
    @property
    def has_vagina(self) -> bool:
        return len(self.vaginas) > 0
    
    @property
    def has_clitoris(self) -> bool:
        return len(self.clitorises) > 0
    
    @property
    def has_scrotum(self) -> bool:
        return len(self.scrotums) > 0
    
    @property
    def has_breasts(self) -> bool:
        return self.breast_grid is not None
    
    @property
    def has_uterus(self) -> bool:
        return self.uterus_system is not None
    
    @property
    def primary_uterus(self) -> Optional[Uterus]:
        "Основная матка."
        if self.uterus_system:
            return self.uterus_system.primary
        return self.uterus

    @property
    def is_fertile(self) -> bool:
        """Проверка фертильности (упрощенно)."""
        if not self.has_uterus:
            return False
        # TODO: Добавить проверку цикла, состояния яичников и т.д.
        return True
    
    def get_appearance_description(self) -> str:
        """Текстовое описание внешности."""
        parts = [
            f"{self.age:.0f}yo {self.race.name} {self.sex.name}",
            f"{self.height:.0f}cm, {self.weight:.0f}kg",
            f"{self.eyes.color.name} {self.eyes.type.name} eyes",
            f"{self.ears.type.name} ears ({self.ears.length:.1f}cm)"
        ]
        return ", ".join(parts)
    
    @property
    def total_cum_storage(self) -> float:
        """Общий объем спермы во всех яичках тела."""
        total = 0.0
        for scrotum in self.scrotums:
            for testicle in scrotum.testicles:
                total += testicle.stored_fluids.get(FluidType.CUM, 0.0)
        return total

    @property
    def total_cum_capacity(self) -> float:
        """Общая вместимость всех яичек."""
        return sum(s.total_storage_capacity for s in self.scrotums)

    def add_penis(self, penis: Penis) -> int:
        self.penises.append(penis)
        return len(self.penises) - 1
    
    def remove_penis(self, index: int) -> Optional[Penis]:
        if 0 <= index < len(self.penises):
            return self.penises.pop(index)
        return None
    
    def add_clitoris(self, clitoris: Clitoris) -> int:
        self.clitorises.append(clitoris)
        return len(self.clitorises) - 1
    
    def transform_clitoris_to_penis(self, clitoris_idx: int, 
                                    target_length: float = 10.0,
                                    target_girth: float = 8.0) -> Optional[int]:
        """Трансформировать клитор в пенис."""
        if 0 <= clitoris_idx < len(self.clitorises):
            clit = self.clitorises[clitoris_idx]
            penis = clit.transform_to_penis(target_length, target_girth)
            
            # НОВОЕ: Если у тела есть мошонка, подключаем пенис к ней
            if self.scrotums:
                penis.scrotum = self.scrotums[0]
            
            return self.add_penis(penis)
        return None
    
    def revert_penis_to_clitoris(self, penis_idx: int) -> bool:
        if 0 <= penis_idx < len(self.penises):
            penis = self.penises[penis_idx]
            if penis.is_transformed_clitoris:
                for clit in self.clitorises:
                    if clit.transformed_penis is penis:
                        clit.revert_to_clitoris()
                        self.penises.pop(penis_idx)
                        return True
        return False
    
    def add_vagina(self, vagina: Vagina) -> int:
        self.vaginas.append(vagina)
        return len(self.vaginas) - 1
    
    def add_scrotum(self, scrotum: Scrotum) -> int:
        self.scrotums.append(scrotum)
        return len(self.scrotums) - 1
    
    def stimulate(self, region: str, index: int = 0, intensity: float = 0.1) -> None:
        self.stats.arousal = min(1.0, self.stats.arousal + intensity * 0.5)
        
        if region == "penis" and index < len(self.penises):
            self.penises[index].stimulate(intensity)
            self.stats.pleasure += intensity * 0.8
            
        elif region == "clitoris" and index < len(self.clitorises):
            self.clitorises[index].stimulate(intensity)
            self.stats.pleasure += intensity * 1.2
            
        elif region == "vagina" and index < len(self.vaginas):
            self.vaginas[index].stimulate(intensity)
            self.stats.pleasure += intensity * 1.0
            
        elif region == "anus" and index < len(self.anuses):
            self.anuses[index].relax(intensity * 0.1)
            self.stats.pleasure += intensity * 0.4
            
        elif region == "breasts" and self.breast_grid:
            for breast in self.breast_grid.all():
                breast.lactation.stimulate()
            self.stats.pleasure += intensity * 0.6
        
        self._emit("stimulation", region=region, index=index, intensity=intensity)
    
    def stimulate_all(self, region: str, intensity: float = 0.1) -> None:
        if region == "penis":
            for i in range(len(self.penises)):
                self.stimulate("penis", i, intensity)
        elif region == "clitoris":
            for i in range(len(self.clitorises)):
                self.stimulate("clitoris", i, intensity)
        elif region == "vagina":
            for i in range(len(self.vaginas)):
                self.stimulate("vagina", i, intensity)
    
    def penetrate(self, target_region: str, target_index: int, 
                  penis_index: int = 0) -> bool:
        if penis_index >= len(self.penises):
            return False
        
        penis = self.penises[penis_index]
        
        if target_region == "vagina":
            if target_index < len(self.vaginas):
                success = self.vaginas[target_index].penetrate(penis)
                if success:
                    self._emit("penetration", region="vagina", 
                              target_idx=target_index, penis_idx=penis_index)
                return success
                
        elif target_region == "anus":
            if target_index < len(self.anuses):
                anus = self.anuses[target_index]
                if penis.can_penetrated(anus.current_diameter):
                    anus.relax(0.3)
                    self._emit("penetration", region="anus",
                              target_idx=target_index, penis_idx=penis_index)
                    return True
            return False
        
        return False
    
    def penetrate_with_external(self, target_region: str, target_index: int,
                                external_penis: Penis) -> bool:
        if target_region == "vagina" and target_index < len(self.vaginas):
            return self.vaginas[target_index].penetrate(external_penis)
        elif target_region == "anus" and target_index < len(self.anuses):
            anus = self.anuses[target_index]
            if external_penis.can_penetrated(anus.current_diameter):
                anus.relax(0.3)
                return True
        return False
    
    def ejaculate(self, penis_index: int = 0, force: float = 1.0) -> Dict[str, Any]:
        """
        Эякуляция через указанный пенис.
        Пенис сам забирает сперму из подключенной мошонки.
        """
        if penis_index >= len(self.penises):
            return {"success": False, "reason": "invalid_penis_index"}
        
        penis = self.penises[penis_index]
        
        if not penis.is_erect:
            return {"success": False, "reason": "not_erect"}
        
        # Проверяем, подключена ли мошонка
        if not penis.has_scrotum():
            return {"success": False, "reason": "no_scrotum_connected"}
        
        # Запоминаем сколько было до (для инфо)
        available_before = penis.get_available_volume()
    
        # Пенис забирает сперму напрямую из яичек (через scrotum.drain_fluid внутри)
        result = penis.ejaculate(force=force)
        # Проверяем результат
        if result.get("amount", 0) <= 0:
            return {
                "success": False, 
                "reason": result.get("reason", "empty"),
                "available_before": available_before
            }
        
        self._emit("ejaculation", 
                   penis_idx=penis_index, 
                   amount=result["amount"], 
                   force=force,
                   pulses=result.get("pulses", 1))

        # После эякуляции возбуждение падает
        self.stats.arousal *= 0.7
        penis.flaccid()
        
        return {
            "success": True,
            "penis_index": penis_index,
            "amount": result["amount"],
            "pulses": result.get("pulses", 1),
            "force": force,
            "available_before": available_before,
            "remaining_in_scrotum": result.get("remaining_in_testicles", 0)
        }
    
    def ejaculate_all(self, force: float = 1.0) -> List[Dict[str, Any]]:
        """Эякуляция всеми эрегированными пенисами."""
        results = []
        for i in range(len(self.penises)):
            if self.penises[i].is_erect:
                results.append(self.ejaculate(i, force))
        return results
    
    def tick(self, dt: float = 1.0) -> None:
        """Обновление состояния тела."""
        self.stats.tick(dt)
        AppearanceMixin.tick(self, dt)
        
        # Обновление гениталий
        for penis in self.penises:
            penis.tick(dt)
        
        for clit in self.clitorises:
            clit.tick(dt)
        
        for vagina in self.vaginas:
            vagina.tick(dt)
        
        # Производство спермы в яичках (хранится там же, переноса в пенис НЕТ)
        for scrotum in self.scrotums:
            scrotum.tick(dt, self.stats.arousal)
            # УДАЛЕНО: Перенос спермы в пенис — она забирается только при эякуляции
        
        for anus in self.anuses:
            anus.tick(dt)
        
        if self.uterus_system:
            self.uterus_system.tick(dt)
        
        if self.breast_grid:
            from body_sim.core.fluids import FLUID_DEFS
            self.breast_grid.tick_all(FLUID_DEFS, dt)
            
        # Новые системы
        self.mouth_system.tick(dt)
        self.stomach_system.tick(dt)
        self.rectum_system.tick(dt)
        if self.esophagus:
            self.esophagus.tick(dt)

        self.magic_tick()

    def _get_random_size(self, param: str) -> float:
        """Получить случайный размер из диапазона пресета."""
        return get_random_race_size(self.race, param)


@dataclass 
class MaleBody(Body):
    sex: Sex = field(default=Sex.MALE, init=False)
    penis_count: int = 1
    penis_size: float = 15.0
    penis_girth: float = 12.0
    penis_type: PenisType = PenisType.HUMAN
    testicle_size: TesticleSize = TesticleSize.AVERAGE
    scrotum_type: ScrotumType = ScrotumType.STANDARD
    
    def _setup_genitals(self) -> None:
        length = self.penis_size or self._get_random_size("penis_length")
        girth = self.penis_girth or self._get_random_size("penis_girth")

        scrotum = create_scrotum(
            scrotum_type=self.scrotum_type,
            has_testicles=True,
            testicle_size=self.testicle_size,
            testicle_count=2
        )
        self.scrotums.append(scrotum)
        for i in range(self.penis_count):
            self.penises.append(create_penis(
                name=f"penis_{i}",
                base_length=length,
                base_girth=girth,
                penis_type=self._get_penis_type(),
                scrotum=scrotum  # Ключевая связь: пенис получает сперму из мошонки
            ))
        self.clitorises = []
        self.vaginas = []

    def _setup_breasts(self) -> None:
        l_breast = self._create_breast(CupSize.FLAT, "left")
        r_breast = self._create_breast(CupSize.FLAT, "right")
        self.breast_grid = BreastGrid(rows=[[l_breast, r_breast]], labels=[["left", "right"]])

    def _setup_uterus(self):
        """Мужское тело не имеет матки."""
        self.uterus_system = None


@dataclass
class FemaleBody(Body):
    sex: Sex = field(default=Sex.FEMALE, init=False)
    
    vagina_count: int = 1
    clitoris_count: int = 1
    breast_cup: str = "C"
    breast_count: int = 2
    vagina_depth: float = 10.0
    vagina_width: float = 3.0
    vagina_type: VaginaType = VaginaType.HUMAN
    clitoris_size: float = 1.5
    
    def _setup_genitals(self) -> None:
        depth = self.vagina_depth or self._get_random_size("vagina_depth")
        
        for i in range(self.vagina_count):
            self.vaginas.append(create_vagina(
                vagina_type=self._get_vagina_type(),
                base_depth=depth,
                base_width=3.0 + (0.5 if self.race == Race.ORC else 0)
            ))
        
        for i in range(self.clitoris_count):
            self.clitorises.append(Clitoris(
                name=f"clitoris_{i}",
                base_length=1.5,
                can_transform=self.race in (Race.DEMON, Race.SHAPESHIFTER)
            ))

        self.penises = []
        self.scrotums = []
    
    def _setup_breasts(self) -> None:
        if self.breast_cup:
            cup = CupSize[self.breast_cup.upper()]
        else:
            # Случайный размер из пресета расы
            options = self._preset.get("breast_cup", [CupSize.B, CupSize.C])
            cup = random.choice(options)
        
        breasts = []
        labels = []
        for i in range(self.breast_count):
            side = ["left", "right", "center"][min(i, 2)]
            breasts.append(self._create_breast(cup, side))
            labels.append(f"B{i+1}")
        
        self.breast_grid = BreastGrid(rows=[breasts], labels=[labels])
    
    def _setup_uterus(self):
        """Создать матку с трубами и яичниками."""
        self.uterus_system = UterusSystem()


@dataclass
class FutanariBody(Body):
    sex: Sex = field(default=Sex.FUTANARI, init=False)
    
    penis_count: int = 1
    penis_size: float = 18.0
    penis_girth: float = 13.0
    has_scrotum: bool = True
    testicle_size: TesticleSize = TesticleSize.LARGE
    internal_testicles: bool = False
    vagina_count: int = 1
    vagina_depth: float = 12.0
    vagina_width: float = 3.5
    clitoris_count: int = 1
    clitoris_size: float = 3.0
    clitoris_enlarged: bool = True
    breast_cup: str = "E"
    breast_count: int = 2
    penis_type: PenisType = PenisType.HUMAN
    scrotum_type: ScrotumType = ScrotumType.STANDARD
    vagina_type: VaginaType = VaginaType.HUMAN


    def _setup_genitals(self) -> None:
        # Мошонка
        scrotum = None
        if self.has_scrotum:
            scrotum = create_scrotum(
                has_testicles=True,
                testicle_size=TesticleSize.LARGE,
                is_internal=self.internal_testicles,
                scrotum_type=self._get_scrotum_type()
            )
            self.scrotums.append(scrotum)
        
        # Пенис
        length = self.penis_size or (self._get_random_size("penis_length") * 1.2)  # +20% для фут
        girth = self.penis_girth or self._get_random_size("penis_girth")
        
        for i in range(self.penis_count):
            penis = create_penis(
                penis_type=self._get_penis_type(),
                base_length=length,
                base_girth=girth,
                scrotum=scrotum
            )
            self.penises.append(penis)
        
        # Влагалище (за пенисом/мошонкой)
        depth = self.vagina_depth or self._get_random_size("vagina_depth")
        for i in range(self.vagina_count):
            self.vaginas.append(create_vagina(
                vagina_type=self._get_vagina_type(),
                base_depth=depth
            ))
        
        # Клитор (обычно увеличен у фут)
        for i in range(self.vagina_count):  # Обычно 1 на влагалище
            self.clitorises.append(Clitoris(
                name=f"clitoris_{i}",
                base_length=2.5,  # Больше чем у обычной женщины
                is_enlarged=True,
                enlargement_ratio=1.5
            ))
    
    def _setup_breasts(self) -> None:
        if self.breast_cup:
            cup = CupSize[self.breast_cup.upper()]
        else:
            # Футы обычно с крупной грудью
            options = [CupSize.D, CupSize.E, CupSize.F]
            cup = random.choice(options)
        
        breasts = [self._create_breast(cup, f"B{i}") for i in range(self.breast_count)]
        self.breast_grid = BreastGrid(rows=[breasts], labels=[[f"B{i+1}" for i in range(self.breast_count)]])
        
    def _setup_uterus(self):
        """Создать матку с трубами и яичниками."""
        self.uterus_system = UterusSystem()
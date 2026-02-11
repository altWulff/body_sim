# body_sim/body/body.py
"""
Тело и его специализации.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from body_sim.core.enums import Sex, BodyType, TesticleSize, CupSize, Color, FluidType, PenisType, VaginaType, ScrotumType
from body_sim.body.stats import BodyStats
from body_sim.anatomy.genitals import Penis, Scrotum, Vagina, Clitoris, Anus, create_penis, create_vagina, create_scrotum
from body_sim.anatomy.uterus import (
    Uterus, UterusSystem, UterusState, CervixState,
    Ovary, FallopianTube, OvaryState
)
from body_sim.anatomy.breast import Breast
from body_sim.anatomy.nipple import Areola, Nipple
from body_sim.systems.grid import BreastGrid
from body_sim.systems.penetration import CrossBodyPenetration


class Body:
    def __init__(self, name: str, sex: Sex):
        self.name = name
        # ... существующая инициализация ...
        
        # Инициализация sexual encounter
        self.active_sex: Optional[CrossBodyPenetration] = None
    
    def start_sex_with(self, target: 'Body', target_organ: str = "vagina", 
                       source_organ: str = "penis") -> CrossBodyPenetration:
        """Начать половой акт с другим телом"""
        self.active_sex = CrossBodyPenetration(self, target, source_organ, target_organ)
        return self.active_sex

@dataclass
class Body:
    name: str = "Unnamed"
    sex: Sex = Sex.NONE
    body_type: BodyType = BodyType.AVERAGE
    stats: BodyStats = field(default_factory=BodyStats)
    
    breast_grid: Optional[BreastGrid] = None
    penises: List[Penis] = field(default_factory=list)
    clitorises: List[Clitoris] = field(default_factory=list)
    vaginas: List[Vagina] = field(default_factory=list)
    scrotums: List[Scrotum] = field(default_factory=list)
    anuses: List[Anus] = field(default_factory=list)
    uterus_system: Optional[UterusSystem] = None
    
    _listeners: Dict[str, List] = field(default_factory=dict, repr=False)

    active_sex: Optional[CrossBodyPenetration] = None
    
    def __post_init__(self):
        self._setup_genitals()
        self._setup_uterus()
        self._setup_breasts()
        if not self.anuses:
            self.anuses.append(Anus())
            
    def _setup_uterus(self) -> None:
        "Создание системы маток."
        pass
    
    def _setup_genitals(self) -> None:
        pass
    
    def _setup_breasts(self) -> None:
        pass
    
    def on(self, event: str, callback) -> None:
        self._listeners.setdefault(event, []).append(callback)
    
    def _emit(self, event: str, **data) -> None:
        for cb in self._listeners.get(event, []):
            cb(self, **data)

    def start_sex_with(self, target: 'Body', target_organ: str = "vagina", source_organ: str = "penis") -> CrossBodyPenetration:
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
    def total_cum_storage(self) -> float:
        total = 0.0
        for scrotum in self.scrotums:
            for testicle in scrotum.testicles:
                total += testicle.stored_fluids.get(FluidType.CUM, 0.0)
        return total

    @property
    def total_cum_capacity(self) -> float:
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
        if 0 <= clitoris_idx < len(self.clitorises):
            clit = self.clitorises[clitoris_idx]
            penis = clit.transform_to_penis(target_length, target_girth)
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
        if penis_index >= len(self.penises):
            return {"success": False, "reason": "invalid_penis_index"}
        
        penis = self.penises[penis_index]
        
        if not penis.is_erect:
            return {"success": False, "reason": "not_erect"}
        
        total_available = self.total_cum_storage
        if total_available > 0:
            for scrotum in self.scrotums:
                scrotum_cum = sum(
                    t.stored_fluids.get(FluidType.CUM, 0.0) 
                    for t in scrotum.testicles
                )
                transfer = scrotum.drain_fluid(FluidType.CUM, scrotum_cum * 0.5)
                penis.produce_cum(transfer)
        
        amount = penis.ejaculate(force)
        
        self._emit("ejaculation", penis_idx=penis_index, amount=amount, force=force)
        
        self.stats.arousal *= 0.7
        penis.flaccid()
        
        return {
            "success": True,
            "penis_index": penis_index,
            "amount": amount,
            "force": force
        }
    
    def ejaculate_all(self, force: float = 1.0) -> List[Dict[str, Any]]:
        results = []
        for i in range(len(self.penises)):
            if self.penises[i].is_erect:
                results.append(self.ejaculate(i, force))
        return results
    
    def tick(self, dt: float = 1.0) -> None:
        self.stats.tick(dt)
        
        for penis in self.penises:
            penis.tick(dt)
        
        for clit in self.clitorises:
            clit.tick(dt)
        
        for vagina in self.vaginas:
            vagina.tick(dt)
        
        for scrotum in self.scrotums:
            scrotum.tick(dt, self.stats.arousal)
            
            if scrotum.has_testicles and self.penises:
                total_production_rate = 0.0
                for testicle in scrotum.testicles:
                    cum_rate = testicle.fluid_production_rates.get(FluidType.CUM, 0.0)
                    total_production_rate += cum_rate
                
                transfer_amount = total_production_rate * dt * 0.1
                if transfer_amount > 0:
                    total_transfer = scrotum.drain_fluid(FluidType.CUM, transfer_amount)
                    
                    if total_transfer > 0:
                        per_penis = total_transfer / len(self.penises)
                        for penis in self.penises:
                            penis.produce_cum(per_penis)
        
        for anus in self.anuses:
            anus.tick(dt)
        
        if self.uterus_system:
            self.uterus_system.tick(dt)
        
        if self.breast_grid:
            from body_sim.core.fluids import FLUID_DEFS
            self.breast_grid.tick_all(FLUID_DEFS, dt)


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
        for i in range(self.penis_count):
            self.penises.append(Penis(
                name=f"penis_{i}",
                base_length=self.penis_size,
                base_girth=self.penis_girth,
                penis_type=self.penis_type
            ))
        
        self.scrotums.append(Scrotum(
            scrotum_type=self.scrotum_type,
            has_testicles=True,
            testicle_size=self.testicle_size,
            testicle_count=2
        ))
        
        self.clitorises = []
        self.vaginas = []
    
    def _setup_breasts(self) -> None:
        nipple = Nipple(base_length=0.3, base_width=0.5, color=Color.LIGHT_PINK)
        areola = Areola(base_diameter=2.5, nipples=[nipple], color=Color.LIGHT_PINK)
        breast = Breast(cup=CupSize.FLAT, areola=areola, base_elasticity=1.2)
        self.breast_grid = BreastGrid(rows=[[breast, breast]], labels=[["chest", "chest"]])

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
        for i in range(self.vagina_count):
            self.vaginas.append(Vagina(
                name=f"vagina_{i}",
                base_depth=self.vagina_depth,
                base_width=self.vagina_width,
                vagina_type=self.vagina_type
            ))
        
        for i in range(self.clitoris_count):
            self.clitorises.append(Clitoris(
                name=f"clitoris_{i}",
                base_length=self.clitoris_size
            ))
        
        self.penises = []
        self.scrotums = []
    
    def _setup_breasts(self) -> None:
        cup = CupSize[self.breast_cup.upper()]
        breasts = []
        labels = []
        
        for i in range(self.breast_count):
            nipple = Nipple(base_length=0.6, base_width=0.8, color=Color.LIGHT_PINK)
            areola = Areola(base_diameter=4.0, nipples=[nipple], color=Color.LIGHT_PINK)
            breast = Breast(cup=cup, areola=areola, base_elasticity=1.0)
            breasts.append(breast)
            labels.append(f"B{i}")
        breasts_row = [breasts]
        labels_row = [labels]
        self.breast_grid = BreastGrid(rows=breasts_row, labels=[labels])
    
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
    testicle_size: TesticleSize = TesticleSize.AVERAGE
    scrotum_type: ScrotumType = ScrotumType.STANDARD
    vagina_type: VaginaType = VaginaType.HUMAN
    
    def _setup_genitals(self) -> None:
        for i in range(self.penis_count):
            self.penises.append(Penis(
                name=f"penis_{i}",
                base_length=self.penis_size,
                base_girth=self.penis_girth,
                penis_type=self.penis_type
            ))
        
        if self.has_scrotum:
            self.scrotums.append(Scrotum(
                has_testicles=True,
                testicle_size=self.testicle_size,
                is_internal=self.internal_testicles,
                scrotum_type=self.scrotum_type
            ))
        
        for i in range(self.vagina_count):
            self.vaginas.append(Vagina(
                name=f"vagina_{i}",
                base_depth=self.vagina_depth,
                base_width=self.vagina_width,
                vagina_type=self.vagina_type
            ))
        
        for i in range(self.clitoris_count):
            enlargement = 2.0 if self.clitoris_enlarged else 1.0
            self.clitorises.append(Clitoris(
                name=f"clitoris_{i}",
                base_length=self.clitoris_size,
                is_enlarged=self.clitoris_enlarged,
                enlargement_ratio=enlargement
            ))
    
    def _setup_breasts(self) -> None:
        cup = CupSize[self.breast_cup.upper()]
        breasts = []
        labels = []
        
        for i in range(self.breast_count):
            nipple = Nipple(base_length=0.6, base_width=0.8, color=Color.LIGHT_PINK)
            areola = Areola(base_diameter=4.0, nipples=[nipple], color=Color.LIGHT_PINK)
            breast = Breast(cup=cup, areola=areola, base_elasticity=1.0)
            breasts.append(breast)
            labels.append(f"B{i}")
        breasts_row = [breasts]
        labels_row = [labels]
        self.breast_grid = BreastGrid(rows=breasts_row, labels=[labels])
        
    
    def _setup_uterus(self):
        """Создать матку с трубами и яичниками."""
        self.uterus_system = UterusSystem()
        
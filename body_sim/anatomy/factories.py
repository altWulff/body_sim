"""
Фабрики для создания гениталий.
"""
from typing import Optional
from body_sim.core.enums import PenisType, VaginaType, ScrotumType, TesticleSize
from .penis import Penis
from .vagina import Vagina
from .scrotum import Scrotum
from .testicle import Testicle


def create_penis(penis_type: PenisType = PenisType.HUMAN, 
                 base_length: Optional[float] = None,
                 base_girth: Optional[float] = None, **options) -> Penis:
    """Создать пенис заданного типа."""
    return Penis(
        base_length=base_length if base_length else 15.0,
        base_girth=base_girth if base_girth else 12.0,
        penis_type=penis_type, **options
    )


def create_vagina(vagina_type: VaginaType = VaginaType.HUMAN,
                  base_depth: Optional[float] = None, **options) -> Vagina:
    """Создать влагалище заданного типа."""
    return Vagina(
        base_depth=base_depth if base_depth else 10.0,
        vagina_type=vagina_type, **options
    )


def create_scrotum(scrotum_type: ScrotumType = ScrotumType.STANDARD,
                   testicle_count: int = 2,
                   testicle_size: TesticleSize = TesticleSize.AVERAGE, **options) -> Scrotum:
    """Создать мошонку заданного типа."""
    testicles = [Testicle(size=testicle_size) for _ in range(testicle_count)]
    return Scrotum(
        scrotum_type=scrotum_type,
        testicles=testicles,
        testicle_count=testicle_count,
        testicle_size=testicle_size, **options
    )
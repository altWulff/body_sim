"""
body_sim/
├── __init__.py              # Главный экспорт пакета
├── __main__.py              # Точка входа: python -m body_sim
├── core/                    # Ядро системы
│   ├── __init__.py
│   ├── enums.py             # ВСЕ перечисления
│   ├── constants.py         # Физические константы
│   ├── fluids.py            # Система жидкостей
│   └── types.py             # Общие типы и протоколы
├── anatomy/                 # Анатомические структуры
│   ├── __init__.py
│   ├── base.py              # Базовый класс Genital
│   ├── nipple.py            # Nipple + Areola
│   ├── breast.py            # Breast
│   └── genitals.py          # Penis, Vagina, Clitoris, Anus, Scrotum
├── body/                    # Тело как целое
│   ├── __init__.py
│   ├── stats.py             # BodyStats
│   ├── body.py              # Body + специализации
│   └── factory.py           # BodyFactory
├── systems/                 # Подсистемы
│   ├── __init__.py
│   ├── physics.py           # Физические расчёты
│   ├── lactation.py         # LactationSystem
│   ├── inflation.py         # InflationSystem
│   ├── insertion.py         # InsertionManager
│   ├── grid.py              # BreastGrid
│   ├── events.py            # EventBus
│   └── pressure.py          # Работа с давлением
└── ui/                      # Интерфейс пользователя
    ├── __init__.py
    ├── console.py           # Главная консоль
    ├── commands.py          # Регистрация команд
    ├── render.py            # Базовый рендер
    └── rich_render.py       # Rich-рендеринг
"""

"""
Breast & Body Simulation System

Основной пакет для симуляции физиологических процессов.
"""

__version__ = "0.2.0"
__author__ = "Simulation Team"

# Удобный доступ к основным классам
from body_sim.core.enums import (
    CupSize, FluidType, BreastState,
    Sex, BodyType, PenisType, VaginaType,
    LactationState, NippleType, NippleShape,
    InsertableType, InsertableMaterial,
    Color, AreolaTexture, PressureTier
)

from body_sim.core.fluids import BreastFluid, FluidMixture

from body_sim.anatomy.nipple import Nipple, Areola
from body_sim.anatomy.breast import Breast
from body_sim.anatomy.genitals import (
    Genital, Penis, Clitoris, Vagina, Anus,
    Testicle, Scrotum
)

from body_sim.body.stats import BodyStats
from body_sim.body.body import Body, MaleBody, FemaleBody, FutanariBody
from body_sim.body.factory import BodyFactory

from body_sim.systems.grid import BreastGrid
from body_sim.systems.events import EventBus, EventType, Event

__all__ = [
    # Версия
    "__version__",
    
    # Enums
    "CupSize", "FluidType", "BreastState",
    "Sex", "BodyType", "PenisType", "VaginaType",
    "LactationState", "NippleType", "NippleShape",
    "InsertableType", "InsertableMaterial",
    "Color", "AreolaTexture", "PressureTier",
    
    # Fluids
    "BreastFluid", "FluidMixture",
    
    # Anatomy
    "Nipple", "Areola", "Breast",
    "Genital", "Penis", "Clitoris", "Vagina", "Anus",
    "Testicle", "Scrotum",
    
    # Body
    "BodyStats", "Body", "MaleBody", "FemaleBody", "FutanariBody",
    "BodyFactory",
    
    # Systems
    "BreastGrid", "EventBus", "EventType", "Event",
]

# body_sim/systems/__init__.py

# Инфляция и растяжение тканей
from body_sim.systems.inflation import (
    StretchState,
    InflationProfile,
    InflationSystem
)

# Управление вставленными объектами
from body_sim.systems.insertion import (
    InsertionType,
    InsertedObject,
    InsertionManager
)

# Лактация
from body_sim.systems.lactation import (
    LactationState,
    LactationProfile,
    LactationSystem
)

# Физика
from body_sim.systems.physics import (
    PhysicsState,
    PhysicsEngine
)

# Давление
from body_sim.systems.pressure import (
    PressureTier,
    PressureController
)

# Статистика
from body_sim.systems.stats import StatisticsService

__all__ = [
    # Inflation
    'StretchState',
    'InflationProfile',
    'InflationSystem',
    
    # Insertion
    'InsertionType',
    'InsertedObject',
    'InsertionManager',
    
    # Lactation
    'LactationState',
    'LactationProfile',
    'LactationSystem',
    
    # Physics
    'PhysicsState',
    'PhysicsEngine',
    
    # Pressure
    'PressureTier',
    'PressureController',
    
    # Stats
    'StatisticsService',
]


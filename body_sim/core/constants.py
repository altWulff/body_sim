# body_sim/core/constants.py
"""
Физические и игровые константы.
"""

# ========== Давление ==========
PRESSURE_NORMAL = 0.5
PRESSURE_TENSE = 1.0
PRESSURE_OVERPRESSURED = 2.0
PRESSURE_LEAK_MIN = 0.8
PRESSURE_TIER_HIGH = 1.2
PRESSURE_TIER_CRITICAL = 1.6

# ========== Соски ==========
GAPE_AUTO_OPEN = 0.15
GAPE_LOCK_THRESHOLD = 0.25
GAPE_OPEN_SPEED = 0.05
GAPE_CLOSE_SPEED = 0.03

NIPPLE_STRETCH_FACTOR = 3.0
NIPPLE_WIDTH_GROWTH = 0.02
NIPPLE_STRETCH_RECOVERY = 0.0

# ========== Эластичность ==========
ELASTICITY_SAG_LOSS = 0.4
ELASTICITY_ADJUST_RATE = 0.2

# ========== Провисание (Sag) ==========
SAG_FILL_GAIN = 0.15
SAG_WEIGHT_GAIN = 0.1
SAG_ELASTICITY_GAIN = 0.3
SAG_RECOVERY = 0.02
SAG_PRESSURE_GAIN = 0.4
SAG_MAX_INCREASE_PER_TICK = 0.02
SAG_DECREASE_PER_TICK = 0.05
MAX_SAG = 1.0
# uterus
UTERUS_MAX_STRETCH = 500.0

# ========== Размерные множители для sag ==========
SAG_SIZE_FACTOR = {
    'FLAT': 0.2, 'MICRO': 0.3,
    'AAA': 0.5, 'AA': 0.6, 'A': 0.7, 'B': 0.8, 'C': 1.0,
    'D': 1.2, 'E': 1.4, 'F': 1.6,
    'G': 1.8, 'H': 2.0, 'I': 2.3, 'J': 2.6, 'K': 3.0,
    'L': 3.5, 'M': 4.0, 'N': 4.8, 'O': 5.5, 'P': 6.5,
    'Q': 8.0, 'R': 10.0, 'S': 12.0, 'T': 15.0,
    'U': 20.0, 'V': 25.0, 'W': 30.0, 'X': 40.0,
    'Y': 50.0, 'Z': 65.0, 'ULTRA': 100.0
}

from enum import Enum

class CupSize(Enum):
    """Размеры груди с базовыми объемами в мл."""
    AAA = 120; AA = 150; A = 180; B = 240; C = 310; D = 400; DD = 520
    E = 650; F = 800; G = 1000; H = 1250; I = 1550; J = 1900
    K = 2300; L = 2800; M = 3500; N = 4500; O = 6000; P = 8000
    Q = 12000; R = 18000; S = 28000; T = 45000; U = 75000
    V = 120000; W = 200000; X = 350000; Y = 600000; Z = 1000000
    
    @property
    def base_volume(self):
        return self.value
    
    @classmethod
    def from_volume(cls, volume: float) -> 'CupSize':
        """Найти ближайший размер по объему."""
        for cup in reversed(list(cls)):
            if volume >= cup.base_volume:
                return cup
        return cls.AAA
        
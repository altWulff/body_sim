# tests/anatomy/chest/test_cup_size.py
import pytest
from body_sim.anatomy.chest.cup_size import CupSize


class TestCupSize:
    def test_cup_size_values(self):
        """Тест значений объемов для разных размеров."""
        assert CupSize.AAA.value == 120
        assert CupSize.C.value == 310
        assert CupSize.Z.value == 1000000

    def test_base_volume_property(self):
        """Тест свойства base_volume."""
        assert CupSize.D.base_volume == 400
        assert CupSize.G.base_volume == 1000

    def test_from_volume_exact_match(self):
        """Тест определения размера по точному объему."""
        assert CupSize.from_volume(310) == CupSize.C
        assert CupSize.from_volume(1000) == CupSize.G

    def test_from_volume_between_sizes(self):
        """Тест определения размера для объема между размерами."""
        # Между C (310) и D (400)
        assert CupSize.from_volume(350) == CupSize.C
        assert CupSize.from_volume(400) == CupSize.D

    def test_from_volume_below_minimum(self):
        """Тест для объема меньше минимального."""
        assert CupSize.from_volume(50) == CupSize.AAA
        assert CupSize.from_volume(0) == CupSize.AAA

    def test_from_volume_above_maximum(self):
        """Тест для объема больше максимального."""
        assert CupSize.from_volume(2000000) == CupSize.Z

    def test_ordering(self):
        """Тест что размеры упорядочены правильно."""
        sizes = list(CupSize)
        values = [s.value for s in sizes]
        assert values == sorted(values)

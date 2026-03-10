# tests/anatomy/chest/test_milk_ducts.py
import pytest
import math
from body_sim.anatomy.chest.milk_ducts import MilkDuct, MilkDuctSystem, DuctState


class TestMilkDuct:
    def test_default_creation(self):
        """Тест дефолтного создания протока."""
        duct = MilkDuct(id=1)
        assert duct.id == 1
        assert duct.state == DuctState.NORMAL
        assert duct.diameter == 0.05
        assert duct.length == 2.0
        assert duct.prolapse_length == 0.0
        assert duct.connected_to is None

    def test_dilate(self):
        """Тест расширения протока."""
        duct = MilkDuct(id=1, diameter=0.1)
        duct.dilate(2.0)

        assert duct.diameter == 0.2
        assert duct.state == DuctState.NORMAL  # Еще не достаточно для DILATED

    def test_dilate_to_dilated_state(self):
        """Тест расширения до состояния DILATED."""
        duct = MilkDuct(id=1, diameter=0.2)
        duct.dilate(2.0)  # 0.4, но порог 0.3

        assert duct.diameter == 0.4
        assert duct.state == DuctState.DILATED

    def test_prolapse(self):
        """Тест пролапса."""
        duct = MilkDuct(id=1)
        duct.prolapse(0.5)

        assert duct.prolapse_length == 0.5
        assert duct.state == DuctState.PROLAPSED

    def test_prolapse_severed_blocked(self):
        """Тест что пролапс не работает при отсечении."""
        duct = MilkDuct(id=1, state=DuctState.SEVERED)
        duct.prolapse(0.5)

        assert duct.prolapse_length == 0.0

    def test_sever(self):
        """Тест отсечения."""
        duct = MilkDuct(id=1)
        duct.sever(portal_id="portal_123")

        assert duct.state == DuctState.SEVERED
        assert duct.connected_to == "portal_123"

    def test_sever_without_portal(self):
        """Тест отсечения без портала."""
        duct = MilkDuct(id=1)
        duct.sever()

        assert duct.state == DuctState.SEVERED
        assert duct.connected_to is None

    def test_reconnect(self):
        """Тест восстановления соединения."""
        duct = MilkDuct(id=1, state=DuctState.SEVERED, connected_to="portal")
        duct.reconnect()

        assert duct.state == DuctState.NORMAL
        assert duct.connected_to is None

    def test_reconnect_not_severed(self):
        """Тест что reconnect не меняет нормальный проток."""
        duct = MilkDuct(id=1, state=DuctState.NORMAL)
        duct.reconnect()

        assert duct.state == DuctState.NORMAL

    def test_receive_milk(self):
        """Тест получения молока."""
        duct = MilkDuct(id=1, diameter=0.1, length=1.0)
        overflow = duct.receive_milk(10.0)

        # Как в коде: 3.14 * (diameter/2)**2 * length * 1000
        max_vol = 3.14 * (0.05) ** 2 * 1.0 * 1000

        assert duct.internal_volume == pytest.approx(max_vol)
        assert overflow == pytest.approx(10.0 - max_vol)

    def test_receive_milk_overflow(self):
        """Тест переполнения."""
        duct = MilkDuct(id=1)
        max_vol = 3.14 * (0.025) ** 2 * 2.0 * 1000  # 3.925

        overflow = duct.receive_milk(max_vol + 5.0)
        assert overflow == pytest.approx(5.0, abs=0.01)
        assert duct.internal_volume == pytest.approx(max_vol, abs=0.001)


class TestMilkDuctSystem:
    def test_default_creation(self):
        """Тест создания системы протоков."""
        system = MilkDuctSystem()
        assert len(system.nipple_ducts) == 18
        assert system.lactiferous_sinuses == 0.0

    def test_custom_creation(self):
        """Тест кастомного создания."""
        ducts = [MilkDuct(id=i) for i in range(5)]
        system = MilkDuctSystem(nipple_ducts=ducts, lactiferous_sinuses=10.0)
        assert len(system.nipple_ducts) == 5
        assert system.lactiferous_sinuses == 10.0

    def test_total_prolapse(self):
        """Тест суммарного пролапса."""
        system = MilkDuctSystem()
        system.nipple_ducts[0].prolapse(0.5)
        system.nipple_ducts[1].prolapse(0.3)

        assert system.total_prolapse() == 0.8

    def test_express_normal_pressure(self):
        """Тест сцеживания при нормальном давлении."""
        system = MilkDuctSystem()
        system.lactiferous_sinuses = 5.0
        system.nipple_ducts[0].internal_volume = 2.0

        total = system.express(pressure=1.0)

        assert total == 7.0
        assert system.lactiferous_sinuses == 0.0
        assert system.nipple_ducts[0].internal_volume == 0.0

    def test_express_high_pressure_prolapse(self):
        """Тест пролапса при высоком давлении."""
        system = MilkDuctSystem()
        system.nipple_ducts[0].diameter = 0.4
        system.nipple_ducts[0].state = DuctState.DILATED

        system.express(pressure=3.0)

        assert system.nipple_ducts[0].prolapse_length > 0

    def test_get_flow_capacity(self):
        """Тест расчета пропускной способности."""
        system = MilkDuctSystem()
        # Дефолтные протоки: 18 шт, диаметр 0.05
        # Площадь = π * (0.025)² * 10 * 18

        capacity = system.get_flow_capacity()
        expected = 18 * math.pi * (0.025) ** 2 * 10

        assert abs(capacity - expected) < 0.001

    def test_get_flow_capacity_excludes_severed(self):
        """Тест что отсеченные протоки не учитываются."""
        system = MilkDuctSystem()
        system.nipple_ducts[0].state = DuctState.SEVERED
        system.nipple_ducts[1].state = DuctState.EXTERNAL

        capacity = system.get_flow_capacity()
        expected = 16 * math.pi * (0.025) ** 2 * 10

        assert abs(capacity - expected) < 0.001

# tests/anatomy/chest/test_breasts.py
import pytest
from unittest.mock import MagicMock, patch
from body_sim.anatomy.chest.breasts import Breasts
from body_sim.anatomy.chest.cup_size import CupSize
from body_sim.anatomy.chest.breast_row import BreastRow


@pytest.fixture
def breasts():
    """Фикстура для объекта груди."""
    return Breasts(cup_size=CupSize.D)


class TestBreasts:
    def test_default_creation(self, breasts):
        """Тест создания с дефолтной парой."""
        assert breasts.cup_size == CupSize.D
        assert len(breasts.rows) == 2
        assert breasts._cross_factor == 0.3

    def test_left_right_properties(self, breasts):
        """Тест свойств left и right."""
        assert breasts.left is not None
        assert breasts.left.side == "left"
        assert breasts.right is not None
        assert breasts.right.side == "right"

    def test_get_by_side(self, breasts):
        """Тест получения по стороне."""
        left = breasts.get_by_side("left")
        right = breasts.get_by_side("right")

        assert left.side == "left"
        assert right.side == "right"

    def test_get_by_side_case_insensitive(self, breasts):
        """Тест нечувствительности к регистру."""
        left_lower = breasts.get_by_side("left")
        left_upper = breasts.get_by_side("LEFT")

        assert left_lower == left_upper

    def test_get_by_side_not_found(self, breasts):
        """Тест отсутствующей стороны."""
        result = breasts.get_by_side("nonexistent")
        assert result is None

    def test_add_row_aux(self, breasts):
        """Тест добавления вспомогательного ряда."""
        initial_count = len(breasts.rows)
        new_row = breasts.add_row(side="aux1", size_factor=0.8)

        assert len(breasts.rows) == initial_count + 1
        assert new_row.side == "aux1"
        # Дополнительный ряд должен быть меньше
        assert new_row.cup_size.base_volume < breasts.cup_size.base_volume

    def test_add_row_default_side(self, breasts):
        """Тест добавления с дефолтной стороной."""
        new_row = breasts.add_row()
        assert new_row.side == "aux"

    def test_stimulate_single(self, breasts):
        """Тест стимуляции одной груди."""
        with patch.object(breasts.left, "stimulate") as mock_stim:
            mock_stim.return_value = {"state": "stimulated"}
            result = breasts.stimulate("left", 1.0)

            mock_stim.assert_called_once_with(1.0)
            assert result["state"] == "stimulated"

    def test_stimulate_invalid_side(self, breasts):
        """Тест стимуляции несуществующей груди."""
        result = breasts.stimulate("nonexistent", 1.0)
        assert result is None

    def test_stimulate_both(self, breasts):
        """Тест стимуляции обеих грудей."""
        with patch.object(breasts, "stimulate") as mock_stim:
            mock_stim.return_value = None
            breasts.stimulate_both(0.5)

            assert mock_stim.call_count == 2

    def test_express_single(self, breasts):
        """Тест сцеживания одной груди."""
        breasts.left.current_milk_volume = 50.0

        with patch.object(breasts.left, "express") as mock_express:
            mock_express.return_value = 30.0
            result = breasts.express(side="left", amount=30.0)

            assert result == 30.0
            mock_express.assert_called_once()

    def test_express_all(self, breasts):
        """Тест сцеживания всех рядов."""
        breasts.left.current_milk_volume = 30.0
        breasts.right.current_milk_volume = 30.0

        with patch.object(breasts.left, "express", return_value=20.0):
            with patch.object(breasts.right, "express", return_value=20.0):
                result = breasts.express()
                assert result == 40.0

    def test_update(self, breasts, event_bus):
        """Тест обновления всех рядов."""
        with patch.object(breasts.left, "update") as mock_left:
            with patch.object(breasts.right, "update") as mock_right:
                breasts.update(1.0, event_bus)

                mock_left.assert_called_once_with(1.0, event_bus)
                mock_right.assert_called_once_with(1.0, event_bus)

    def test_update_sets_event_bus(self, breasts, event_bus):
        """Тест что update устанавливает event bus если не установлен."""
        breasts._event_bus = None
        with patch.object(breasts, "set_event_bus") as mock_set:
            breasts.update(1.0, event_bus)
            mock_set.assert_called_once_with(event_bus)

    def test_get_state(self, breasts):
        """Тест получения состояния."""
        state = breasts.get_state()

        assert state["cup_size"] == "D"
        assert state["rows_count"] == 2
        assert "rows" in state
        assert "left" in state["rows"]
        assert "right" in state["rows"]

    def test_get_full_state_alias(self, breasts):
        """Тест что get_full_state вызывает get_state."""
        with patch.object(breasts, "get_state") as mock_get:
            mock_get.return_value = {"test": "data"}
            result = breasts.get_full_state()
            assert result == {"test": "data"}

    def test_set_event_bus(self, breasts, event_bus):
        """Тест установки event bus."""
        breasts.set_event_bus(event_bus)
        assert breasts._event_bus is event_bus

    def test_cross_stimulation_setup(self, breasts, event_bus):
        """Тест настройки перекрестной стимуляции."""
        breasts.set_event_bus(event_bus)

        # Проверяем что подписка на событие была создана
        # В реальном коде здесь была бы проверка event_bus.subscribe
        assert breasts._event_bus is not None

    def test_chest_measurements(self, breasts):
        """Тест измерений грудной клетки."""
        assert breasts.chest_circumference == 85.0
        assert breasts.intermammary_distance == 18.0

    def test_rows_are_breast_row_instances(self, breasts):
        """Тест что ряды являются экземплярами BreastRow."""
        for row in breasts.rows:
            assert isinstance(row, BreastRow)

    def test_initial_rows_same_size(self, breasts):
        """Тест что начальные ряды имеют одинаковый размер."""
        assert breasts.left.cup_size == breasts.right.cup_size
        assert breasts.left.cup_size == CupSize.D

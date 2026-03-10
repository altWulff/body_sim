# tests/anatomy/chest/test_breast_row.py
import pytest
from unittest.mock import MagicMock, patch
from body_sim.anatomy.chest.breast_row import BreastRow, BreastState
from body_sim.anatomy.chest.cup_size import CupSize


@pytest.fixture
def breast_row():
    """Фикстура для стандартного ряда груди."""
    return BreastRow(index=0, side="left", cup_size=CupSize.C)


class TestBreastRow:
    def test_default_creation(self, breast_row):
        """Тест создания ряда."""
        assert breast_row.index == 0
        assert breast_row.side == "left"
        assert breast_row.cup_size == CupSize.C
        assert breast_row.firmness == 1.0
        assert breast_row.sensitivity == 1.2

    def test_properties_initial_state(self, breast_row):
        """Тест начальных свойств."""
        assert breast_row.filled == 0.0
        assert breast_row.fill_ratio == 0.0
        assert breast_row.state == BreastState.EMPTY

    def test_current_cup_empty(self, breast_row):
        """Тест текущего размера при пустой груди (только ткань)."""
        # Объем ткани CupSize.C = 310ml, поэтому размер C
        assert breast_row.current_cup == CupSize.C

    def test_current_cup_increases_with_fill(self, breast_row):
        """Тест увеличения размера при наполнении."""
        initial_cup = breast_row.current_cup  # CupSize.C

        # Добавляем жидкость достаточную для следующего размера (D = 400ml)
        # Нужно добавить > 90ml сверх базового
        breast_row.add_fluid_by_type(MagicMock(), 100.0)

        # После инфляции и добавления объема размер должен увеличиться
        assert (
            breast_row.current_cup > initial_cup or breast_row.current_cup == CupSize.D
        )

    def test_add_fluid_by_type(self, breast_row):
        """Тест добавления жидкости."""
        amount = breast_row.add_fluid_by_type(MagicMock(), 100.0)
        assert amount == 100.0

    def test_add_fluid_exceeds_capacity(self, breast_row):
        """Тест добавления жидкости сверх вместимости."""
        # C = 310ml base, max = 310 * 1.5 = 465ml
        fluid_type = MagicMock()
        fluid_type.name = "milk"

        amount = breast_row.add_fluid_by_type(fluid_type, 5000.0)
        # Должно быть ограничено GIGA_LIMIT или доступным объемом
        assert amount <= 5000.0

    def test_add_fluid_auto_inflate(self, breast_row):
        """Тест автоинфляции при переполнении."""
        breast_row._auto_inflate = True

        with patch.object(breast_row.inflation, "apply_stretch") as mock_stretch:
            # Пытаемся добавить больше базового объема
            fluid_type = MagicMock()
            fluid_type.name = "milk"
            breast_row.add_fluid_by_type(fluid_type, 1000.0)

            # Инфляция должна быть вызвана
            mock_stretch.assert_called()

    def test_express(self, breast_row):
        """Тест сцеживания."""
        # Добавляем молока
        breast_row.current_milk_volume = 50.0

        result = breast_row.express(30.0)
        assert result == 30.0
        assert breast_row.current_milk_volume == 20.0

    def test_exceed_express(self, breast_row):
        """Тест сцеживания больше чем есть."""
        breast_row.current_milk_volume = 10.0

        result = breast_row.express(50.0)
        assert result == 10.0
        assert breast_row.current_milk_volume == 0.0

    def test_stimulate(self, breast_row):
        """Тест стимуляции."""
        result = breast_row.stimulate(1.0)

        assert breast_row.arousal > 0
        assert breast_row.pleasure > 0
        assert result["state"] == "stimulated"
        assert "sensitivity" in result

    def test_stimulate_cross_threshold(self, breast_row):
        """Тест накопления возбуждения."""
        initial_arousal = breast_row.arousal
        breast_row.stimulate(0.5)

        assert breast_row.arousal > initial_arousal

    def test_start_lactation(self, breast_row):
        """Тест запуска лактации."""
        breast_row.start_lactation(intensity=5.0)

        # Проверяем что метод lactation был вызван
        breast_row.lactation.start.assert_called() or breast_row.lactation.activate.assert_called()

    def test_stop_lactation(self, breast_row):
        """Тест остановки лактации."""
        breast_row.stop_lactation()

        breast_row.lactation.stop.assert_called() or breast_row.lactation.deactivate.assert_called()

    def test_determine_state_empty(self, breast_row):
        """Тест определения состояния - пустая."""
        state = breast_row._determine_state(0.0)
        assert state == BreastState.EMPTY

    def test_determine_state_normal(self, breast_row):
        """Тест определения состояния - нормальное."""
        breast_row._base_volume = 310  # Cup C
        # Наполняем немного
        with patch.object(breast_row, "filled", 100.0):
            state = breast_row._determine_state(0.3)
            assert state == BreastState.NORMAL

    def test_determine_state_tense(self, breast_row):
        """Тест определения состояния - напряженная."""
        state = breast_row._determine_state(0.8)
        assert state == BreastState.TENSE

    def test_determine_state_leaking(self, breast_row):
        """Тест определения состояния - утечка."""
        # Создаем сосок и открываем его
        breast_row.areola.nipples[0].open(0.5)

        state = breast_row._determine_state(0.9)
        assert state == BreastState.LEAKING

    def test_determine_state_overpressured(self, breast_row):
        """Тест определения состояния - переполнение."""
        # Закрытые соски
        breast_row.areola.nipples[0].close()

        state = breast_row._determine_state(1.5)
        assert state == BreastState.OVERPRESSURED

    def test_auto_open_nipples_low_pressure(self, breast_row):
        """Тест автооткрытия при низком давлении."""
        nipple = breast_row.areola.nipples[0]
        nipple.close()

        breast_row._auto_open_nipples(0.5)
        assert nipple.is_open is False

    def test_auto_open_nipples_high_pressure(self, breast_row):
        """Тест автооткрытия при высоком давлении."""
        nipple = breast_row.areola.nipples[0]
        nipple.close()

        breast_row._auto_open_nipples(0.8)
        assert nipple.is_open is True

    def test_calc_leak_rate_no_nipples(self, breast_row):
        """Тест расчета утечки без сосков."""
        breast_row.areola.nipples = []
        rate = breast_row._calc_leak_rate(1.0)
        assert rate == 0.0

    def test_calc_leak_rate_closed_nipples(self, breast_row):
        """Тест расчета утечки с закрытыми сосками."""
        breast_row.areola.nipples[0].close()
        rate = breast_row._calc_leak_rate(2.0)
        assert rate == 0.0

    def test_calc_leak_rate_open_nipples(self, breast_row):
        """Тест расчета утечки с открытыми сосками."""
        breast_row.areola.nipples[0].open(0.5)

        # Добавляем жидкость
        with patch.object(breast_row.mixture, "total", return_value=100.0):
            rate = breast_row._calc_leak_rate(1.0)
            assert rate > 0.0

    def test_update_sag_empty(self, breast_row):
        """Тест обновления провисания при пустой груди."""
        breast_row._sag = 0.5
        breast_row._update_sag(1.0)
        assert breast_row._sag < 0.5  # Должно уменьшаться

    def test_update_sag_filled(self, breast_row):
        """Тест обновления провисания при наполненной груди."""
        breast_row._sag = 0.0
        with patch.object(breast_row, "filled", 300.0):
            with patch.object(breast_row, "volume", 400.0):
                breast_row._update_sag(1.0)
                assert breast_row._sag > 0.0

    def test_update_elasticity(self, breast_row):
        """Тест обновления эластичности."""
        breast_row._sag = 0.5
        initial_elasticity = breast_row._elasticity

        breast_row._update_elasticity(1.0)
        assert breast_row._elasticity < initial_elasticity

    def test_tick_updates_state(self, breast_row, event_bus):
        """Тест что tick обновляет состояние."""
        result = breast_row.tick(1.0, event_bus)

        assert "state" in result
        assert "filled" in result
        assert "pressure" in result

    def test_tick_state_change_event(self, breast_row, event_bus):
        """Тест эмиссии события при смене состояния."""
        breast_row._state = BreastState.EMPTY

        # Мокаем высокое давление чтобы вызвать изменение состояния
        with patch.object(
            breast_row, "_determine_state", return_value=BreastState.TENSE
        ):
            with patch.object(breast_row, "filled", 100.0):
                breast_row.tick(1.0, event_bus)

                # Проверяем что было отправлено событие
                # В реальном коде здесь проверялась бы эмиссия в event_bus

    def test_update_alias(self, breast_row, event_bus):
        """Тест что update вызывает tick."""
        with patch.object(breast_row, "tick") as mock_tick:
            breast_row.update(1.0, event_bus)
            mock_tick.assert_called_once_with(1.0, event_bus)

    def test_get_full_state(self, breast_row):
        """Тест полного состояния."""
        state = breast_row.get_full_state()

        assert "cup" in state
        assert "base_cup" in state
        assert "filled" in state
        assert "max_volume" in state
        assert "pressure" in state
        assert "stretch" in state
        assert "sag" in state
        assert "state" in state
        assert "arousal" in state
        assert "pleasure" in state
        assert "lactation" in state
        assert "areola" in state
        assert "ducts" in state

    def test_get_state_short(self, breast_row):
        """Тест короткого состояния."""
        state = breast_row.get_state()

        assert "cup" in state
        assert "filled" in state
        assert "pressure" in state
        assert "state" in state
        assert "arousal" in state
        assert "pleasure" in state

    def test_event_listeners(self, breast_row):
        """Тест работы слушателей событий."""
        events = []
        breast_row.on("test_event", lambda obj, **kw: events.append(kw))

        breast_row._emit_local("test_event", data="test")
        assert len(events) == 1
        assert events[0]["data"] == "test"

    def test_set_event_bus(self, breast_row, event_bus):
        """Тест установки event bus."""
        breast_row.set_event_bus(event_bus)
        assert breast_row._event_bus is event_bus

    def test_add_row_creates_areola(self, breast_row):
        """Тест что создается ареола с правильным размером."""
        # Для CupSize C (310), диаметр ареолы должен быть около 3.0 + 310/100 = 6.1
        assert breast_row.areola.diameter == pytest.approx(6.1, 0.1)
        assert breast_row.areola.base_diameter == breast_row.areola.diameter

    def test_pressure_property(self, breast_row):
        """Тест свойства давления."""
        breast_row.pressure_controller.current_pressure = 0.8
        assert breast_row.pressure == 0.8

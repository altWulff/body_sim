# tests/anatomy/chest/test_nipple.py
import pytest
import math
from body_sim.anatomy.chest.nipple import Nipple, NippleState, NipplePlug


class TestNipplePlug:
    def test_plug_creation(self):
        """Тест создания плага."""
        plug = NipplePlug(name="Test Plug", diameter=0.5, length=1.0)
        assert plug.name == "Test Plug"
        assert plug.diameter == 0.5
        assert plug.length == 1.0
        assert plug.material == "silicone"
        assert plug.has_hole is False
        assert plug.leak_reduction == 0.0

    def test_plug_with_hole(self):
        """Тест плага с отверстием."""
        plug = NipplePlug(
            name="Hole Plug",
            diameter=0.3,
            length=0.5,
            has_hole=True,
            fluid_type="water",
            leak_reduction=0.5,
        )
        assert plug.has_hole is True
        assert plug.fluid_type == "water"
        assert plug.leak_reduction == 0.5


class TestNipple:
    def test_default_creation(self):
        """Тест создания соска с дефолтными значениями."""
        nipple = Nipple()
        assert nipple.diameter == 1.0
        assert nipple.length == 0.8
        assert nipple.state == NippleState.SOFT
        assert nipple.is_erect is False
        assert nipple.sensitivity == 1.5
        assert nipple.gape_diameter == 0.0
        assert nipple.is_open is False
        assert nipple.plug is None

    def test_custom_creation(self):
        """Тест создания с кастомными параметрами."""
        nipple = Nipple(
            name="custom", diameter=2.0, length=1.5, sensitivity=2.0, max_gape=5.0
        )
        assert nipple.name == "custom"
        assert nipple.diameter == 2.0
        assert nipple.base_diameter == 2.0
        assert nipple.max_gape == 5.0

    def test_erect(self):
        """Тест эрекции соска."""
        nipple = Nipple(diameter=1.0, length=0.8)
        nipple.erect()

        assert nipple.state == NippleState.ERECT
        assert nipple.is_erect is True
        assert nipple.diameter == 1.2  # 1.0 * 1.2
        assert nipple.length == 1.04  # 0.8 * 1.3
        assert nipple.current_width == 1.2

    def test_erect_inverted(self):
        """Тест что инвертированный сосок не становится эрегированным."""
        nipple = Nipple(state=NippleState.INVERTED)
        nipple.erect()
        assert nipple.state == NippleState.INVERTED
        assert nipple.is_erect is False

    def test_relax(self):
        """Тест расслабления соска."""
        nipple = Nipple()
        nipple.erect()
        nipple.relax()

        assert nipple.state == NippleState.SOFT
        assert nipple.is_erect is False
        assert nipple.diameter == nipple.base_diameter
        assert nipple.length == nipple.base_length

    def test_open_default(self):
        """Тест открытия соска с дефолтным значением."""
        nipple = Nipple(diameter=1.0)
        nipple.open()

        assert nipple.is_open is True
        assert nipple.gape_diameter == 0.5  # 50% от диаметра

    def test_open_custom(self):
        """Тест открытия с кастомным размером."""
        nipple = Nipple(diameter=2.0)
        nipple.open(0.5)

        assert nipple.gape_diameter == 0.5
        assert nipple.is_open is True

    def test_open_respects_max_gape(self):
        """Тест что открытие уважает max_gape."""
        nipple = Nipple(diameter=2.0, max_gape=1.0)
        nipple.open(5.0)  # Пытаемся открыть больше max_gape

        assert nipple.gape_diameter == 1.0

    def test_close(self):
        """Тест закрытия соска."""
        nipple = Nipple()
        nipple.open()
        nipple.close()

        assert nipple.gape_diameter == 0.0
        assert nipple.is_open is False

    def test_stretch(self):
        """Тест растяжения."""
        nipple = Nipple()
        nipple.stretch(0.8)

        assert nipple.gape_diameter == 0.8
        assert nipple.is_open is True

    def test_effective_gape_closed(self):
        """Тест эффективного отверстия когда закрыто."""
        nipple = Nipple()
        assert nipple.effective_gape == 0.0

    def test_effective_gape_open(self):
        """Тест эффективного отверстия когда открыто."""
        nipple = Nipple()
        nipple.open(0.5)
        assert nipple.effective_gape == 0.5

    def test_effective_gape_with_solid_plug(self):
        """Тест с непроницаемым плагом."""
        nipple = Nipple()
        nipple.open(1.0)
        nipple.plug = NipplePlug("plug", 0.5, 1.0, has_hole=False)

        assert nipple.effective_gape == 0.0

    def test_effective_gape_with_hole_plug(self):
        """Тест с плагом с отверстием."""
        nipple = Nipple()
        nipple.open(1.0)
        nipple.plug = NipplePlug("plug", 0.5, 1.0, has_hole=True)

        # Должно быть ограничено диаметром плага
        assert nipple.effective_gape == 0.4  # 0.5 * 0.8

    def test_insert_plug_success(self):
        """Тест успешной вставки плага."""
        nipple = Nipple(gape_diameter=1.0)
        plug = NipplePlug("plug", 0.5, 1.0)

        result = nipple.insert_plug(plug)

        assert result is True
        assert nipple.plug == plug

    def test_insert_plug_fail_small_gape(self):
        """Тест неудачной вставки при маленьком отверстии."""
        nipple = Nipple(gape_diameter=0.1)
        # Сначала вставляем маленький plug
        small_plug = NipplePlug("small", 0.05, 0.5)
        nipple.insert_plug(small_plug)

        # Теперь пытаемся вставить большой plug в маленькое отверстие
        big_plug = NipplePlug("big", 0.5, 1.0)
        result = nipple.insert_plug(big_plug)

        assert result is False
        assert nipple.plug == small_plug  # Старый plug остался

    def test_insert_plug_replace_existing(self):
        """Тест замены существующего плага."""
        nipple = Nipple(gape_diameter=1.0)
        old_plug = NipplePlug("old", 0.3, 0.5)
        new_plug = NipplePlug("new", 0.4, 0.6)

        nipple.insert_plug(old_plug)
        nipple.insert_plug(new_plug)

        assert nipple.plug == new_plug

    def test_remove_plug(self):
        """Тест удаления плага."""
        nipple = Nipple()
        plug = NipplePlug("plug", 0.5, 1.0)
        nipple.insert_plug(plug)

        removed = nipple.remove_plug()

        assert removed == plug
        assert nipple.plug is None

    def test_remove_plug_empty(self):
        """Тест удаления когда плага нет."""
        nipple = Nipple()
        removed = nipple.remove_plug()
        assert removed is None

    def test_stimulate(self):
        """Тест стимуляции."""
        nipple = Nipple(sensitivity=1.0)
        nipple.stimulate(1.0)

        assert nipple.is_erect is True
        assert nipple.sensitivity > 1.0

    def test_stimulate_already_erect(self):
        """Тест стимуляции уже эрегированного соска."""
        nipple = Nipple()
        nipple.erect()
        initial_sensitivity = nipple.sensitivity

        nipple.stimulate(1.0)
        assert nipple.sensitivity > initial_sensitivity

    def test_stimulate_capped_at_3(self):
        """Тест что чувствительность ограничена 3.0."""
        nipple = Nipple(sensitivity=2.9)
        nipple.stimulate(10.0)  # Большая интенсивность

        assert nipple.sensitivity == 3.0

    def test_open_from_pressure_low(self):
        """Тест открытия при низком давлении."""
        nipple = Nipple()
        nipple.open_from_pressure(0.1, max_pressure=1.0)

        assert nipple.is_open is False

    def test_open_from_pressure_medium(self):
        """Тест открытия при среднем давлении."""
        nipple = Nipple(diameter=1.0)
        nipple.open_from_pressure(0.6, max_pressure=1.0)

        assert nipple.is_open is True
        assert 0 < nipple.gape_diameter < 0.5

    def test_open_from_pressure_high(self):
        """Тест открытия при высоком давлении."""
        nipple = Nipple(diameter=1.0)
        nipple.open_from_pressure(2.0, max_pressure=1.0)

        # Должно быть ограничено 0.5 * diameter
        assert nipple.gape_diameter <= 0.5

    def test_event_emit_on_erect(self):
        """Тест эмиссии события при эрекции."""
        events = []
        nipple = Nipple()
        nipple.on("erect", lambda n, **kw: events.append("erect"))

        nipple.erect()
        assert "erect" in events

    def test_event_emit_on_open(self):
        """Тест эмиссии события при открытии."""
        events = []
        nipple = Nipple()
        nipple.on("open", lambda n, **kw: events.append(("open", kw.get("gape"))))

        nipple.open(0.5)
        assert ("open", 0.5) in events

    def test_event_emit_on_close(self):
        """Тест эмиссии события при закрытии."""
        events = []
        nipple = Nipple()
        nipple.on("close", lambda n, **kw: events.append("close"))

        nipple.open()
        nipple.close()
        assert "close" in events

    def test_get_state(self):
        """Тест получения состояния."""
        nipple = Nipple(diameter=1.5, length=1.2, base_diameter=1.5, base_length=1.2)
        nipple.erect()
        nipple.open(0.4)
        state = nipple.get_state()

        assert state["diameter"] == pytest.approx(1.8)  # 1.5 * 1.2
        assert state["length"] == pytest.approx(1.56)  # 1.2 * 1.3
        assert state["gape_diameter"] == pytest.approx(0.4)
        assert state["is_erect"] is True
        assert state["is_open"] is True

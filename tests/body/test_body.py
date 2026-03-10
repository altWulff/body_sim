# tests/body/test_body.py
import pytest
from unittest.mock import patch, MagicMock

from body_sim.body.body import Body, Sex
from body_sim.appearance.core import Race
from body_sim.anatomy.chest.cup_size import CupSize


# Параметризация рас и базовых размеров груди
RACE_BREAST_SIZES = {
    Race.HUMAN: CupSize.C,
    Race.HIGH_ELF: CupSize.B,
    Race.DARK_ELF: CupSize.C,
    Race.BEASTKIN: CupSize.C,
    Race.SUCCUBUS: CupSize.D,
    Race.INCUBUS: CupSize.D,  # Incub тоже может иметь грудь (футанари/гинекомастия)
    Race.DEMON: CupSize.D,
    Race.DRAGON: CupSize.D,    # Драконы крупные
    Race.DRAGONKIN: CupSize.C, # Дракониды поменьше
    Race.VAMPIRE: CupSize.C,   # Вампиры как люди
    Race.DEMI_HUMAN: CupSize.C # Полулюди как люди
}

# Расы, где клитор может трансформироваться (демоны и производные)
TRANSFORMABLE_RACES = {Race.DEMON, Race.SUCCUBUS, Race.INCUBUS, Race.DRAGON}


class TestBodyCreationBasic:
    """Базовые тесты создания тела."""

    def test_default_creation(self):
        """Тест дефолтного создания тела."""
        body = Body()
        
        assert body.name == "Unnamed"
        assert body.sex == Sex.FEMALE
        assert body.race == Race.HUMAN
        assert body.age == 25.0
        assert body.height == 170.0
        assert body.weight == 60.0
        assert body.event_bus is not None

    def test_custom_creation(self):
        """Тест создания с кастомными параметрами."""
        body = Body(
            name="Test Character",
            sex=Sex.MALE,
            race=Race.DEMON,
            age=150.0,
            height=180.0,
            weight=75.0
        )
        
        assert body.name == "Test Character"
        assert body.sex == Sex.MALE
        assert body.race == Race.DEMON
        assert body.age == 150.0

    def test_appearance_auto_created(self):
        """Тест что appearance создается автоматически."""
        body = Body(race=Race.HIGH_ELF, height=160.0, weight=50.0)
        
        assert body.appearance is not None
        assert body.appearance.config.race == Race.HIGH_ELF
        assert body.appearance.config.height_cm == 160.0


class TestRaceAndSexVariations:
    """Тесты всех рас со всеми полами."""

    @pytest.mark.parametrize("race", list(Race))
    def test_female_creation(self, race):
        """Тест создания женщины каждой расы."""
        body = Body(name=f"{race.value}_female", race=race, sex=Sex.FEMALE)
        
        assert body.race == race
        assert body.sex == Sex.FEMALE
        assert body.breasts is not None
        assert body.reproductive_system is not None
        assert len(body.reproductive_system.vaginas) > 0
        assert len(body.reproductive_system.uteri) > 0
        assert len(body.reproductive_system.clitorises) > 0
        # Проверка базового размера груди
        assert body.breasts.cup_size == RACE_BREAST_SIZES[race]

    @pytest.mark.parametrize("race", list(Race))
    def test_male_creation(self, race):
        """Тест создания мужчины каждой расы."""
        body = Body(name=f"{race.value}_male", race=race, sex=Sex.MALE)
        
        assert body.race == race
        assert body.sex == Sex.MALE
        # У мужчин нет груди (в текущей реализации)
        assert body.breasts is None
        assert body.reproductive_system is not None
        assert len(body.reproductive_system.penises) > 0
        assert len(body.reproductive_system.scrotums) > 0
        # У мужчин нет влагалища и матки
        assert len(body.reproductive_system.vaginas) == 0
        assert len(body.reproductive_system.uteri) == 0

    @pytest.mark.parametrize("race", list(Race))
    def test_futanari_creation(self, race):
        """Тест создания футанари каждой расы."""
        body = Body(name=f"{race.value}_futanari", race=race, sex=Sex.FUTANARI)
        
        assert body.race == race
        assert body.sex == Sex.FUTANARI
        # Футанари имеет всё
        assert body.breasts is not None
        assert len(body.reproductive_system.vaginas) > 0
        assert len(body.reproductive_system.uteri) > 0
        assert len(body.reproductive_system.penises) > 0
        assert len(body.reproductive_system.scrotums) > 0
        assert len(body.reproductive_system.clitorises) > 0
        assert body.breasts.cup_size == RACE_BREAST_SIZES[race]


class TestRaceSpecificTraits:
    """Тесты специфичных для рас особенностей."""

    def test_demon_clitoris_transformable(self):
        """Тест что демоны могут трансформировать клитор."""
        for sex in [Sex.FEMALE, Sex.FUTANARI]:
            body = Body(race=Race.DEMON, sex=sex)
            for clitoris in body.reproductive_system.clitorises:
                assert clitoris.can_transform is True

    def test_succubus_clitoris_transformable(self):
        """Тест что суккубы могут трансформировать клитор."""
        body = Body(race=Race.SUCCUBUS, sex=Sex.FEMALE)
        assert body.reproductive_system.clitorises[0].can_transform is True

    def test_incubus_clitoris_transformable(self):
        """Тест что инкубы (как мужские демоны) могут трансформировать."""
        # Инкуб как футанари (для теста трансформации нужен клитор)
        body = Body(race=Race.INCUBUS, sex=Sex.FUTANARI)
        assert any(c.can_transform for c in body.reproductive_system.clitorises)

    def test_dragon_clitoris_transformable(self):
        """Тест что драконы могут трансформировать клитор."""
        body = Body(race=Race.DRAGON, sex=Sex.FEMALE)
        assert body.reproductive_system.clitorises[0].can_transform is True

    @pytest.mark.parametrize("race", 
        [Race.HUMAN, Race.HIGH_ELF, Race.DARK_ELF, Race.BEASTKIN, 
         Race.VAMPIRE, Race.DEMI_HUMAN, Race.DRAGONKIN])
    def test_non_transformable_races(self, race):
        """Тест что остальные расы не могут трансформировать клитор."""
        body = Body(race=race, sex=Sex.FEMALE)
        assert body.reproductive_system.clitorises[0].can_transform is False

    def test_beastkin_breasts(self):
        """Тест особенностей зверолюдов."""
        body = Body(race=Race.BEASTKIN, sex=Sex.FEMALE)
        # Зверолюды могут иметь множественные соски (в будущем)
        assert body.breasts.cup_size == CupSize.C

    def test_dragonkin_vs_dragon(self):
        """Тест различий между драконом и драконидом."""
        dragon = Body(race=Race.DRAGON, sex=Sex.FEMALE)
        dragonkin = Body(race=Race.DRAGONKIN, sex=Sex.FEMALE)
        
        # У драконов больше грудь
        assert dragon.breasts.cup_size.value > dragonkin.breasts.cup_size.value
        # Только драконы могут трансформировать (если логика такая)
        assert dragon.reproductive_system.clitorises[0].can_transform is True
        assert dragonkin.reproductive_system.clitorises[0].can_transform is False

    def test_vampire_traits(self):
        """Тест особенностей вампиров."""
        body = Body(race=Race.VAMPIRE, sex=Sex.FEMALE)
        assert body.race == Race.VAMPIRE
        # Вампиры как люди по размеру
        assert body.breasts.cup_size == CupSize.C

    def test_demi_human_traits(self):
        """Тест полулюдей."""
        body = Body(race=Race.DEMI_HUMAN, sex=Sex.FEMALE)
        assert body.race == Race.DEMI_HUMAN
        assert body.breasts.cup_size == CupSize.C


class TestBreastSizeCalculation:
    """Тесты расчета размера груди с учетом BMI."""

    def test_bmi_overweight_all_races(self):
        """Тест увеличения груди при высоком BMI для всех рас."""
        for race in RACE_BREAST_SIZES.keys():
            # BMI = 31.25 (высокий)
            body = Body(race=race, sex=Sex.FEMALE, height=160.0, weight=80.0)
            base_size = RACE_BREAST_SIZES[race]
            # Должно увеличиться на 2 размера (но не больше максимума)
            assert body.breasts.cup_size.value >= base_size.value

    def test_bmi_underweight_all_races(self):
        """Тест уменьшения груди при низком BMI для всех рас."""
        for race in [Race.HUMAN, Race.HIGH_ELF, Race.DARK_ELF]:  # Только для теста с B/C
            # BMI = 17.3 (низкий)
            body = Body(race=race, sex=Sex.FEMALE, height=170.0, weight=50.0)
            base_size = RACE_BREAST_SIZES[race]
            # Должно уменьшиться на 1 размер (минимум AAA)
            if base_size != CupSize.AAA:
                assert body.breasts.cup_size.value <= base_size.value

    def test_bmi_normal_no_change(self):
        """Тест что нормальный BMI не меняет размер."""
        body = Body(race=Race.HUMAN, sex=Sex.FEMALE, height=170.0, weight=60.0)
        assert body.breasts.cup_size == CupSize.C

    def test_succubus_always_large(self):
        """Тест что суккубы всегда с большой грудью."""
        for weight in [40.0, 60.0, 100.0]:  # Разный вес
            body = Body(race=Race.SUCCUBUS, sex=Sex.FEMALE, 
                       height=170.0, weight=weight)
            # Даже при низком весе минимум D (или близко к нему)
            assert body.breasts.cup_size.value >= CupSize.D.value


class TestReproductiveSystemSetup:
    """Тесты настройки репродуктивной системы."""

    @pytest.mark.parametrize("race", list(Race))
    def test_female_has_full_set(self, race):
        """Тест что женщины всех рас имеют полный набор женских органов."""
        body = Body(race=race, sex=Sex.FEMALE)
        
        assert len(body.reproductive_system.vaginas) > 0
        assert len(body.reproductive_system.uteri) > 0
        assert len(body.reproductive_system.clitorises) > 0
        assert len(body.reproductive_system.penises) == 0
        assert len(body.reproductive_system.scrotums) == 0

    @pytest.mark.parametrize("race", list(Race))
    def test_male_has_full_set(self, race):
        """Тест что мужчины всех рас имеют полный набор мужских органов."""
        body = Body(race=race, sex=Sex.MALE)
        
        assert len(body.reproductive_system.penises) > 0
        assert len(body.reproductive_system.scrotums) > 0
        assert len(body.reproductive_system.vaginas) == 0
        assert len(body.reproductive_system.uteri) == 0

    @pytest.mark.parametrize("race", list(Race))
    def test_futanari_has_all_organs(self, race):
        """Тест что футанари всех рас имеют все органы."""
        body = Body(race=race, sex=Sex.FUTANARI)
        
        assert len(body.reproductive_system.vaginas) > 0
        assert len(body.reproductive_system.uteri) > 0
        assert len(body.reproductive_system.clitorises) > 0
        assert len(body.reproductive_system.penises) > 0
        assert len(body.reproductive_system.scrotums) > 0


class TestBodyMethods:
    """Тесты методов тела."""

    @pytest.mark.parametrize("race", [Race.HUMAN, Race.DEMON, Race.DRAGON])
    def test_stimulate_clitoris(self, race):
        """Тест стимуляции клитора у разных рас."""
        body = Body(race=race, sex=Sex.FEMALE)
        
        with patch.object(body.reproductive_system.clitorises[0], 'stimulate') as mock:
            body.stimulate("clitoris", index=0, intensity=0.5)
            mock.assert_called_once_with(0.5)

    @pytest.mark.parametrize("race", list(Race))
    def test_stimulate_penis(self, race):
        """Тест стимуляции пениса у разных рас."""
        body = Body(race=race, sex=Sex.MALE)
        
        with patch.object(body.reproductive_system.penises[0], 'stimulate') as mock:
            body.stimulate("penis", index=0, intensity=0.5)
            mock.assert_called_once_with(0.5)

    @pytest.mark.parametrize("race", [Race.HUMAN, Race.SUCCUBUS, Race.DRAGON])
    def test_stimulate_breasts(self, race):
        """Тест стимуляции груди у разных рас."""
        body = Body(race=race, sex=Sex.FEMALE)
        
        with patch.object(body.breasts, 'stimulate') as mock:
            body.stimulate("breast", index=0, intensity=0.5)
            mock.assert_called_once_with("left", 0.5)

    @pytest.mark.parametrize("race", TRANSFORMABLE_RACES)
    def test_transform_clitoris_success(self, race):
        """Тест успешной трансформации клитора у разных демонических рас."""
        body = Body(race=race, sex=Sex.FEMALE)
        initial_penis_count = len(body.reproductive_system.penises)
        
        result = body.transform_clitoris_to_penis(
            clitoris_idx=0,
            target_length=15.0,
            target_girth=10.0
        )
        
        assert result is True
        assert len(body.reproductive_system.penises) == initial_penis_count + 1

    @pytest.mark.parametrize("race", 
        [Race.HUMAN, Race.HIGH_ELF, Race.DARK_ELF, Race.BEASTKIN, 
         Race.VAMPIRE, Race.DEMI_HUMAN, Race.DRAGONKIN])
    def test_transform_clitoris_fails_for_non_demon(self, race):
        """Тест что трансформация не работает для не-демонов."""
        body = Body(race=race, sex=Sex.FEMALE)
        
        result = body.transform_clitoris_to_penis()
        assert result is False

    def test_transform_invalid_index(self):
        """Тест трансформации с неверным индексом."""
        body = Body(race=Race.DEMON, sex=Sex.FEMALE)
        
        result = body.transform_clitoris_to_penis(clitoris_idx=99)
        assert result is False

    @pytest.mark.parametrize("race", list(Race))
    def test_ejaculate_races(self, race):
        """Тест эякуляции у разных рас."""
        body = Body(race=race, sex=Sex.MALE)
        
        with patch.object(body.reproductive_system.penises[0], 'ejaculate', 
                         return_value={"success": True, "volume": 5.0}):
            result = body.ejaculate(penis_index=0)
            assert result["success"] is True

    @pytest.mark.parametrize("race", list(Race))
    def test_inflate_uterus_races(self, race):
        """Тест надувания матки у разных рас."""
        body = Body(race=race, sex=Sex.FEMALE)
        
        with patch.object(body.reproductive_system.uteri[0], 'inflate', 
                         return_value=True):
            result = body.inflate_uterus(uterus_idx=0, ratio=2.0)
            assert result is True


class TestBodyUpdate:
    """Тесты обновления состояния тела."""

    @pytest.mark.parametrize("sex", [Sex.FEMALE, Sex.MALE, Sex.FUTANARI])
    def test_update_all_sexes(self, sex):
        """Тест update для всех полов."""
        body = Body(sex=sex)
        
        with patch.object(body.digestive_system, 'update') as mock_digest:
            with patch.object(body.reproductive_system, 'update') as mock_reprod:
                body.update(delta_time=1.0)
                
                mock_digest.assert_called_once_with(1.0, body.event_bus)
                mock_reprod.assert_called_once_with(1.0, body.event_bus)
                
                if body.breasts:
                    with patch.object(body.breasts, 'update') as mock_breasts:
                        body.update(0.5)
                        mock_breasts.assert_called_once()


class TestBodyState:
    """Тесты получения состояния."""

    @pytest.mark.parametrize("race", list(Race))
    @pytest.mark.parametrize("sex", [Sex.FEMALE, Sex.MALE, Sex.FUTANARI])
    def test_get_full_state(self, race, sex):
        """Тест получения полного состояния для всех комбинаций."""
        body = Body(name=f"{race.value}_{sex.name}", race=race, sex=sex)
        
        state = body.get_full_state()
        
        assert state["name"] == f"{race.value}_{sex.name}"
        assert state["sex"] == sex.name
        assert state["race"] == race.value
        assert "appearance" in state
        assert "digestive" in state
        assert "reproductive" in state
        # breasts только для FEMALE и FUTANARI
        if sex in [Sex.FEMALE, Sex.FUTANARI]:
            assert state["breasts"] is not None
        else:
            assert state["breasts"] is None


# Фикстуры для удобства использования в других тестах
@pytest.fixture
def human_female():
    """Фикстура: человек-женщина."""
    return Body(name="Human", race=Race.HUMAN, sex=Sex.FEMALE)

@pytest.fixture
def demon_male():
    """Фикстура: демон-мужчина."""
    return Body(race=Race.DEMON, sex=Sex.MALE)

@pytest.fixture
def dragon_futanari():
    """Фикстура: дракон-футанари."""
    return Body(race=Race.DRAGON, sex=Sex.FUTANARI, height=200.0)

@pytest.fixture
def succubus():
    """Фикстура: суккуб."""
    return Body(race=Race.SUCCUBUS, sex=Sex.FEMALE)

@pytest.fixture
def vampire():
    """Фикстура: вампир."""
    return Body(race=Race.VAMPIRE, sex=Sex.FEMALE)

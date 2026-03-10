# tests/anatomy/chest/test_areola.py
import pytest
from unittest.mock import patch
from body_sim.anatomy.chest.areola import Areola, AreolaTexture, MontgomeryGland
from body_sim.anatomy.chest.nipple import Nipple

class TestMontgomeryGland:
    def test_default_creation(self):
        """Тест создания железы."""
        gland = MontgomeryGland()
        assert gland.size == 0.1
        assert gland.active is True
        assert gland.secretion == 0.0
    
    def test_custom_creation(self):
        """Тест кастомного создания."""
        gland = MontgomeryGland(size=0.2, active=False, secretion=0.5)
        assert gland.size == 0.2
        assert gland.active is False
        assert gland.secretion == 0.5

class TestAreola:
    def test_default_creation(self):
        """Тест дефолтного создания ареолы."""
        areola = Areola()
        assert areola.diameter == 4.0
        assert areola.color == "pink"
        assert areola.texture == AreolaTexture.BUMPY
        assert areola.puffiness == 0.0
        assert areola.sensitivity == 0.8
    
    def test_custom_creation(self):
        """Тест кастомного создания."""
        areola = Areola(
            diameter=5.0,
            color="brown",
            texture=AreolaTexture.PUFFY,
            puffiness=0.5,
            sensitivity=1.0
        )
        assert areola.diameter == 5.0
        assert areola.base_diameter == 5.0
        assert areola.color == "brown"
        assert areola.texture == AreolaTexture.PUFFY
    
    def test_auto_creates_nipples(self):
        """Тест автоматического создания сосков."""
        areola = Areola(diameter=4.0)
        assert len(areola.nipples) == 1
        assert areola.nipples[0].diameter == 1.0  # 25% от 4.0
    
    def test_auto_creates_montgomery_glands(self):
        """Тест автоматического создания желез."""
        with patch('random.randint', return_value=12):
            areola = Areola()
            assert len(areola.montgomery_glands) == 12
    
    def test_add_nipple(self):
        """Тест добавления соска."""
        areola = Areola()
        new_nipple = Nipple(diameter=0.5)
        
        initial_count = len(areola.nipples)
        areola.add_nipple(new_nipple)
        
        assert len(areola.nipples) == initial_count + 1
        assert new_nipple in areola.nipples
    
    def test_update_diameter(self):
        """Тест обновления диаметра при растяжении."""
        areola = Areola(diameter=4.0)
        areola._update_diameter(2.0)  # stretch_ratio = 2
        
        # Диаметр должен увеличиться как sqrt(2)
        import math
        expected = 4.0 * math.sqrt(2.0)
        assert abs(areola.diameter - expected) < 0.01
    
    def test_stimulate_bumpy_texture(self):
        """Тест стимуляции с шероховатой текстурой."""
        areola = Areola(texture=AreolaTexture.BUMPY)
        areola.stimulate(1.0)
        
        # Железы должны начать секрецию
        active_glands = [g for g in areola.montgomery_glands if g.secretion > 0]
        assert len(active_glands) > 0
    
    def test_stimulate_smooth_texture(self):
        """Тест стимуляции с гладкой текстурой."""
        areola = Areola(texture=AreolaTexture.SMOOTH)
        initial_secretions = [g.secretion for g in areola.montgomery_glands]
        
        areola.stimulate(1.0)
        
        # Секреция не должна измениться для гладкой текстуры
        for i, gland in enumerate(areola.montgomery_glands):
            assert gland.secretion == initial_secretions[i]
    
    def test_stimulate_nipples(self):
        """Тест что стимуляция передается соскам."""
        areola = Areola()
        nipple = areola.nipples[0]
        
        areola.stimulate(1.0)
        assert nipple.is_erect is True
    
    def test_relax(self):
        """Тест расслабления."""
        areola = Areola()
        nipple = areola.nipples[0]
        nipple.erect()
        
        areola.relax()
        assert nipple.is_erect is False
    
    def test_get_total_gape(self):
        """Тест суммарного отверстия."""
        areola = Areola()
        areola.nipples[0].open(0.5)
        
        # Добавим еще один сосок
        areola.add_nipple(Nipple(gape_diameter=0.3, is_open=True))
        
        assert areola.get_total_gape() == 0.8
    
    def test_get_state(self):
        """Тест получения состояния."""
        areola = Areola(diameter=5.0, color="dark")
        state = areola.get_state()
        
        assert state['diameter'] == 5.0
        assert state['base_diameter'] == 5.0
        assert state['color'] == "dark"
        assert state['texture'] == AreolaTexture.BUMPY.value
        assert state['nipple_count'] == 1
        assert 'nipples' in state
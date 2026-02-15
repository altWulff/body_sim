# body_sim/characters/deep_reactions.py
"""
Реакции персонажей на глубокое проникновение и пролапс.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from random import choice, random

@dataclass
class DeepPenetrationReaction:
    text: str
    emotion: str  # "pleasure", "pain", "panic", "shock"
    sound_effect: Optional[str] = None
    physical_effect: Optional[str] = None
    intensity: float = 0.5  # 0-1


class DeepReactionSystem:
    """Система реакций на глубокое проникновение."""
    
    REACTIONS = {
        "cervix_bump": [
            DeepPenetrationReaction(
                "Ах! Что-то уперлось в самую глубину... это шейка матки?",
                "surprise",
                "*глубокий вздох*",
                "cervix_strain",
                0.6
            ),
            DeepPenetrationReaction(
                "[name] вздрагивает всем телом от резкой боли внизу живота",
                "pain",
                "*стон*",
                "cervix_trauma",
                0.8
            ),
            DeepPenetrationReaction(
                "Больно! Слишком глубоко... шейка сжимается, пытаясь не пустить дальше",
                "pain",
                "*сжимает зубы*",
                "cervix_resistance",
                0.7
            ),
        ],
        
        "cervix_penetration": [
            DeepPenetrationReaction(
                "[name] кричит - член прорывается через шейку матки, растягивая её изнутри!",
                "agony",
                "*пронзительный крик*",
                "cervix_tearing",
                0.9
            ),
            DeepPenetrationReaction(
                "Нет... нет... он внутри матки... это невозможно...",
                "shock",
                "*дрожь*",
                "uterus_entry",
                1.0
            ),
        ],
        
        "uterus_filling": [
            DeepPenetrationReaction(
                "Тепло расползается внизу живота - сперма наполняет матку, давя на стенки",
                "pleasure_pain",
                "*тяжелое дыхание*",
                "uterus_distension",
                0.7
            ),
            DeepPenetrationReaction(
                "Матка растягивается, принимая всё глубже... чувствуется каждую каплю",
                "pleasure",
                "*стон*",
                "uterus_fullness",
                0.6
            ),
        ],
        
        "tube_entry": [
            DeepPenetrationReaction(
                "Ааа! Он залез в трубу... узкий канал сжимает член со всех сторон",
                "panic",
                "*вскрик*",
                "tube_dilation",
                0.8
            ),
            DeepPenetrationReaction(
                "Что-то идёт не туда... в сторону... это фаллопиева труба?!",
                "shock",
                "*паника*",
                "tube_stretch",
                0.9
            ),
        ],
        
        "ovary_contact": [
            DeepPenetrationReaction(
                "Удар по яичнику! [name] корчится от внезапной боли в боку",
                "agony",
                "*вой*",
                "ovary_trauma",
                1.0
            ),
            DeepPenetrationReaction(
                "Он достал до яичника... там... внутри...",
                "shock",
                "*дрожь*",
                "ovary_contact",
                0.8
            ),
        ],
        
        "ovary_eversion": [
            DeepPenetrationReaction(
                "[bold red]НЕТ! Яичник... он вытягивает яичник наружу! БОЛЬНО![/bold red]",
                "agony",
                "*пронзительный крик*",
                "ovary_prolapse",
                1.0
            ),
            DeepPenetrationReaction(
                "Что происходит... что-то выворачивается внутри... о боже, это видно снаружи?!",
                "panic_embarrassment",
                "*паника*",
                "ovary_exposed",
                1.0
            ),
        ],
        
        "uterine_prolapse": [
            DeepPenetrationReaction(
                "[bold red]МАТКА! Моя матка вываливается! ПОМОГИТЕ![/bold red]",
                "agony",
                "*крик ужаса*",
                "uterus_prolapse",
                1.0
            ),
            DeepPenetrationReaction(
                "Что-то огромное выходит вслед за членом... шейка... матка... она наружу!",
                "dissociation",
                "*истерика*",
                "complete_prolapse",
                1.0
            ),
        ],
        
        "urethra_penetration": [
            DeepPenetrationReaction(
                "Ты... ты в мочеиспускательном канале... это так больно...",
                "pain",
                "*вскрик*",
                "urethra_stretch",
                0.9
            ),
            DeepPenetrationReaction(
                "Горит... жжёт изнутри... канал слишком мал для этого",
                "agony",
                "*стон*",
                "urethra_tear",
                0.8
            ),
        ],
        
        "nipple_penetration": [
            DeepPenetrationReaction(
                "Сосок... внутри соска... что ты делаешь?!",
                "surprise",
                "*вздох*",
                "nipple_canal_entry",
                0.6
            ),
            DeepPenetrationReaction(
                "Чувствую как толкаешься прямо в молочный проток... странное ощущение...",
                "weird",
                "*напряжение*",
                "duct_fill",
                0.5
            ),
        ],
    }
    
    @classmethod
    def get_reaction(cls, event: str, name: str = "Она") -> DeepPenetrationReaction:
        """Получить случайную реакцию на событие."""
        reactions = cls.REACTIONS.get(event, [])
        if not reactions:
            return DeepPenetrationReaction("...", "neutral")
        
        reaction = choice(reactions)
        # Заменяем [name]
        text = reaction.text.replace("[name]", name)
        return DeepPenetrationReaction(
            text=text,
            emotion=reaction.emotion,
            sound_effect=reaction.sound_effect,
            physical_effect=reaction.physical_effect,
            intensity=reaction.intensity
        )
    
    @classmethod
    def process_deep_event(cls, body, event: str, intensity: float = 0.5) -> Optional[DeepPenetrationReaction]:
        """Обработать событие глубокого проникновения."""
        name = getattr(body, 'name', 'Она')
        reaction = cls.get_reaction(event, name)
        
        if random() < intensity:
            return reaction
        return None
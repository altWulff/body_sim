# body_sim/appearance/body_parts.py
"""
Внешность анатомических частей - рот, желудок (живот), анус.
Работает в связке с anatomy-классами.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum, auto
import random
from .enums import LipFullness, LipColor, BellyShape, BellyButtonType, AnusAppearanceType


@dataclass
class MouthAppearance:
    """
    Внешность рта.
    """
    # Губы
    lip_fullness: LipFullness = LipFullness.AVERAGE
    upper_lip_thickness: float = 0.8  # см
    lower_lip_thickness: float = 1.0  # см
    lip_color: LipColor = LipColor.PINK
    lip_softness: float = 0.7  # 0-1 (мягкость)
    
    # Растяжимость
    max_stretch_ratio: float = 3.0  # Макс растяжение губ
    stretch_marks: bool = False  # Растяжки от частого растягивания
    
    # Состояние (обновляется из anatomy)
    current_opening: float = 0.0  # Текущее открытие в см
    is_open: bool = False
    is_stretched: bool = False
    is_puffed: bool = False
    
    # Детали
    has_lip_piercing: bool = False
    lip_piercing_count: int = 0
    lipstick_applied: bool = False
    lipstick_color: Optional[str] = None
    
    def update_from_mouth(self, mouth_anatomy):
        """Обновить состояние из anatomy.Mouth."""
        if hasattr(mouth_anatomy, 'lips'):
            lips = mouth_anatomy.lips
            self.current_opening = lips.effective_opening if hasattr(lips, 'effective_opening') else 0
            self.is_open = lips.state != lips.__class__.__dict__.get('CLOSED', 0)
            self.is_stretched = lips.stretch_ratio > 1.5 if hasattr(lips, 'stretch_ratio') else False
            self.is_puffed = lips.puff_ratio > 1.3 if hasattr(lips, 'puff_ratio') else False
            
            # Растяжки при частом растягивании
            if hasattr(lips, 'fatigue') and lips.fatigue > 0.8:
                if random.random() < 0.1:
                    self.stretch_marks = True
    
    def get_description(self) -> str:
        """Текстовое описание."""
        parts = []
        
        # Полнота
        fullness_desc = {
            LipFullness.THIN: "thin lips",
            LipFullness.AVERAGE: "average lips",
            LipFullness.FULL: "full lips",
            LipFullness.VERY_FULL: "very full lips",
            LipFullness.INFLATED: "inflated lips"
        }
        parts.append(fullness_desc.get(self.lip_fullness, "lips"))
        
        # Цвет
        parts.append(f"{self.lip_color.value}")
        
        # Состояние
        if self.is_stretched:
            parts.append("stretched wide")
        elif self.is_open:
            parts.append("slightly open")
        
        if self.stretch_marks:
            parts.append("with stretch marks")
        
        return ", ".join(parts)


@dataclass
class BellyAppearance:
    """
    Внешность живота (визуальное отображение желудка).
    """
    base_shape: BellyShape = BellyShape.SLIM
    base_size: float = 0.0  # Выступание в см относительно плоского
    
    # Пупок
    belly_button: BellyButtonType = BellyButtonType.INNIE
    belly_button_depth: float = 1.5  # глубина/выпирание в см
    
    # Кожа живота
    skin_texture: str = "smooth"
    stretch_marks: List[str] = field(default_factory=list)  # Растяжки
    
    # Состояние (обновляется из anatomy)
    current_shape: BellyShape = BellyShape.SLIM
    current_size: float = 0.0  # Текущее выступание
    inflation_ratio: float = 1.0
    fill_ratio: float = 0.0
    
    # Детали
    has_piercing: bool = False
    is_tanned: bool = False
    muscle_definition: float = 0.0  # 0-1 (рельеф мышц)
    
    def update_from_stomach(self, stomach_anatomy):
        """Обновить состояние из anatomy.Stomach."""
        if not stomach_anatomy:
            return
        
        # Размер из инфляции и заполнения
        if hasattr(stomach_anatomy, 'inflation_ratio'):
            self.inflation_ratio = stomach_anatomy.inflation_ratio
        if hasattr(stomach_anatomy, 'fill_ratio'):
            self.fill_ratio = stomach_anatomy.fill_ratio
        
        # Вычисляем визуальный размер
        base = self.base_size
        if hasattr(stomach_anatomy, 'inflation_ratio'):
            base *= stomach_anatomy.inflation_ratio
        if hasattr(stomach_anatomy, 'fill_ratio'):
            base += stomach_anatomy.fill_ratio * 10  # +10см при полном заполнении
        
        self.current_size = base
        
        # Определяем форму
        if hasattr(stomach_anatomy, 'state'):
            state_name = stomach_anatomy.state.name if hasattr(stomach_anatomy.state, 'name') else str(stomach_anatomy.state)
            if 'RUPTURE' in state_name or 'HYPER' in state_name:
                self.current_shape = BellyShape.DISTENDED
            elif 'DISTENDED' in state_name or 'OVERSTUFFED' in state_name:
                self.current_shape = BellyShape.INFLATED
            elif 'FILLED' in state_name:
                self.current_shape = BellyShape.ROUNDED
            else:
                self.current_shape = self.base_shape
        
        # Растяжки при большом растяжении
        if self.inflation_ratio > 2.0 or self.fill_ratio > 0.8:
            if random.random() < 0.05 and "stretch_marks" not in self.stretch_marks:
                self.stretch_marks.append("stretch_marks")
    
    def get_description(self) -> str:
        """Описание живота."""
        parts = []
        
        # Форма
        shape_desc = {
            BellyShape.FLAT: "flat belly",
            BellyShape.SLIM: "slim belly",
            BellyShape.SOFT: "soft belly",
            BellyShape.ROUNDED: "rounded belly",
            BellyShape.POT: "pot belly",
            BellyShape.PREGNANT: "pregnant belly",
            BellyShape.INFLATED: "inflated belly",
            BellyShape.DISTENDED: "heavily distended belly",
            BellyShape.MUSCULAR: "muscular belly with abs"
        }
        
        current = shape_desc.get(self.current_shape, "belly")
        if self.current_shape != self.base_shape:
            current += f" (normally {shape_desc.get(self.base_shape, 'slim')})"
        parts.append(current)
        
        # Размер
        if self.current_size > 5:
            parts.append(f"protruding {self.current_size:.1f}cm")
        
        # Пупок
        if self.belly_button == BellyButtonType.OUTIE:
            parts.append("with outie belly button")
        elif self.belly_button == BellyButtonType.INNIE:
            parts.append("with innie belly button")
        
        # Растяжки
        if self.stretch_marks:
            parts.append(f"has {len(self.stretch_marks)} stretch marks")
        
        return ", ".join(parts)
    
    def get_visual_circumference(self) -> float:
        """Визуальный объем в см (для отображения)."""
        base = 60.0  # базовый обхват талии
        base += self.current_size * 2  # +2см на каждый см выступания
        return base * self.inflation_ratio


@dataclass
class AnusAppearance:
    """
    Внешность ануса.
    """
    base_type: AnusAppearanceType = AnusAppearanceType.NORMAL
    base_color: str = "pink"
    
    # Размеры
    base_diameter: float = 0.5  # см в норме
    max_visual_diameter: float = 2.0  # макс визуальный размер
    
    # Детали
    has_hair: bool = True  # Наличие волос
    hair_density: str = "sparse"  # sparse, normal, dense
    has_piercing: bool = False
    
    # Состояние (обновляется из anatomy)
    current_type: AnusAppearanceType = AnusAppearanceType.NORMAL
    current_diameter: float = 0.5
    is_gaping: bool = False
    gaping_size: float = 0.0
    prolapse_degree: float = 0.0
    
    # Растяжки/изменения
    is_permanently_loose: bool = False
    stretch_marks: bool = False
    discoloration: bool = False  # Изменение цвета от растяжения
    
    def update_from_anus(self, anus_anatomy):
        """Обновить состояние из anatomy.Anus."""
        if not anus_anatomy:
            return
        
        # Состояние
        if hasattr(anus_anatomy, 'is_gaping'):
            self.is_gaping = anus_anatomy.is_gaping
        if hasattr(anus_anatomy, 'gaping_size'):
            self.gaping_size = anus_anatomy.gaping_size
        if hasattr(anus_anatomy, 'current_diameter'):
            self.current_diameter = anus_anatomy.current_diameter
        
        # Пролапс
        if hasattr(anus_anatomy, 'prolapse_degree'):
            self.prolapse_degree = anus_anatomy.prolapse_degree
        
        # Определяем текущий тип
        if self.prolapse_degree > 0.5:
            self.current_type = AnusAppearanceType.PROLAPSED
        elif self.is_gaping and self.gaping_size > 3.0:
            self.current_type = AnusAppearanceType.GAPING
        elif hasattr(anus_anatomy, 'sphincter_tone') and anus_anatomy.sphincter_tone < 0.3:
            self.current_type = AnusAppearanceType.RELAXED
        elif self.stretch_marks or self.is_permanently_loose:
            self.current_type = AnusAppearanceType.STRETCHED
        else:
            self.current_type = self.base_type
        
        # Постоянные изменения
        if hasattr(anus_anatomy, 'canal'):
            canal = anus_anatomy.canal
            if hasattr(canal, 'stretch_ratio') and canal.stretch_ratio > 3.0:
                self.is_permanently_loose = True
            if hasattr(canal, 'fatigue') and canal.fatigue > 0.9:
                self.discoloration = True
    
    def get_description(self) -> str:
        """Описание ануса."""
        parts = []
        
        # Тип
        type_desc = {
            AnusAppearanceType.TIGHT: "tight",
            AnusAppearanceType.NORMAL: "normal",
            AnusAppearanceType.RELAXED: "relaxed",
            AnusAppearanceType.GAPING: "gaping open",
            AnusAppearanceType.PROLAPSED: "prolapsed",
            AnusAppearanceType.PUFFED: "puffed",
            AnusAppearanceType.STRETCHED: "permanently stretched"
        }
        
        desc = type_desc.get(self.current_type, "normal")
        if self.current_type != self.base_type:
            desc += f" (was {type_desc.get(self.base_type, 'normal')})"
        parts.append(desc)
        
        # Размер
        if self.current_diameter > self.base_diameter * 2:
            parts.append(f"{self.current_diameter:.1f}cm diameter")
        
        # Пролапс
        if self.prolapse_degree > 0:
            parts.append(f"prolapsed {self.prolapse_degree:.0%}")
        
        # Изменения
        if self.is_permanently_loose:
            parts.append("permanently loose")
        if self.discoloration:
            parts.append("discolored from use")
        if self.stretch_marks:
            parts.append("has stretch marks")
        
        return ", ".join(parts)


# ============ ИНТЕГРАЦИЯ В APPEARANCE ============

@dataclass
class FullBodyAppearance:
    """
    Полная внешность тела с анатомическими деталями.
    Расширяет стандартный Appearance.
    """
    # Стандартные (уже есть в AppearanceMixin)
    # eyes, ears, skin_color...
    
    # Новые части
    mouth: MouthAppearance = field(default_factory=MouthAppearance)
    belly: BellyAppearance = field(default_factory=BellyAppearance)
    anus: AnusAppearance = field(default_factory=AnusAppearance)
    
    def update_from_body(self, body):
        """Обновить всю внешность из Body."""
        # Рот
        if hasattr(body, 'mouth_system') and body.mouth_system:
            mouth = body.mouth_system.primary
            if mouth:
                self.mouth.update_from_mouth(mouth)
        
        # Живот (из желудка)
        if hasattr(body, 'stomach_system') and body.stomach_system:
            stomach = body.stomach_system.primary
            if stomach:
                self.belly.update_from_stomach(stomach)
        
        # Анус
        if hasattr(body, 'anuses') and body.anuses:
            anus = body.anuses[0]  # Первичный анус
            self.anus.update_from_anus(anus)
    
    def get_detailed_description(self) -> Dict[str, str]:
        """Полное описание всех частей."""
        return {
            "mouth": self.mouth.get_description(),
            "belly": self.belly.get_description(),
            "anus": self.anus.get_description()
        }

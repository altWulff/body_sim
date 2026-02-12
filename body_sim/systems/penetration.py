# body_sim/systems/penetration.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
from enum import Enum, auto
import math
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from body_sim.systems.fluid_container import FluidContainer
from body_sim.core.enums import FluidType, InsertionStatus


@dataclass
class InsertableObject:
    """Объект для вставки"""
    name: str
    length: float          # см
    diameter: float        # см
    rigidity: float = 0.8
    texture: str = "smooth"
    
    # Динамическое состояние
    inserted_depth: float = 0.0
    angle: float = 0.0
    
    @property
    def remaining_outside(self) -> float:
        return max(0, self.length - self.inserted_depth)
    
    @property
    def cross_section(self) -> float:
        return math.pi * (self.diameter / 2) ** 2


@dataclass
class PenetrationData:
    object: InsertableObject
    entry_time: float = 0.0
    total_friction: float = 0.0
    micro_trauma: float = 0.0
    is_vacuum_locked: bool = False
    
    def get_depth_percentage(self, canal_length: float) -> float:
        return (self.object.inserted_depth / canal_length) * 100


class PenetrableOrgan:
    """Mixin для органов, поддерживающих проникновение"""
    
    def __init__(self):
        self.canal_length: float = 10.0
        self.rest_diameter: float = 3.0
        self.max_stretch_ratio: float = 3.0
        self.muscle_tone: float = 0.5
        self.current_dilation: float = 0.0
        self.lubrication: float = 20.0
        
        self.inserted_objects: List[PenetrationData] = []
        self.total_inserted_volume: float = 0.0
        
    @property
    def occupied_depth(self) -> float:
        if not self.inserted_objects:
            return 0.0
        return max(obj.object.inserted_depth for obj in self.inserted_objects)
    
    @property
    def is_penetrated(self) -> bool:
        return len(self.inserted_objects) > 0
    
    def calculate_resistance(self, obj: InsertableObject, depth: float) -> float:
        size_ratio = obj.diameter / self.rest_diameter
        if size_ratio > self.max_stretch_ratio:
            return 100.0
            
        resistance = (size_ratio ** 2) * 30 * self.muscle_tone
        
        if depth > self.canal_length * 0.7:
            resistance *= 1.5
            
        resistance *= (1 - (self.lubrication / 200))
        return min(100, resistance)
    
    def check_insertion(self, obj: InsertableObject, force: float) -> Tuple[bool, str]:
        initial_resistance = self.calculate_resistance(obj, 0)
        
        if force < initial_resistance:
            return False, f"Слишком большое сопротивление ({initial_resistance:.0f}%)"
        
        if hasattr(self, 'current_volume') and hasattr(self, 'max_volume'):
            obj_volume = obj.cross_section * min(obj.length, self.canal_length)
            available = self.max_volume - self.current_volume
            
            if obj_volume > available * 1.2:
                return False, f"Недостаточно места (требуется {obj_volume:.0f}мл)"
        
        return True, "OK"
    
    def insert_object(self, obj: InsertableObject, force: float) -> Tuple[bool, str]:
        can_insert, msg = self.check_insertion(obj, force)
        if not can_insert:
            return False, msg
        
        initial_depth = min(2.0, obj.length * 0.1)
        resistance = self.calculate_resistance(obj, initial_depth)
        
        if force > resistance:
            obj.inserted_depth = initial_depth
            self.current_dilation = max(self.current_dilation, obj.diameter)
            
            data = PenetrationData(object=obj)
            self.inserted_objects.append(data)
            self._update_occupied_volume()
            self._handle_displacement(obj.cross_section * initial_depth)
            
            return True, f"{obj.name} вставлен на {initial_depth:.1f} см"
        else:
            return False, "Не удалось преодолеть входное сопротивление"
    
    def advance_object(self, obj_name: str, amount: float, force: float) -> Tuple[bool, str]:
        data = self._get_penetration_data(obj_name)
        if not data:
            return False, f"Объект {obj_name} не найден"
        
        obj = data.object
        current = obj.inserted_depth
        target = min(current + amount, self.canal_length)
        
        avg_resistance = (self.calculate_resistance(obj, current) + 
                         self.calculate_resistance(obj, target)) / 2
        
        if force < avg_resistance:
            actual_move = amount * (force / avg_resistance) * 0.5
            obj.inserted_depth += actual_move
            data.total_friction += force * 0.1
            self._update_occupied_volume()
            return False, f"Застопорено. Продвинуто на {actual_move:.1f} см (всего {obj.inserted_depth:.1f})"
        
        obj.inserted_depth = target
        data.total_friction += avg_resistance * 0.05
        
        if obj.inserted_depth >= self.canal_length:
            msg = f"{obj.name} полностью погружен"
            self._on_deep_penetration(data)
        else:
            msg = f"{obj.name} продвинут до {obj.inserted_depth:.1f} см"
        
        self._update_occupied_volume()
        self._handle_displacement(obj.cross_section * amount)
        return True, msg
    
    def withdraw_object(self, obj_name: str, amount: float, speed: float = 5.0) -> Tuple[bool, str]:
        data = self._get_penetration_data(obj_name)
        if not data:
            return False, f"Объект {obj_name} не найден"
        
        obj = data.object
        
        if hasattr(self, 'pressure') and self.pressure > 20 and speed > 8:
            data.is_vacuum_locked = True
            return False, "ВАКУУМНЫЙ ЗАХВАТ! Медленнее!"
        
        new_depth = max(0, obj.inserted_depth - amount)
        removed = obj.inserted_depth - new_depth
        obj.inserted_depth = new_depth
        
        if obj.inserted_depth <= 0:
            self.inserted_objects.remove(data)
            self._update_occupied_volume()
            return True, f"{obj.name} полностью извлечен"
        
        self._update_occupied_volume()
        return True, f"{obj.name} извлечен на {removed:.1f} см"
    
    def _get_penetration_data(self, name: str) -> Optional[PenetrationData]:
        for data in self.inserted_objects:
            if data.object.name == name:
                return data
        return None
    
    def _update_occupied_volume(self):
        total = 0.0
        for data in self.inserted_objects:
            obj = data.object
            volume = obj.cross_section * obj.inserted_depth
            total += volume
        self.total_inserted_volume = total
    
    def _handle_displacement(self, displaced_volume: float):
        if hasattr(self, 'add_pressure'):
            pressure_increase = displaced_volume * 0.5
            self.add_pressure(pressure_increase)
        
        if hasattr(self, 'fluid_volume'):
            if self.fluid_volume > 0:
                leak = min(displaced_volume * 0.8, self.fluid_volume)
                self.fluid_volume -= leak
                if hasattr(self, 'leakage'):
                    self.leakage += leak
    
    def _on_deep_penetration(self, data: PenetrationData):
        if hasattr(self, 'on_deep_penetration'):
            self.on_deep_penetration(data)
    
    def get_penetration_status(self) -> Table:
        table = Table(title=f"Penetration: {self.__class__.__name__}")
        table.add_column("Object", style="cyan")
        table.add_column("Depth", style="green")
        table.add_column("Diam", style="yellow")
        table.add_column("Status", style="red")
        
        if not self.inserted_objects:
            table.add_row("—", "—", "—", "Empty")
            return table
        
        for data in self.inserted_objects:
            obj = data.object
            pct = (obj.inserted_depth / self.canal_length) * 100
            status = "Deep" if pct > 80 else "Partial"
            if data.is_vacuum_locked:
                status = "[bold red]VACUUM LOCK[/]"
            
            table.add_row(
                obj.name,
                f"{obj.inserted_depth:.1f}/{self.canal_length}cm ({pct:.0f}%)",
                f"{obj.diameter:.1f}cm",
                status
            )
        return table

# ==================== CROSS-BODY PENETRATION ====================

@dataclass
class SemenProperties:
    volume: float
    viscosity: float = 3.0
    sperm_count: float = 100.0
    source_name: str = "unknown"
    fluid_type: str = "semen"
    
    def to_fluid_dict(self) -> Dict:
        return {
            "type": self.fluid_type,
            "volume": self.volume,
            "viscosity": self.viscosity,
            "sperm_count": self.sperm_count,
            "source": self.source_name,
            "sticky": True
        }


@dataclass
class EjaculationResult:
    success: bool
    volume: float = 0.0
    target_organ: str = ""
    depth: float = 0.0
    is_knotted: bool = False
    remaining_volume: float = 0.0
    message: str = ""


class IndexedOrganRef:
    """Ссылка на орган по типу и индексу"""
    
    # Словарь неправильных форм множественного числа
    PLURAL_EXCEPTIONS = {
        "penis": "penises",  # penis -> penises, не peniss
        "anus": "anuses",    # anus -> anuses
        "vagina": "vaginas", # vagina -> vaginas
    }
    
    def __init__(self, organ_type: str, index: int):
        self.organ_type = organ_type  # "penis", "vagina", "anus"
        self.index = index
        # Правильное формирование множественного числа
        self.plural_name = self.PLURAL_EXCEPTIONS.get(organ_type, organ_type + "s")
        self.full_name = f"{self.plural_name}[{index}]"  # penises[0], vaginas[0]
    
    def __str__(self):
        return self.full_name


class CrossBodyPenetration:
    """
    Управление половым актом с поддержкой множественных органов.
    Source: penises[index], Target: vaginas[index]/anuses[index]
    """
    
    def __init__(self, source_body: Any, target_body: Any, 
                 source_ref: IndexedOrganRef, target_ref: IndexedOrganRef):
        
        self.source = source_body
        self.target = target_body
        self.source_ref = source_ref
        self.target_ref = target_ref
        
        self.active = False
        self.penetration_data = None
        self.insertable_penis = None
        
        # Получаем пенис (источник)
        self.penis = self._get_organ_from_body(source_body, source_ref)
        if not self.penis:
            raise ValueError(f"У {source_body.name} нет {source_ref.full_name}")
            
        # Получаем целевой орган
        self.target_organ = self._get_organ_from_body(target_body, target_ref)
        if not self.target_organ:
            # Детальная диагностика для цели
            plural = target_ref.organ_type + "s"
            if hasattr(target_body, plural):
                val = getattr(target_body, plural)
                if isinstance(val, list) and len(val) == 0:
                    raise ValueError(
                        f"У {target_body.name} нет {target_ref.full_name} - "
                        f"список {plural} существует, но ПУСТОЙ. "
                        f"Возможно, персонаж создан без этого органа."
                    )
            
            raise ValueError(f"У {target_body.name} нет {target_ref.full_name}")
    
    def _get_organ_from_body(self, body: Any, ref: IndexedOrganRef) -> Optional[Any]:
        """Получить орган из тела по ссылке с индексом"""
        plural_dict = {
            "penis": "penises",
            "vagina": "vaginas",
            "anus": "anus"
        }
        plural_name = plural_dict[ref.organ_type]
        
        # Проверяем наличие списка (penises, vaginas, anuses)
        if hasattr(body, plural_name):
            organs_list = getattr(body, plural_name)
            
            if organs_list is not None and hasattr(organs_list, '__getitem__'):
                length = len(organs_list) if hasattr(organs_list, '__len__') else '?'
                
                if length == 0:
                    print(f"DEBUG: {plural_name} exists but is EMPTY (length 0)")
                    return None
                    
                if ref.index < length:
                    organ = organs_list[ref.index]
                    if organ is not None:
                        return organ
                    else:
                        print(f"DEBUG: {plural_name}[{ref.index}] is None")
                else:
                    print(f"DEBUG: index {ref.index} out of range for {plural_name} (length {length})")
        
        # Fallback на singular
        if hasattr(body, ref.organ_type) and ref.index == 0:
            return getattr(body, ref.organ_type)
        
        return None
    
    def start(self, force: float = 50.0) -> Tuple[bool, str]:
        """Начать проникновение"""
        # Проверка эрекции
        if hasattr(self.penis, 'is_erect') and not self.penis.is_erect:
            return False, "Член не эрегирован"
        
        # Проверка что пенис не уже используется
        if hasattr(self.penis, 'is_inserted') and self.penis.is_inserted:
            return False, "Этот пенис уже используется"
        
        # Проверка что вагина не занята
        if hasattr(self.target_organ, 'is_penetrated') and self.target_organ.is_penetrated:
            return False, "Этот орган уже занят другим пенисом"
        
        # Создаем InsertableObject из Penis
        self.insertable_penis = InsertableObject(
            name=f"penis_{self.source.name}_{self.source_ref.index}",
            length=getattr(self.penis, 'current_length', self.penis.base_length),
            diameter=getattr(self.penis, 'current_diameter', self.penis.base_girth / 3.14),
            rigidity=0.95 if getattr(self.penis, 'is_erect', True) else 0.5,
            texture="skin"
        )
        
        # ИСПРАВЛЕНИЕ: insert_object (без 's') - это метод, не атрибут
        success, msg = self.target_organ.insert_object(self.insertable_penis, force)
        
        if success:
            self.active = True
            # Помечаем пенис как используемый
            if hasattr(self.penis, 'is_inserted'):
                self.penis.is_inserted = True
            if hasattr(self.penis, 'state'):
                self.penis.state = "inserted"
            return True, msg
        else:
            return False, msg
    
    def thrust(self, amount: float, force: float = 60.0) -> Tuple[bool, str]:
        """Толчок"""
        if not self.active or not self.insertable_penis:
            return False, "Нет активного проникновения"
        
        obj_name = self.insertable_penis.name
        
        if amount > 0:
            # Вглубь
            success, msg = self.target_organ.advance_object(obj_name, amount, force)
            
            # Стимуляция
            friction = abs(amount) * 0.2
            if hasattr(self.penis, 'stimulate'):
                self.penis.stimulate(friction)
            if hasattr(self.target_organ, 'stimulate'):
                self.target_organ.stimulate(friction * 0.5)
            
            # Проверка узла
            if (hasattr(self.penis, 'has_knot') and self.penis.has_knot and 
                self.insertable_penis.inserted_depth >= self.target_organ.canal_length * 0.8):
                if not getattr(self.penis, 'is_knotted', False):
                    if self.penis.knot_girth > self.target_organ.current_dilation:
                        self.penis.is_knotted = True
                        return True, f"{msg}\n[УЗЕЛ ЗАФИКСИРОВАН]"
        else:
            # Наружу
            if getattr(self.penis, 'is_knotted', False):
                return False, "УЗЕЛ УДЕРЖИВАЕТ! Нельзя выйти."
            
            speed = abs(amount) * 2
            success, msg = self.target_organ.withdraw_object(obj_name, abs(amount), speed)
            
            if self.insertable_penis.inserted_depth <= 0:
                self.active = False
                self.penis.is_knotted = False
                if hasattr(self.penis, 'is_inserted'):
                    self.penis.is_inserted = False
                
        return success, msg

    def ejaculate(self) -> EjaculationResult:
        if not self.active:
            return EjaculationResult(False, message="Нет проникновения")
        
        cum_volume = getattr(self.penis, 'current_cum_volume', 0)
        if cum_volume <= 0:
            return EjaculationResult(False, message="Нет спермы")
        
        current_depth = self.insertable_penis.inserted_depth
        
        # Расходуем сперму
        if hasattr(self.penis, 'ejaculate'):
            volume = self.penis.ejaculate(cum_volume)
        else:
            volume = cum_volume
            self.penis.current_cum_volume = 0
        
        # Добавляем через единый интерфейс (использует FluidMixture внутри)
        if hasattr(self.target_organ, 'add_fluid'):
            added = self.target_organ.add_fluid(volume, "cum", {
                "source": getattr(self.source, 'name', 'unknown'),
                "depth": current_depth
            })
            
            if added < volume:
                overflow = volume - added
                console.print(f"[yellow]⚠ {overflow:.1f}ml спермы вытекает наружу![/yellow]")
        
        # Спад эрекции
        if hasattr(self.penis, 'arousal'):
            self.penis.arousal = max(0.2, self.penis.arousal - 0.6)
        if hasattr(self.penis, 'is_erect'):
            self.penis.is_erect = False
        
        fill_pct = 0
        if hasattr(self.target_organ, 'fluid_system'):
            fill_pct = self.target_organ.fluid_system.fill_percentage
        
        return EjaculationResult(
            success=True,
            volume=volume,
            target_organ=self.target_ref.full_name,
            depth=current_depth,
            is_knotted=getattr(self.penis, 'is_knotted', False),
            remaining_volume=getattr(self.penis, 'current_cum_volume', 0),
            message=f"Эякуляция {volume:.1f}ml ({fill_pct:.1f}% заполнения)"
        )

    def pullout(self) -> Tuple[bool, str]:
        """Извлечение"""
        if not self.active:
            return False, "Нечего извлекать"
        
        # Проверка узла
        if getattr(self.penis, 'is_knotted', False):
            arousal = getattr(self.penis, 'arousal', 0)
            if arousal > 0.3:
                return False, f"Узел зафиксирован (возбуждение: {arousal:.0%})"
            self.penis.is_knotted = False
        
        # Вакуум
        if hasattr(self.target_organ, 'pressure') and self.target_organ.pressure > 30:
            return False, "Вакуум удерживает!"
        
        # Извлечение
        while self.insertable_penis and self.insertable_penis.inserted_depth > 0:
            self.target_organ.withdraw_object(self.insertable_penis.name, 5.0, 2.0)
        
        self.active = False
        self.penis.is_knotted = False
        if hasattr(self.penis, 'is_inserted'):
            self.penis.is_inserted = False
        if hasattr(self.penis, 'state'):
            self.penis.state = "flaccid"
        
        return True, "Извлечение завершено"
    
    def get_status(self) -> Dict:
        """Статус"""
        if not self.active:
            return {"active": False}
        
        depth_pct = 0
        if self.insertable_penis and self.target_organ.canal_length > 0:
            depth_pct = (self.insertable_penis.inserted_depth / self.target_organ.canal_length) * 100
        
        return {
            "active": True,
            "source": f"{self.source.name}.{self.source_ref.full_name}",
            "target": f"{self.target.name}.{self.target_ref.full_name}",
            "depth": self.insertable_penis.inserted_depth if self.insertable_penis else 0,
            "max_depth": self.target_organ.canal_length,
            "depth_percent": depth_pct,
            "arousal": getattr(self.penis, 'arousal', 0),
            "knotted": getattr(self.penis, 'is_knotted', False),
            "cum_ready": getattr(self.penis, 'current_cum_volume', 0)
        }
class PenetrableWithFluid(PenetrableOrgan):
    def __init__(self):
        super().__init__()
        self.fluid_system = FluidContainer(base_volume=120.0, max_stretch_ratio=5.0)
        # Сохраняем базовые размеры для пересчета при инфляции
        self._base_canal_length = self.canal_length
        self._base_rest_diameter = self.rest_diameter
        
    def inflate(self, ratio: float) -> bool:
        """Инфляция с обновлением физических размеров"""
        success = self.fluid_system.inflate(ratio)
        if success:
            self._apply_inflation_to_dimensions()
        return success
    
    def _apply_inflation_to_dimensions(self):
        """Применить масштабирование размеров на основе инфляции"""
        # inflation_ratio - множитель объема
        # для сохранения пропорций: V2/V1 = (L2/L1)^3
        # значит L2/L1 = (V2/V1)^(1/3)
        volume_ratio = self.fluid_system.inflation_ratio
        linear_scale = volume_ratio ** (1/3)
        
        self.canal_length = self._base_canal_length * linear_scale
        self.rest_diameter = self._base_rest_diameter * linear_scale
        
    def deflate(self, recovery_rate: float = 0.1):
        """Уменьшение инфляции с восстановлением размеров"""
        old_ratio = self.fluid_system.inflation_ratio
        self.fluid_system.deflate(recovery_rate)
        # Если ratio изменился, обновляем размеры
        if self.fluid_system.inflation_ratio != old_ratio:
            self._apply_inflation_to_dimensions()
        
    def tick(self, dt: float = 1.0):
        super().tick(dt)
        old_ratio = self.fluid_system.inflation_ratio
        self.fluid_system.tick(dt)
        # Автоматическое восстановление размеров при спаде инфляции
        if self.fluid_system.inflation_ratio != old_ratio:
            self._apply_inflation_to_dimensions()
        
    # Свойства для совместимости
    @property
    def fluid_volume(self) -> float:
        return self.fluid_system.filled
        
    @property
    def max_volume(self) -> float:
        return self.fluid_system.max_volume
        
    @property
    def pressure(self) -> float:
        return self.fluid_system.pressure
        
    # Единый интерфейс как у uterus
    def add_fluid(self, volume: float, fluid_type: str = "water", properties: dict = None) -> float:
        try:
            ft = FluidType[fluid_type.upper()]
        except KeyError:
            ft = FluidType.WATER
        return self.fluid_system.add_fluid(ft, volume)
        
    def drain_all(self) -> Dict[str, float]:
        removed = self.fluid_system.drain_all()
        return {k.name: v for k, v in removed.items()}
        
    def remove_fluid(self, amount: float) -> float:
        return self.fluid_system.remove_fluid(amount)


        
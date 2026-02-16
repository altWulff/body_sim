# body_sim/systems/ejaculation.py
"""
Система эякуляции с заполнением конкретных зон.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from enum import Enum, auto
from dataclasses import dataclass

if TYPE_CHECKING:
    from body_sim.anatomy.genitals import Penis
    from body_sim.anatomy.uterus import Uterus, FallopianTube, Ovary
    from body_sim.anatomy.breast import Breast
    from body_sim.systems.advanced_penetration import AdvancedPenetrationEncounter, PenetrationDepthZone

class EjaculationZone(Enum):
    """Зоны для эякуляции."""
    VAGINA_CANAL = auto()      # Во влагалище
    CERVIX = auto()            # В шейку матки
    UTERUS_CAVITY = auto()     # В полость матки
    FALLOPIAN_TUBE = auto()    # В фаллопиеву трубу
    OVARY = auto()             # В яичник
    BREAST_MILK_DUCT = auto()  # В молочный проток (через сосок)
    URETHRA = auto()           # В уретру цели
    ANAL_CANAL = auto()        # В анальный канал
    RECTUM = auto()            # В прямую кишку


@dataclass
class EjaculationResult:
    """Результат эякуляции."""
    success: bool
    volume_ejaculated: float
    volume_absorbed: float
    volume_overflow: float
    zone: 'EjaculationZone'
    target_organ: Optional[Any]
    fluid_type: Any  # FluidType
    pulses: int
    messages: list[str]
    special_effect: Optional[str] = None
    
    def get_summary(self) -> str:
        """Краткое описание результата."""
        if not self.success:
            return f"Эякуляция не удалась: {self.messages[0] if self.messages else 'Unknown error'}"
        
        msg = f"Эякуляция в {self.zone.name}: {self.volume_ejaculated:.1f}мл"
        if self.volume_overflow > 0:
            msg += f" (переполнение: {self.volume_overflow:.1f}мл)"
        return msg


class ZoneFluidReceiver:
    """Обработчик приема жидкости в различные зоны."""

    @staticmethod
    def receive_fluid(
        zone: EjaculationZone, target: Any, fluid_type: Any, amount: float, source: Any) -> tuple[float, float, list[str]]:
        """
        Передать жидкость в целевую зону.
        """
        messages: list[str] = []
        absorbed = 0.0
        overflow = amount  # По умолчанию всё переполнение
        
        try:
            if zone == EjaculationZone.VAGINA_CANAL:
                absorbed, overflow = ZoneFluidReceiver._receive_in_vagina(
                    target, fluid_type, amount, source
                )
                
            elif zone == EjaculationZone.CERVIX:
                absorbed, overflow = ZoneFluidReceiver._receive_in_cervix(
                    target, fluid_type, amount
                )
                
            elif zone == EjaculationZone.UTERUS_CAVITY:
                absorbed, overflow = ZoneFluidReceiver._receive_in_uterus(
                    target, fluid_type, amount
                )
                
            elif zone == EjaculationZone.FALLOPIAN_TUBE:
                absorbed, overflow = ZoneFluidReceiver._receive_in_tube(
                    target, fluid_type, amount
                )
                
            elif zone == EjaculationZone.OVARY:
                absorbed, overflow = ZoneFluidReceiver._receive_in_ovary(
                    target, fluid_type, amount
                )
                
            elif zone == EjaculationZone.BREAST_MILK_DUCT:
                absorbed, overflow = ZoneFluidReceiver._receive_in_breast(
                    target, fluid_type, amount, source
                )
                
            elif zone in (EjaculationZone.ANAL_CANAL, EjaculationZone.RECTUM):
                absorbed, overflow = ZoneFluidReceiver._receive_in_anus(
                    target, fluid_type, amount
                )
                
            elif zone == EjaculationZone.URETHRA:
                absorbed, overflow = ZoneFluidReceiver._receive_in_urethra(
                    target, fluid_type, amount
                )
                
            else:
                messages.append(f"Неизвестная зона: {zone}")
                overflow = amount
                
        except Exception as e:
            messages.append(f"Ошибка приема жидкости: {str(e)}")
            overflow = amount
            
        return absorbed, overflow, messages

    
    @staticmethod
    def _receive_in_vagina(vagina: Any, fluid_type: Any, amount: float, 
                          source: Any) -> tuple[float, float]:
        """Прием в влагалище."""
        if not hasattr(vagina, 'add_fluid'):
            # Fallback для старых версий
            return ZoneFluidReceiver._generic_receive(vagina, fluid_type, amount)
        
        # Вагина может растягиваться, но есть лимит
        old_filled = getattr(vagina, 'current_fluid_volume', 0)
        max_cap = getattr(vagina, 'max_fluid_capacity', 
                         getattr(vagina, 'volume', 100.0))
        
        # Проверяем доступный объем
        available = max_cap - old_filled
        
        if available <= 0:
            return 0.0, amount
        
        to_add = min(amount, available)
        
        # Добавляем жидкость
        if hasattr(vagina, 'add_fluid'):
            actual = vagina.add_fluid(fluid_type, to_add)
        else:
            actual = to_add
            # Увеличиваем заполнение
            if hasattr(vagina, 'current_fluid_volume'):
                vagina.current_fluid_volume += actual
        
        overflow = amount - actual
        
        # Автоматическая передача в матку если вагина переполнена и шейка открыта
        if overflow > 0 and hasattr(vagina, 'cervix') and vagina.cervix.is_open:
            # Ищем связанную матку
            uterus = None
            if hasattr(vagina, 'connected_uterus') and vagina.connected_uterus:
                uterus = vagina.connected_uterus
            elif hasattr(vagina, 'uterus') and vagina.uterus:
                uterus = vagina.uterus
            
            if uterus:
                uterus_abs, uterus_overflow = ZoneFluidReceiver._receive_in_uterus(
                    uterus, fluid_type, overflow
                )
                actual += uterus_abs
                overflow = uterus_overflow
        
        return actual, overflow
    
    @staticmethod
    def _receive_in_cervix(cervix: Any, fluid_type: Any, amount: float) -> tuple[float, float]:
        """Прием в шейку матки."""
        # Шейка - узкий канал, пропускает часть жидкости сразу в матку
        uterus = None
        if hasattr(cervix, 'vaginal_connection') and cervix.vaginal_connection:
            uterus = cervix.vaginal_connection
        elif hasattr(cervix, 'uterus') and cervix.uterus:
            uterus = cervix.uterus
            
        if uterus and cervix.is_open:
            # Если шейка открыта - 90% идет в матку
            return ZoneFluidReceiver._receive_in_uterus(
                uterus, fluid_type, amount * 0.9
            )
        else:
            # Закрытая шейка задерживает жидкость
            capacity = getattr(cervix, 'volume', 5.0)
            current = getattr(cervix, 'current_volume', 0)
            available = capacity - current
            
            absorbed = min(amount, available)
            overflow = amount - absorbed
            
            if hasattr(cervix, 'add_fluid'):
                cervix.add_fluid(fluid_type, absorbed)
            elif hasattr(cervix, 'current_volume'):
                cervix.current_volume += absorbed
            
            # Давление может открыть шейку
            if overflow > 0 and hasattr(cervix, 'dilate'):
                cervix.dilate(overflow * 0.1)
                
                # После раскрытия - остаток в матку
                if cervix.is_open and uterus:
                    uterus_abs, _ = ZoneFluidReceiver._receive_in_uterus(
                        uterus, fluid_type, overflow
                    )
                    absorbed += uterus_abs
                    overflow = amount - absorbed
            
            return absorbed, overflow
        
        return amount, 0.0
    
    @staticmethod
    def _receive_in_uterus(uterus: Any, fluid_type: Any, amount: float) -> tuple[float, float]:
        """Прием в матку с распределением по трубам."""
        if not hasattr(uterus, 'add_fluid'):
            return 0.0, amount
        
        # Используем существующий метод add_fluid матки
        added = uterus.add_fluid(fluid_type, amount)
        
        # Проверяем переполнение
        total_filled = uterus.filled if hasattr(uterus, 'filled') else added
        max_vol = uterus.current_volume if hasattr(uterus, 'current_volume') else float('inf')
        
        overflow = max(0.0, amount - added)
        
        # Если есть переполнение и матка вывернута - жидкость вытекает наружу
        if overflow > 0 and hasattr(uterus, 'is_everted') and uterus.is_everted:
            # При выворачивании жидкость теряется
            pass
        
        return added, overflow
    
    @staticmethod
    def _receive_in_tube(tube: Any, fluid_type: Any, amount: float) -> tuple[float, float]:
        """Прием в фаллопиеву трубу."""
        if not hasattr(tube, 'add_fluid'):
            return 0.0, amount
        
        available = tube.max_fluid_capacity - tube.contained_fluid
        to_add = min(amount, available)
        
        if to_add > 0:
            tube.add_fluid(to_add, fluid_type)
        
        # Автоматическая передача в яичник если труба заполнена
        if to_add > 0 and hasattr(tube, 'transfer_to_ovary'):
            overflow_from_tube = tube.contained_fluid - tube.max_fluid_capacity * 0.8
            if overflow_from_tube > 0:
                tube.transfer_to_ovary(overflow_from_tube, fluid_type)
        
        return to_add, amount - to_add
    
    @staticmethod
    def _receive_in_ovary(ovary: Any, fluid_type: Any, amount: float) -> tuple[float, float]:
        """Прием в яичник."""
        if not hasattr(ovary, 'add_fluid'):
            return 0.0, amount
        
        added = ovary.add_fluid(fluid_type, amount)
        return added, amount - added
    
    @staticmethod
    def _receive_in_breast(breast: Any, fluid_type: Any, amount: float,
                          source: Any) -> tuple[float, float]:
        """Прием в грудь через молочные протоки."""
        if not hasattr(breast, 'add_fluid'):
            return 0.0, amount
        
        # Проверяем открытие сосков
        if hasattr(breast, 'areola') and breast.areola.nipples:
            nipples = breast.areola.nipples
            open_nipples = [n for n in nipples if getattr(n, 'is_open', False)]
            
            if not open_nipples:
                # Соски закрыты - высокое давление, может открыть
                for nipple in nipples:
                    if hasattr(nipple, 'open_from_pressure'):
                        nipple.open_from_pressure(3.0, max_pressure=3.0)
                open_nipples = [n for n in nipples if getattr(n, 'is_open', False)]
            
            if not open_nipples:
                return 0.0, amount  # Не удалось открыть
        
        added = breast.add_fluid(fluid_type, amount)
        return added, amount - added
    
    @staticmethod
    def _receive_in_anus(anus: Any, fluid_type: Any, amount: float) -> tuple[float, float]:
        """Прием в анус."""
        if hasattr(anus, 'add_fluid'):
            return ZoneFluidReceiver._generic_receive(anus, fluid_type, amount)
        
        # Fallback
        capacity = getattr(anus, 'volume', 200.0)
        current = getattr(anus, 'current_fill', 0)
        available = capacity - current
        
        absorbed = min(amount, available)
        
        if hasattr(anus, 'current_fill'):
            anus.current_fill += absorbed
        
        return absorbed, amount - absorbed
    
    @staticmethod
    def _receive_in_urethra(urethra: Any, fluid_type: Any, amount: float) -> tuple[float, float]:
        """Прием в уретру."""
        capacity = getattr(urethra, 'capacity', 10.0)
        current = getattr(urethra, 'filled', 0)
        available = capacity - current
        
        absorbed = min(amount, available)
        
        if hasattr(urethra, 'add_fluid'):
            urethra.add_fluid(fluid_type, absorbed)
        elif hasattr(urethra, 'filled'):
            urethra.filled += absorbed
        
        return absorbed, amount - absorbed
    
    @staticmethod
    def _generic_receive(obj: Any, fluid_type: Any, amount: float) -> tuple[float, float]:
        """Универсальный метод приема."""
        if hasattr(obj, 'add_fluid'):
            old = getattr(obj, 'filled', 0)
            obj.add_fluid(fluid_type, amount)
            new = getattr(obj, 'filled', old + amount)
            actual = new - old
            return actual, amount - actual
        
        if hasattr(obj, 'filled') and hasattr(obj, 'max_volume'):
            available = obj.max_volume - obj.filled
            actual = min(amount, available)
            obj.filled += actual
            return actual, amount - actual
        
        return 0.0, amount


class EjaculationController:
    """Контроллер эякуляции для сессии проникновения."""
    
    def __init__(self, encounter: 'AdvancedPenetrationEncounter'):
        self.encounter = encounter
        self.total_ejaculated = 0.0
        self.ejaculation_history: list[Dict[str, Any]] = []
    def determine_zone(self) -> tuple['EjaculationZone', Any]:
        """
        Определить текущую зону проникновения и целевой орган.
        """
        state = self.encounter.state
        target_body = getattr(self.encounter, 'target_body', None)
        
        # Проверяем сначала флаги глубокого проникновения
        if getattr(state, 'is_at_ovary', False):
            ovary = getattr(self.encounter, 'ovary_ref', None)
            if ovary:
                return EjaculationZone.OVARY, ovary
            # Fallback: ищем в target_body
            if target_body and hasattr(target_body, 'uterus'):
                uterus = target_body.uterus
                if hasattr(uterus, 'left_ovary') and state.tube_side == 'left':
                    return EjaculationZone.OVARY, uterus.left_ovary
                if hasattr(uterus, 'right_ovary') and state.tube_side == 'right':
                    return EjaculationZone.OVARY, uterus.right_ovary
            
        if getattr(state, 'is_in_tube', False):
            tube = getattr(self.encounter, 'tube_ref', None)
            if tube:
                return EjaculationZone.FALLOPIAN_TUBE, tube
            # Fallback
            if target_body and hasattr(target_body, 'uterus'):
                uterus = target_body.uterus
                if state.tube_side == 'left' and hasattr(uterus, 'left_tube'):
                    return EjaculationZone.FALLOPIAN_TUBE, uterus.left_tube
                if state.tube_side == 'right' and hasattr(uterus, 'right_tube'):
                    return EjaculationZone.FALLOPIAN_TUBE, uterus.right_tube
            
        if getattr(state, 'is_in_uterus', False):
            uterus = getattr(self.encounter, 'uterus_ref', None)
            if uterus:
                return EjaculationZone.UTERUS_CAVITY, uterus
            # Fallback
            if target_body and hasattr(target_body, 'uterus'):
                return EjaculationZone.UTERUS_CAVITY, target_body.uterus
            
        if getattr(state, 'is_through_cervix', False):
            uterus = getattr(self.encounter, 'uterus_ref', None)
            if not uterus and target_body and hasattr(target_body, 'uterus'):
                uterus = target_body.uterus
            
            if uterus:
                if state.current_depth < 12:  # Шейка матки
                    return EjaculationZone.CERVIX, uterus.cervix
                return EjaculationZone.UTERUS_CAVITY, uterus
    
        # Определяем по текущей зоне из state
        current_zone = getattr(state, 'current_zone', None)
        zone_name = None
        if current_zone:
            zone_name = current_zone.name if hasattr(current_zone, 'name') else str(current_zone)
        
        # ВЛАГАЛИЩЕ (любая зона с VAGINA в названии)
        if zone_name and 'VAGINA' in zone_name:
            # Сначала пробуем прямую ссылку
            vagina = getattr(self.encounter, 'vagina_ref', None)
            if vagina:
                return EjaculationZone.VAGINA_CANAL, vagina
            
            # Fallback: ищем в target_body по индексу entry_organ_idx
            if target_body:
                organ_idx = getattr(self.encounter, 'entry_organ_idx', 0)
                
                if hasattr(target_body, 'vaginas') and target_body.vaginas:
                    if organ_idx < len(target_body.vaginas):
                        return EjaculationZone.VAGINA_CANAL, target_body.vaginas[organ_idx]
                    return EjaculationZone.VAGINA_CANAL, target_body.vaginas[0]
                
                if hasattr(target_body, 'vagina') and target_body.vagina:
                    return EjaculationZone.VAGINA_CANAL, target_body.vagina
        
        # ГРУДЬ / СОСКИ
        if zone_name and ('NIPPLE' in zone_name or 'BREAST' in zone_name):
            breast = getattr(self.encounter, 'breast_ref', None)
            if breast:
                return EjaculationZone.BREAST_MILK_DUCT, breast
            
            # Fallback: ищем грудь в target_body
            if target_body and hasattr(target_body, 'breast_grid'):
                # Берем первую доступную грудь
                for row in target_body.breast_grid.rows:
                    for breast in row:
                        return EjaculationZone.BREAST_MILK_DUCT, breast
        
        # АНАЛЬНЫЙ СЕКС
        if zone_name and ('ANAL' in zone_name or 'ANUS' in zone_name or 'RECTUM' in zone_name):
            anus = getattr(self.encounter, 'anus_ref', None)
            if anus:
                return EjaculationZone.ANAL_CANAL, anus
            
            # Fallback
            if target_body:
                organ_idx = getattr(self.encounter, 'entry_organ_idx', 0)
                
                if hasattr(target_body, 'anuses') and target_body.anuses:
                    if organ_idx < len(target_body.anuses):
                        return EjaculationZone.ANAL_CANAL, target_body.anuses[organ_idx]
                    return EjaculationZone.ANAL_CANAL, target_body.anuses[0]
                
                if hasattr(target_body, 'anus') and target_body.anus:
                    return EjaculationZone.ANAL_CANAL, target_body.anus
        
        # УРЕТРА
        if zone_name and 'URETHRA' in zone_name:
            if hasattr(target_body, 'urethra') and target_body.urethra:
                return EjaculationZone.URETHRA, target_body.urethra
        
        # ПОСЛЕДНИЙ FALLBACK: если ничего не определено но есть target_body
        # Пытаемся определить по entry_organ изначального проникновения
        entry_organ = getattr(self.encounter, 'entry_organ', None)
        if entry_organ == 'vagina' and target_body:
            if hasattr(target_body, 'vaginas') and target_body.vaginas:
                return EjaculationZone.VAGINA_CANAL, target_body.vaginas[0]
            if hasattr(target_body, 'vagina') and target_body.vagina:
                return EjaculationZone.VAGINA_CANAL, target_body.vagina
        
        # Если совсем ничего не нашли - возвращаем None чтобы показать ошибку
        return EjaculationZone.VAGINA_CANAL, None


    
    def ejaculate(self, requested_volume: Optional[float] = None, 
                  force: float = 1.0) -> EjaculationResult:
        """
        Выполнить эякуляцию в текущую зону.
        
        Args:
            requested_volume: Запрошенный объем (None = максимально возможный)
            force: Сила эякуляции (0.0 - 1.0)
        """
        messages = []
        
        # 1. Получаем пенис
        penis = self.encounter.penetrating_object
        
        # Проверяем что это действительно пенис (по наличию необходимых методов)
        if not penis or not hasattr(penis, 'ejaculate'):
            return EjaculationResult(
                success=False, volume_ejaculated=0, volume_absorbed=0,
                volume_overflow=0, zone=EjaculationZone.VAGINA_CANAL,
                target_organ=None, fluid_type=None, pulses=0,
                messages=["Нет пениса для эякуляции"]
            )
        
        # 2. Определяем зону
        zone, target = self.determine_zone()
        
        if target is None:
            return EjaculationResult(
                success=False, volume_ejaculated=0, volume_absorbed=0,
                volume_overflow=0, zone=zone, target_organ=None,
                fluid_type=None, pulses=0, messages=["Целевой орган не найден"]
            )
        
        # 3. Получаем жидкость от пениса
        try:
            from body_sim.core.enums import FluidType
        except ImportError:
            # Fallback если нет enums
            FluidType = None
        
        fluid_type = FluidType.CUM if FluidType else "cum"
        
        # Вызываем ejaculate у пениса
        ejac_result = penis.ejaculate(amount=requested_volume, 
                                      fluid_type=fluid_type, 
                                      force=force)
        
        total_volume = ejac_result.get('amount', 0)
        pulses = ejac_result.get('pulses', 0)
        
        if total_volume <= 0:
            return EjaculationResult(
                success=False, volume_ejaculated=0, volume_absorbed=0,
                volume_overflow=0, zone=zone, target_organ=target,
                fluid_type=fluid_type, pulses=0,
                messages=["Нет спермы для эякуляции"]
            )
        
        # 4. Передаем жидкость в целевую зону
        absorbed, overflow, recv_messages = ZoneFluidReceiver.receive_fluid(
            zone=zone,
            target=target,
            fluid_type=fluid_type,
            amount=total_volume,
            source=penis
        )
        
        messages.extend(recv_messages)
        
        # 5. Обновляем статистику
        self.total_ejaculated += absorbed
        self.ejaculation_history.append({
            'zone': zone.name,
            'volume': total_volume,
            'absorbed': absorbed,
            'overflow': overflow,
            'target': type(target).__name__
        })
        
        # 6. Формируем специальные эффекты
        special_effect = None
        if overflow > total_volume * 0.5:
            special_effect = "💦 Сильное переполнение! Жидкость вытекает наружу."
        elif zone == EjaculationZone.OVARY:
            special_effect = "⚠️ Прямая инсеминация яичника!"
        elif zone == EjaculationZone.UTERUS_CAVITY:
            if hasattr(target, 'inflation_status'):
                status = target.inflation_status
                status_val = status.value if hasattr(status, 'value') else str(status)
                special_effect = f"Матка заполнена: {status_val}"
        
        return EjaculationResult(
            success=True,
            volume_ejaculated=total_volume,
            volume_absorbed=absorbed,
            volume_overflow=overflow,
            zone=zone,
            target_organ=target,
            fluid_type=fluid_type,
            pulses=pulses,
            messages=messages,
            special_effect=special_effect
        )

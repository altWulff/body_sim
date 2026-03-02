# anatomy/reproductive/vagina.py
from typing import Dict, List


from body_sim.anatomy.base import AnatomicalComponent
from body_sim.core.events import EventBus


class Vagina(AnatomicalComponent):
    def __init__(self):
        super().__init__("vagina", max_volume=200)
        self.depth_rest = 10.0  # cm
        self.depth_max = 25.0   # cm с растяжением
        self.elasticity = 1.0
        self.muscle_tightness = 1.0
        self.current_depth = 0.0  # текущая глубина проникновения
        self.clitoris_size = 1.0  # cm
        self.clitoris_erect = False
        self.penetration_objects: List[Dict] = []  # активные объекты внутри
        
    def penetrate(self, depth: float, diameter: float, object_id: str, 
                  event_bus: EventBus = None) -> Dict:
        """Возвращает результат проникновения"""
        effective_depth = min(depth, self.depth_max * self.elasticity)
        
        # Проверка контакта с шейкой матки
        cervix_contact = effective_depth >= (self.depth_rest - 1.0)
        
        self.current_depth = effective_depth
        self.penetration_objects.append({
            'id': object_id,
            'depth': effective_depth,
            'diameter': diameter,
            'cervix_contact': cervix_contact
        })
        
        if event_bus:
            event_bus.emit(Event(
                type=EventType.PENETRATION,
                source=self.component_id,
                data={
                    'depth': effective_depth,
                    'cervix_contact': cervix_contact,
                    'object': object_id
                }
            ))
            
        return {
            'success': True,
            'depth': effective_depth,
            'cervix_contact': cervix_contact,
            'resistance': self.muscle_tightness
        }
        
    def stimulate_clitoris(self, intensity: float):
        self.clitoris_erect = True
        self.current_stimulation += intensity * 1.5

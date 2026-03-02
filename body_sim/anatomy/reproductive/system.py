# === anatomy/reproductive/system.py ===
from typing import List, Dict, Any

from body_sim.core.components import BaseComponent
from body_sim.core.events import EventBus
from body_sim.anatomy.reproductive.vagina import Vagina
from body_sim.anatomy.reproductive.uterus import Uterus
from body_sim.anatomy.reproductive.clitoris import Clitoris
from body_sim.anatomy.reproductive.penis import Penis
from body_sim.anatomy.reproductive.scrotum import Scrotum

class ReproductiveSystem(BaseComponent):
    def __init__(self):
        super().__init__("reproductive_system")
        self.vaginas: List[Vagina] = []
        self.uteri: List[Uterus] = []
        self.clitorises: List[Clitoris] = []
        self.penises: List[Penis] = []
        self.scrotums: List[Scrotum] = []
        
    def add_vagina(self, vagina: Vagina):
        self.vaginas.append(vagina)
        vagina.connect_to(self)
        
    def add_uterus(self, uterus: Uterus):
        self.uteri.append(uterus)
        uterus.connect_to(self)
        
    def add_clitoris(self, clitoris: Clitoris):
        self.clitorises.append(clitoris)
        clitoris.connect_to(self)
        
    def add_penis(self, penis: Penis):
        self.penises.append(penis)
        penis.connect_to(self)
        
    def add_scrotum(self, scrotum: Scrotum):
        self.scrotums.append(scrotum)
        scrotum.connect_to(self)
        
    def update(self, delta_time: float, event_bus: EventBus):
        for vagina in self.vaginas:
            vagina.update(delta_time, event_bus)
        for uterus in self.uteri:
            uterus.update(delta_time, event_bus)
        for clitoris in self.clitorises:
            clitoris.update(delta_time, event_bus)
        for penis in self.penises:
            penis.update(delta_time, event_bus)
        for scrotum in self.scrotums:
            scrotum.update(delta_time, event_bus)
            
    def get_state(self) -> Dict[str, Any]:
        return {
            'vaginas': [v.get_state() for v in self.vaginas],
            'uteri': [u.get_state() for u in self.uteri],
            'clitorises': [c.get_state() for c in self.clitorises],
            'penises': [p.get_state() for p in self.penises],
            'scrotums': [s.get_state() for s in self.scrotums]
        }
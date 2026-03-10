# === anatomy/digestive/system.py ===
from typing import Dict, Any

from body_sim.core.components import BaseComponent
from body_sim.core.events import EventBus
from body_sim.anatomy.digestive.mouth import Mouth
from body_sim.anatomy.digestive.stomach import Stomach
from body_sim.anatomy.digestive.anus import Anus
from body_sim.anatomy.base import AnatomicalComponent


class DigestiveSystem(BaseComponent):
    def __init__(self):
        super().__init__("digestive_system")
        self.mouth = Mouth()
        self.stomach = Stomach()
        self.anus = Anus()
        self.intestines = AnatomicalComponent("intestines", max_volume=2000)

    def update(self, delta_time: float, event_bus: EventBus):
        self.mouth.update(delta_time, event_bus)
        self.stomach.update(delta_time, event_bus)
        self.anus.update(delta_time, event_bus)
        self.intestines.update(delta_time, event_bus)

        # Связь ануса с желудком для специфических сценариев
        if self.anus.connected_to_stomach and self.anus.fluids:
            for fluid in self.anus.fluids[:]:
                self.anus.transfer_to(self.stomach, fluid.volume, event_bus=event_bus)

    def get_state(self) -> Dict[str, Any]:
        return {
            "mouth": self.mouth.get_state(),
            "stomach": self.stomach.get_state(),
            "anus": self.anus.get_state(),
            "intestines": self.intestines.get_state(),
        }

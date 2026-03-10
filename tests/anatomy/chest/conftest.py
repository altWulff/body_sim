# tests/anatomy/chest/conftest.py
import pytest
from unittest.mock import MagicMock, Mock
import sys
from pathlib import Path


# Моки для зависимостей проекта (создаем до импорта body_sim)
class MockEventBus:
    def __init__(self):
        self.subscribers = {}
        self.events = []

    def subscribe(self, event_type, callback):
        self.subscribers.setdefault(event_type, []).append(callback)

    def emit(self, event):
        self.events.append(event)
        if event.type in self.subscribers:
            for cb in self.subscribers[event.type]:
                cb(event)


class MockEventType:
    FLUID_ADDED = "fluid_added"
    FLUID_REMOVED = "fluid_removed"
    LEAK = "leak"
    STATE_CHANGE = "state_change"
    MODIFIER_APPLIED = "modifier_applied"
    LACTATION_START = "lactation_start"
    LACTATION_END = "lactation_end"
    LACTATION_ACTIVE = "lactation_active"
    ENGORGEMENT_RELIEF = "engorgement_relief"
    CUP_CHANGE = "cup_change"


# Патчим модули перед импортом
import body_sim.core.events as events_module

events_module.EventBus = MockEventBus
events_module.EventType = MockEventType


@pytest.fixture
def event_bus():
    return MockEventBus()


@pytest.fixture
def mock_fluid_mixture():
    mixture = MagicMock()
    mixture.total.return_value = 0.0
    mixture.viscosity.return_value = 1.0
    mixture.density.return_value = 1.0
    mixture._contents = {}
    mixture.add = MagicMock(return_value=None)
    mixture.remove = MagicMock(return_value={})
    mixture.get_amount = MagicMock(return_value=0.0)
    return mixture


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch, mock_fluid_mixture):
    # Патчим FluidMixture в breast_row модуле напрямую
    monkeypatch.setattr(
        "body_sim.anatomy.chest.breast_row.FluidMixture", lambda: mock_fluid_mixture
    )

    # Аналогично для других импортов если нужно
    # ...

# systems/stats.py
from datetime import datetime
from typing import Dict, List


class StatisticsService:
    """Централизованный сервис статистики (не декоратор, как в старой версии)"""
    def __init__(self):
        self._counters: Dict[str, Dict[str, float]] = {}
        self._history: List[Dict] = []
        
    def record(self, category: str, action: str, value: float = 1.0, metadata: Dict = None):
        if category not in self._counters:
            self._counters[category] = {}
        self._counters[category][action] = self._counters[category].get(action, 0) + value
        
        self._history.append({
            'timestamp': datetime.now(),
            'category': category,
            'action': action,
            'value': value,
            'metadata': metadata or {}
        })
        
    def get_stats(self, category: str = None) -> Dict:
        if category:
            return self._counters.get(category, {})
        return self._counters
        
    def report(self) -> str:
        lines = ["=== Statistics Report ==="]
        for cat, actions in self._counters.items():
            lines.append(f"\n{cat}:")
            for action, value in actions.items():
                lines.append(f"  {action}: {value:.2f}")
        return "\n".join(lines)

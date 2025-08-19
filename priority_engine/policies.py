from __future__ import annotations
from datetime import date
from typing import Optional

def norm_layer(layer: str) -> str:
    key = (layer or "").strip().lower()
    if key in ("fundament", "fundamental", "foundation"): return "fundament"
    if key in ("strategic", "strategie", "strategicky", "strategicke"): return "strategic"
    if key in ("support", "podpurne", "podpůrné"): return "support"
    if key in ("leisure", "volnocas", "volnočas", "experiment", "experiments"): return "leisure"
    return "support"

class DefaultLayerPolicy:
    _weights = {"fundament": 1.30, "strategic": 1.20, "support": 1.00, "leisure": 0.80}
    def weight(self, layer: str) -> float:
        return self._weights.get(norm_layer(layer), 1.0)

class DefaultUrgencyPolicy:
    def urgency_multiplier(self, deadline: Optional[date], today: date) -> float:
        if deadline is None: return 1.00
        d = (deadline - today).days
        return 1.60 if d <= 1 else 1.40 if d <= 3 else 1.20 if d <= 7 else 1.10 if d <= 14 else 1.05
    def days_to_deadline(self, deadline: Optional[date], today: date) -> Optional[int]:
        return None if deadline is None else (deadline - today).days

class DefaultEisenhowerClassifier:
    def quadrant(self, impact: float, deadline: Optional[date], today: date) -> str:
        important = impact >= 3.0
        urgent = deadline is not None and (deadline - today).days <= 3
        if important and urgent: return "Important+Urgent"
        if important: return "Important+NotUrgent"
        if urgent: return "NotImportant+Urgent"
        return "NotImportant+NotUrgent"

    def tag(self, time_est: float, impact: float, deadline: Optional[date], today: date) -> str:
        urgent = (deadline is not None) and ((deadline - today).days <= 3)
        if time_est <= 0.5 and (impact >= 2.0 or urgent): return "QuickWin"
        if time_est <= 2.0 and impact >= 3.0: return "HighROI"
        if time_est >= 4.0 and impact >= 4.0: return "BigBet"
        return ""

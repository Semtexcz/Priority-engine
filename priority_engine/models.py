from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

@dataclass
class Task:
    title: str
    owner: str = "já"
    deadline: Optional[date] = None
    time_est: float = 1.0
    energy: str = "medium"
    layer: str = "Support"
    impact: float = 3.0
    leverage: float = 3.0
    effort: float = 2.0
    notes: str = ""

    # computed
    layer_weight: float = field(init=False, default=1.0)
    um: float = field(init=False, default=1.0)
    importance_core: float = field(init=False, default=0.0)
    score: float = field(init=False, default=0.0)
    quadrant: str = field(init=False, default="")
    tag: str = field(init=False, default="")
    days_to_deadline: Optional[int] = field(init=False, default=None)

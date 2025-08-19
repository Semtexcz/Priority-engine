from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

@dataclass
class Task:
    """
    Represents a task with attributes for prioritization and productivity scoring.

    This class models a single task with metadata such as deadline, estimated
    time, energy requirements, and prioritization metrics (impact, leverage, effort).
    It also contains computed fields for importance and quadrant classification
    in frameworks like the Eisenhower matrix or custom productivity models.

    :ivar title: Short descriptive title of the task.
    :vartype title: str

    :ivar owner: Person responsible for the task. Defaults to ``"já"``.
    :vartype owner: str

    :ivar deadline: Due date for the task, or ``None`` if no deadline is set.
    :vartype deadline: Optional[date]

    :ivar time_est: Estimated time required to complete the task (in hours).
                    Defaults to ``1.0``.
    :vartype time_est: float

    :ivar energy: Subjective energy level needed to complete the task
                  (e.g., ``"low"``, ``"medium"``, ``"high"``). Defaults to ``"medium"``.
    :vartype energy: str

    :ivar layer: Category or work layer the task belongs to
                 (e.g., ``"Support"``, ``"Core"``). Defaults to ``"Support"``.
    :vartype layer: str

    :ivar impact: Expected impact of completing the task, typically on a numeric scale.
                  Defaults to ``3.0``.
    :vartype impact: float

    :ivar leverage: Degree to which the task creates multiplier effects.
                    Defaults to ``3.0``.
    :vartype leverage: float

    :ivar effort: Amount of effort required (difficulty or resistance).
                  Defaults to ``2.0``.
    :vartype effort: float

    :ivar notes: Additional notes or description for the task. Defaults to ``""``.
    :vartype notes: str

    Computed Attributes
    -------------------
    These fields are calculated automatically and should not be set manually:

    :ivar layer_weight: Weight assigned based on the task's layer.
    :vartype layer_weight: float

    :ivar um: Utility measure, often used as an intermediate metric.
    :vartype um: float

    :ivar importance_core: Calculated importance of the task relative to core priorities.
    :vartype importance_core: float

    :ivar score: Final prioritization score combining impact, leverage, and effort.
    :vartype score: float

    :ivar quadrant: Classification of the task into a prioritization quadrant
                    (e.g., Eisenhower matrix).
    :vartype quadrant: str

    :ivar tag: Additional categorization or label for the task.
    :vartype tag: str

    :ivar days_to_deadline: Number of days remaining until the deadline,
                            or ``None`` if no deadline is set.
    :vartype days_to_deadline: Optional[int]
    """
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

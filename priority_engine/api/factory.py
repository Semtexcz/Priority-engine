from __future__ import annotations
from datetime import date
from typing import Optional
from ..repositories import TabularTaskRepository
from ..services import TaskPreFilter, TaskComputer, PriorityEngine
from ..sorters import BacklogSorter
from ..selectors import DefaultMITSelector


class ApiEngineFactory:
    """
    Factory for constructing a :class:`PriorityEngine` instance configured for the API layer.

    The factory encapsulates initialization of all required components:
    - Repository for storing tasks (:class:`TabularTaskRepository`)
    - Pre-filtering logic (:class:`TaskPreFilter`)
    - Task scoring and computation (:class:`TaskComputer`)
    - Sorting strategy (:class:`BacklogSorter`)
    - MIT selection strategy (:class:`DefaultMITSelector`)
    """

    @staticmethod
    def build(today: Optional[date] = None, alpha: float = 0.7) -> PriorityEngine:
        """
        Build and return a configured :class:`PriorityEngine`.

        :param today: Optional date to override "today" (useful for tests).
        :type today: date or None
        :param alpha: Damping parameter for scoring effort in denominator.
                      Defaults to 0.7. Can be tuned for different prioritization dynamics.
        :type alpha: float
        :return: Fully configured :class:`PriorityEngine` ready for API usage.
        :rtype: PriorityEngine
        """
        # TaskComputer internally uses default policies and scoring.
        computer = TaskComputer(today=today)
        # Reconfigure alpha (optional – for more dynamic control).
        computer.scoring._alpha = alpha  # safe, but a setter could be added

        return PriorityEngine(
            repo=TabularTaskRepository(),
            computer=computer,
            pre=TaskPreFilter(),
            sorter=BacklogSorter(),
            mit_selector=DefaultMITSelector(),
        )

from __future__ import annotations
from datetime import date
from typing import List
from .models import Task


class BacklogSorter:
    """
    Sorter for prioritizing a backlog of tasks.

    Sorting strategy:
    1. Higher score first (descending).
    2. Earlier deadline first (ascending).
    3. Higher impact first (descending).

    This ensures that the most valuable, urgent, and impactful tasks
    appear at the top of the list.
    """

    @staticmethod
    def sort(tasks: List[Task]) -> List[Task]:
        """
        Sort a list of tasks according to score, deadline, and impact.

        :param tasks: List of tasks to be sorted.
        :type tasks: List[Task]
        :return: Sorted list of tasks.
        :rtype: List[Task]

        Sorting criteria:
        - **Score**: Higher scores are ranked first.
        - **Deadline**: Tasks with earlier deadlines are ranked earlier.
          Tasks without deadlines are treated as having the maximum possible date.
        - **Impact**: Among tasks with equal score and deadline, higher impact is ranked first.
        """
        def key(t: Task):
            dl = date.max if t.deadline is None else t.deadline
            return (-t.score, dl, -t.impact)
        return sorted(tasks, key=key)

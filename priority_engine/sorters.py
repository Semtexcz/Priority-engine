from __future__ import annotations
from datetime import date
from typing import List
from .models import Task

class BacklogSorter:
    @staticmethod
    def sort(tasks: List[Task]) -> List[Task]:
        def key(t: Task):
            dl = date.max if t.deadline is None else t.deadline
            return (-t.score, dl, -t.impact)
        return sorted(tasks, key=key)
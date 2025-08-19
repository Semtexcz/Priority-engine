from __future__ import annotations
from datetime import date
from typing import List, Optional, Tuple
from .models import Task
from .policies import DefaultUrgencyPolicy, DefaultLayerPolicy, DefaultEisenhowerClassifier
from .scoring import PowerScoringStrategy

class TaskPreFilter:
    def filter(self, tasks: List[Task]) -> Tuple[List[Task], List[Task], List[Task]]:
        keep, delegated, dropped = [], [], []
        for t in tasks:
            owner_key = (t.owner or "").strip().lower()
            if owner_key not in ("ja", "já", "me", "mne", "moje", "i"):
                delegated.append(t); continue
            if t.impact <= 1 and t.leverage <= 1 and t.effort >= 3:
                dropped.append(t); continue
            keep.append(t)
        return keep, delegated, dropped

class TaskComputer:
    def __init__(self, today: Optional[date] = None) -> None:
        self.today = today or date.today()
        self.urgency = DefaultUrgencyPolicy()
        self.layers = DefaultLayerPolicy()
        self.classifier = DefaultEisenhowerClassifier()
        self.scoring = PowerScoringStrategy(alpha=0.7)

    def compute(self, t: Task) -> Task:
        t.layer_weight = self.layers.weight(t.layer)
        t.um = self.urgency.urgency_multiplier(t.deadline, self.today)
        t.importance_core = self.scoring.importance_core(t.impact, t.leverage, t.layer_weight)
        t.score = self.scoring.score(t.importance_core, t.um, t.effort)
        t.quadrant = self.classifier.quadrant(t.impact, t.deadline, self.today)
        t.tag = self.classifier.tag(t.time_est, t.impact, t.deadline, self.today)
        t.days_to_deadline = self.urgency.days_to_deadline(t.deadline, self.today)
        return t

class PriorityEngine:
    def __init__(self, repo, computer: TaskComputer, pre: TaskPreFilter, sorter, mit_selector):
        self.repo, self.computer, self.pre, self.sorter, self.mit_selector = repo, computer, pre, sorter, mit_selector

    def process(self, input_path, output_path, mits_out=None):
        tasks = self.repo.load(input_path)
        kept, delegated, dropped = self.pre.filter(tasks)
        computed = [self.computer.compute(t) for t in kept]
        sorted_tasks = self.sorter.sort(computed)
        self.repo.dump_csv(output_path, sorted_tasks)
        mits = []
        if mits_out:
            mits = self.mit_selector.select(sorted_tasks)
            self.mit_selector.dump_markdown(mits_out, mits)
        return sorted_tasks, delegated, dropped, mits

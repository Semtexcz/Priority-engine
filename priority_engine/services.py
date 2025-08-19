from __future__ import annotations
from datetime import date
from typing import List, Optional, Tuple
from .models import Task
from .policies import DefaultUrgencyPolicy, DefaultLayerPolicy, DefaultEisenhowerClassifier
from .scoring import PowerScoringStrategy


class TaskPreFilter:
    """
    Pre-filter for tasks before scoring and prioritization.

    This class separates tasks into three groups:
    - **keep**: tasks owned by the current user and worth keeping
    - **delegated**: tasks assigned to someone else
    - **dropped**: tasks with low impact, low leverage, and high effort
    """

    def filter(self, tasks: List[Task]) -> Tuple[List[Task], List[Task], List[Task]]:
        """
        Filter a list of tasks into keep, delegated, and dropped categories.

        :param tasks: List of tasks to be filtered.
        :type tasks: List[Task]
        :return: A tuple ``(keep, delegated, dropped)`` containing lists of tasks.
        :rtype: Tuple[List[Task], List[Task], List[Task]]
        """
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
    """
    Computes derived attributes for tasks using defined policies.

    This includes urgency multipliers, layer weights, importance core,
    final score, Eisenhower quadrant classification, tags, and deadline metrics.
    """

    def __init__(self, today: Optional[date] = None) -> None:
        """
        Initialize a task computer with policies.

        :param today: Reference date for urgency/deadline calculations.
                      Defaults to current date if not provided.
        :type today: Optional[date]
        """
        self.today = today or date.today()
        self.urgency = DefaultUrgencyPolicy()
        self.layers = DefaultLayerPolicy()
        self.classifier = DefaultEisenhowerClassifier()
        self.scoring = PowerScoringStrategy(alpha=0.7)

    def compute(self, t: Task) -> Task:
        """
        Compute derived fields for a given task.

        Updates the following attributes:
        - ``layer_weight``
        - ``um``
        - ``importance_core``
        - ``score``
        - ``quadrant``
        - ``tag``
        - ``days_to_deadline``

        :param t: The task to compute fields for.
        :type t: Task
        :return: The task with updated computed attributes.
        :rtype: Task
        """
        t.layer_weight = self.layers.weight(t.layer)
        t.um = self.urgency.urgency_multiplier(t.deadline, self.today)
        t.importance_core = self.scoring.importance_core(t.impact, t.leverage, t.layer_weight)
        t.score = self.scoring.score(t.importance_core, t.um, t.effort)
        t.quadrant = self.classifier.quadrant(t.impact, t.deadline, self.today)
        t.tag = self.classifier.tag(t.time_est, t.impact, t.deadline, self.today)
        t.days_to_deadline = self.urgency.days_to_deadline(t.deadline, self.today)
        return t


class PriorityEngine:
    """
    High-level engine to process tasks from input to prioritized output.

    Combines repository I/O, pre-filtering, task computation, sorting,
    and Most Important Task (MIT) selection.
    """

    def __init__(self, repo, computer: TaskComputer, pre: TaskPreFilter, sorter, mit_selector):
        """
        Initialize the priority engine.

        :param repo: Repository for loading and saving tasks.
        :type repo: object
        :param computer: Task computer for computing derived fields.
        :type computer: TaskComputer
        :param pre: Pre-filter for delegating/dropping tasks.
        :type pre: TaskPreFilter
        :param sorter: Sorting strategy for prioritizing tasks.
        :type sorter: object
        :param mit_selector: Selector for choosing Most Important Tasks (MITs).
        :type mit_selector: object
        """
        self.repo, self.computer, self.pre, self.sorter, self.mit_selector = repo, computer, pre, sorter, mit_selector

    def process(self, input_path, output_path, mits_out=None):
        """
        Process tasks from input to output.

        Steps:
        1. Load tasks from repository.
        2. Pre-filter into keep, delegated, and dropped.
        3. Compute derived attributes for kept tasks.
        4. Sort tasks using the sorter.
        5. Save sorted tasks to CSV.
        6. Optionally select and dump MITs.

        :param input_path: Path to the input file (CSV or JSON).
        :type input_path: Path
        :param output_path: Path to the output CSV file.
        :type output_path: Path
        :param mits_out: Optional path to save MITs in Markdown format.
        :type mits_out: Optional[Path]
        :return: Tuple of (sorted tasks, delegated, dropped, mits).
        :rtype: Tuple[List[Task], List[Task], List[Task], List[Task]]
        """
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

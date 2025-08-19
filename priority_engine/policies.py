from __future__ import annotations
from datetime import date
from typing import Optional

def norm_layer(layer: str) -> str:
    """
    Normalize a layer string to a canonical form.

    The function accepts different variants of layer names (including translations)
    and maps them to one of the standard categories: ``fundament``, ``strategic``,
    ``support``, or ``leisure``. If the input does not match any known category,
    the default value ``support`` is returned.

    :param layer: The input layer string to normalize.
    :type layer: str
    :return: Normalized layer string.
    :rtype: str
    """
    key = (layer or "").strip().lower()
    if key in ("fundament", "fundamental", "foundation"): return "fundament"
    if key in ("strategic", "strategie", "strategicky", "strategicke"): return "strategic"
    if key in ("support", "podpurne", "podpůrné"): return "support"
    if key in ("leisure", "volnocas", "volnočas", "experiment", "experiments"): return "leisure"
    return "support"


class DefaultLayerPolicy:
    """
    Policy for assigning weights to layers.

    This class defines a mapping of normalized task layers to numeric weights.
    Higher weights indicate greater importance in prioritization calculations.
    """

    _weights = {"fundament": 1.30, "strategic": 1.20, "support": 1.00, "leisure": 0.80}

    def weight(self, layer: str) -> float:
        """
        Get the weight associated with a given layer.

        :param layer: The name of the layer to evaluate.
        :type layer: str
        :return: Weight of the layer. Defaults to ``1.0`` if the layer is unknown.
        :rtype: float
        """
        return self._weights.get(norm_layer(layer), 1.0)


class DefaultUrgencyPolicy:
    """
    Policy for calculating urgency multipliers based on deadlines.

    This class determines how close a deadline is and assigns a numeric urgency
    multiplier. It also provides utility for computing days remaining.
    """

    def urgency_multiplier(self, deadline: Optional[date], today: date) -> float:
        """
        Compute an urgency multiplier based on the deadline.

        :param deadline: The deadline for the task, or ``None`` if no deadline exists.
        :type deadline: Optional[date]
        :param today: The current date.
        :type today: date
        :return: Urgency multiplier. Higher values mean greater urgency.
        :rtype: float
        """
        if deadline is None: return 1.00
        d = (deadline - today).days
        return 1.60 if d <= 1 else 1.40 if d <= 3 else 1.20 if d <= 7 else 1.10 if d <= 14 else 1.05

    def days_to_deadline(self, deadline: Optional[date], today: date) -> Optional[int]:
        """
        Calculate the number of days remaining until the deadline.

        :param deadline: The deadline for the task, or ``None`` if no deadline exists.
        :type deadline: Optional[date]
        :param today: The current date.
        :type today: date
        :return: Number of days until deadline, or ``None`` if no deadline.
        :rtype: Optional[int]
        """
        return None if deadline is None else (deadline - today).days


class DefaultEisenhowerClassifier:
    """
    Classifier based on the Eisenhower matrix.

    This class classifies tasks into quadrants of the Eisenhower matrix depending
    on importance and urgency. It also provides simple tagging heuristics for tasks.
    """

    def quadrant(self, impact: float, deadline: Optional[date], today: date) -> str:
        """
        Classify a task into one of the Eisenhower quadrants.

        :param impact: Impact score of the task.
        :type impact: float
        :param deadline: The deadline of the task, or ``None`` if no deadline exists.
        :type deadline: Optional[date]
        :param today: The current date.
        :type today: date
        :return: Quadrant classification (``"Important+Urgent"``,
                 ``"Important+NotUrgent"``, ``"NotImportant+Urgent"``,
                 ``"NotImportant+NotUrgent"``).
        :rtype: str
        """
        important = impact >= 3.0
        urgent = deadline is not None and (deadline - today).days <= 3
        if important and urgent: return "Important+Urgent"
        if important: return "Important+NotUrgent"
        if urgent: return "NotImportant+Urgent"
        return "NotImportant+NotUrgent"

    def tag(self, time_est: float, impact: float, deadline: Optional[date], today: date) -> str:
        """
        Assign a heuristic tag to a task.

        Tags are based on a combination of time estimate, impact, and urgency.

        - ``QuickWin``: Short tasks (<= 0.5h) with impact >= 2.0 or urgent.
        - ``HighROI``: Medium tasks (<= 2h) with impact >= 3.0.
        - ``BigBet``: Large tasks (>= 4h) with very high impact (>= 4.0).

        :param time_est: Estimated time required (in hours).
        :type time_est: float
        :param impact: Impact score of the task.
        :type impact: float
        :param deadline: Deadline of the task, or ``None`` if no deadline exists.
        :type deadline: Optional[date]
        :param today: The current date.
        :type today: date
        :return: Tag string, or empty string if no tag applies.
        :rtype: str
        """
        urgent = (deadline is not None) and ((deadline - today).days <= 3)
        if time_est <= 0.5 and (impact >= 2.0 or urgent): return "QuickWin"
        if time_est <= 2.0 and impact >= 3.0: return "HighROI"
        if time_est >= 4.0 and impact >= 4.0: return "BigBet"
        return ""

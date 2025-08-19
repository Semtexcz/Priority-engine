from __future__ import annotations
from pathlib import Path
from typing import List
from .models import Task
from .policies import norm_layer


class DefaultMITSelector:
    """
    Default strategy for selecting MITs (Most Important Tasks).

    The selection process favors:
    1. One **fundament** task (if available).
    2. One **strategic** task (prioritizing those tagged as ``BigBet``).
    3. One **momentum** task (tagged as ``HighROI`` or ``QuickWin``).

    The final list is deduplicated and limited to a maximum of three tasks.
    """

    def select(self, tasks: List[Task]) -> List[Task]:
        """
        Select MITs (Most Important Tasks) from a list of tasks.

        Selection logic:
        - Prefer a task from the ``fundament`` layer.
        - Prefer a task from the ``strategic`` layer, prioritizing those tagged ``BigBet``.
        - Prefer one task that builds momentum (tagged ``HighROI`` or ``QuickWin``).
        - Ensure no duplicates, and return at most 3 tasks.

        :param tasks: List of tasks to choose from.
        :type tasks: List[Task]
        :return: Selected MITs (maximum of 3).
        :rtype: List[Task]
        """
        fundament = [t for t in tasks if norm_layer(t.layer) == "fundament"]
        strategic = [t for t in tasks if norm_layer(t.layer) == "strategic"]
        momentum = [t for t in tasks if t.tag in ("HighROI", "QuickWin")]

        result = []
        if fundament:
            result.append(fundament[0])
        if strategic:
            bigbets = [t for t in strategic if t.tag == "BigBet"]
            result.append((bigbets or strategic)[0])
        pool = [t for t in momentum if t not in result]
        if pool:
            result.append(pool[0])

        uniq, seen = [], set()
        for t in result:
            if id(t) not in seen:
                uniq.append(t)
                seen.add(id(t))
        return uniq[:3]

    def dump_markdown(self, path: Path, mits: List[Task]) -> None:
        """
        Write MITs to a Markdown file.

        Output format:
        - Heading ``# Dnešní MIT (Most Important Tasks)``
        - Subsections for each MIT with details:
          - Layer, Tag, Quadrant
          - Score, Time estimate, Effort, Impact, Leverage
          - Deadline (if available)
          - Notes (if provided)

        :param path: Path to the Markdown output file.
        :type path: Path
        :param mits: List of MITs to write.
        :type mits: List[Task]
        :return: None
        """
        with path.open("w", encoding="utf-8") as f:
            f.write("# Dnešní MIT (Most Important Tasks)\n\n")
            if not mits:
                f.write("_Nenalezeny vhodné MIT._\n")
                return
            for i, t in enumerate(mits, 1):
                f.write(f"## {i}. {t.title}\n")
                f.write(f"- Layer: **{t.layer}** | Tag: **{t.tag or '—'}** | Quadrant: **{t.quadrant}**\n")
                f.write(f"- Score: **{t.score:.2f}** | TimeEst: **{t.time_est} h** | Effort: **{t.effort}** | Impact: **{t.impact}** | Leverage: **{t.leverage}**\n")
                if t.deadline:
                    f.write(f"- Deadline: **{t.deadline.isoformat()}** (D-**{t.days_to_deadline}**)\n")
                if t.notes:
                    f.write(f"- Poznámky: {t.notes}\n")
                f.write("\n")

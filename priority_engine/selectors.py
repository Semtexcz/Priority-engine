from __future__ import annotations
from pathlib import Path
from typing import List
from .models import Task
from .policies import norm_layer

class DefaultMITSelector:
    def select(self, tasks: List[Task]) -> List[Task]:
        fundament = [t for t in tasks if norm_layer(t.layer) == "fundament"]
        strategic = [t for t in tasks if norm_layer(t.layer) == "strategic"]
        momentum = [t for t in tasks if t.tag in ("HighROI", "QuickWin")]

        result = []
        if fundament: result.append(fundament[0])
        if strategic:
            bigbets = [t for t in strategic if t.tag == "BigBet"]
            result.append((bigbets or strategic)[0])
        pool = [t for t in momentum if t not in result]
        if pool: result.append(pool[0])

        uniq, seen = [], set()
        for t in result:
            if id(t) not in seen: uniq.append(t); seen.add(id(t))
        return uniq[:3]

    def dump_markdown(self, path: Path, mits: List[Task]) -> None:
        with path.open("w", encoding="utf-8") as f:
            f.write("# Dnešní MIT (Most Important Tasks)\n\n")
            if not mits:
                f.write("_Nenalezeny vhodné MIT._\n"); return
            for i, t in enumerate(mits, 1):
                f.write(f"## {i}. {t.title}\n")
                f.write(f"- Layer: **{t.layer}** | Tag: **{t.tag or '—'}** | Quadrant: **{t.quadrant}**\n")
                f.write(f"- Score: **{t.score:.2f}** | TimeEst: **{t.time_est} h** | Effort: **{t.effort}** | Impact: **{t.impact}** | Leverage: **{t.leverage}**\n")
                if t.deadline:
                    f.write(f"- Deadline: **{t.deadline.isoformat()}** (D-**{t.days_to_deadline}**)\n")
                if t.notes: f.write(f"- Poznámky: {t.notes}\n")
                f.write("\n")

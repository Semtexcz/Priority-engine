from __future__ import annotations
import csv, json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from .models import Task

def parse_date(value: Optional[str]):
    if not value or not str(value).strip(): return None
    s = str(value).strip()
    try:
        return date.fromisoformat(s)
    except ValueError:
        for fmt in ("%Y/%m/%d", "%d.%m.%Y", "%d/%m/%Y"):
            try: return datetime.strptime(s, fmt).date()
            except ValueError: pass
    raise ValueError(f"Neznámý formát data: {value}")

class TabularTaskRepository:
    def load(self, path: Path) -> List[Task]:
        if path.suffix.lower() == ".csv": return self._load_csv(path)
        if path.suffix.lower() == ".json": return self._load_json(path)
        raise ValueError("Podporované vstupy: .csv nebo .json")

    def dump_csv(self, path: Path, tasks: List[Task]) -> None:
        fields = ["Title","Owner","Deadline","DaysToDeadline","TimeEst","Energy","Layer",
                  "Impact","Leverage","Effort","LayerWeight","UM","ImportanceCore",
                  "Score","Quadrant","Tag","Notes"]
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
            for t in tasks:
                w.writerow({
                    "Title": t.title, "Owner": t.owner,
                    "Deadline": "" if t.deadline is None else t.deadline.isoformat(),
                    "DaysToDeadline": "" if t.days_to_deadline is None else t.days_to_deadline,
                    "TimeEst": t.time_est, "Energy": t.energy, "Layer": t.layer,
                    "Impact": t.impact, "Leverage": t.leverage, "Effort": t.effort,
                    "LayerWeight": round(t.layer_weight, 3), "UM": round(t.um, 3),
                    "ImportanceCore": round(t.importance_core, 3), "Score": round(t.score, 3),
                    "Quadrant": t.quadrant, "Tag": t.tag, "Notes": t.notes
                })

    def _load_csv(self, path: Path) -> List[Task]:
        tasks: List[Task] = []
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                g = self._get(row)
                tasks.append(Task(
                    title=g("Title", required=True),
                    owner=g("Owner","já"),
                    deadline=parse_date(g("Deadline","")),
                    time_est=float(g("TimeEst","1") or 1),
                    energy=(g("Energy","medium") or "medium").strip().lower(),
                    layer=g("Layer","Support"),
                    impact=float(g("Impact","3") or 3),
                    leverage=float(g("Leverage","3") or 3),
                    effort=float(g("Effort","2") or 2),
                    notes=g("Notes",""),
                ))
        return tasks

    def _load_json(self, path: Path) -> List[Task]:
        with path.open(encoding="utf-8") as f: data = json.load(f)
        items = data.get("tasks", data) if isinstance(data, dict) else data
        return [Task(
            title=i.get("Title",""), owner=i.get("Owner","já"),
            deadline=parse_date(i.get("Deadline")), time_est=float(i.get("TimeEst",1)),
            energy=(i.get("Energy","medium") or "medium").strip().lower(),
            layer=i.get("Layer","Support"), impact=float(i.get("Impact",3)),
            leverage=float(i.get("Leverage",3)), effort=float(i.get("Effort",2)),
            notes=i.get("Notes",""),
        ) for i in items]

    @staticmethod
    def _get(row: Dict[str, Any]):
        def get(name: str, default: str = "", required: bool = False) -> str:
            for k, v in row.items():
                if k.strip().lower() == name.strip().lower():
                    if required and (v is None or str(v).strip() == ""):
                        raise ValueError(f"Pole '{name}' je povinné.")
                    return "" if v is None else str(v)
            if required: raise ValueError(f"Pole '{name}' je povinné.")
            return default
        return get
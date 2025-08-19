from __future__ import annotations
import csv, json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from .models import Task

def parse_date(value: Optional[str]):
    """
    Parse a string into a :class:`datetime.date`.

    Supports multiple formats, including ISO (``YYYY-MM-DD``),
    slash-separated (``YYYY/MM/DD``), and European styles
    (``DD.MM.YYYY``, ``DD/MM/YYYY``).

    :param value: Input string to parse, or ``None``.
    :type value: Optional[str]
    :return: Parsed date object, or ``None`` if the input is empty.
    :rtype: Optional[date]
    :raises ValueError: If the string does not match any supported format.
    """
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
    """
    Repository for loading and saving tasks from tabular data sources.

    This repository supports CSV and JSON file formats. It provides
    methods to load tasks into :class:`Task` objects and to export
    them back to CSV.

    Methods
    -------
    - :meth:`load`: Load tasks from a file (CSV or JSON).
    - :meth:`dump_csv`: Save tasks to a CSV file.
    - :meth:`_load_csv`: Internal method to load from CSV.
    - :meth:`_load_json`: Internal method to load from JSON.
    - :meth:`_get`: Internal helper to extract values from rows.
    """

    def load(self, path: Path) -> List[Task]:
        """
        Load tasks from a file (CSV or JSON).

        :param path: Path to the file.
        :type path: Path
        :return: List of tasks.
        :rtype: List[Task]
        :raises ValueError: If the file extension is not supported.
        """
        if path.suffix.lower() == ".csv": return self._load_csv(path)
        if path.suffix.lower() == ".json": return self._load_json(path)
        raise ValueError("Podporované vstupy: .csv nebo .json")

    def dump_csv(self, path: Path, tasks: List[Task]) -> None:
        """
        Save tasks into a CSV file.

        :param path: Path to the output CSV file.
        :type path: Path
        :param tasks: List of tasks to save.
        :type tasks: List[Task]
        :return: None
        """
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
        """
        Internal method to load tasks from a CSV file.

        :param path: Path to the CSV file.
        :type path: Path
        :return: List of tasks loaded from the file.
        :rtype: List[Task]
        :raises ValueError: If required fields are missing.
        """
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
        """
        Internal method to load tasks from a JSON file.

        The JSON can be either a list of task dictionaries or a dictionary
        with a key ``"tasks"`` containing the list.

        :param path: Path to the JSON file.
        :type path: Path
        :return: List of tasks loaded from the file.
        :rtype: List[Task]
        """
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
        """
        Helper factory for safely accessing values in a row.

        Returns a function ``get(name, default, required)`` that retrieves
        a value from the row in a case-insensitive manner.

        :param row: A dictionary representing a single row from the input.
        :type row: Dict[str, Any]
        :return: A function that retrieves values by column name.
        :rtype: Callable[[str, str, bool], str]
        :raises ValueError: If a required field is missing or empty.
        """
        def get(name: str, default: str = "", required: bool = False) -> str:
            for k, v in row.items():
                if k.strip().lower() == name.strip().lower():
                    if required and (v is None or str(v).strip() == ""):
                        raise ValueError(f"Pole '{name}' je povinné.")
                    return "" if v is None else str(v)
            if required: raise ValueError(f"Pole '{name}' je povinné.")
            return default
        return get

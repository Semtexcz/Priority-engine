from __future__ import annotations
import csv, json, io
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
    if not value or not str(value).strip():
        return None
    s = str(value).strip()
    try:
        return date.fromisoformat(s)
    except ValueError:
        for fmt in ("%Y/%m/%d", "%d.%m.%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                pass
    raise ValueError(f"Neznámý formát data: {value}")

def _norm_energy(v: str) -> str:
    return (v or "medium").strip().lower()

def _case_get(row: Dict[str, Any]):
    """Case-insensitive getter pro CSV DictReader řádky."""
    def get(name: str, default: str = "", required: bool = False) -> str:
        for k, v in row.items():
            if k and k.strip().lower() == name.strip().lower():
                if required and (v is None or str(v).strip() == ""):
                    raise ValueError(f"Pole '{name}' je povinné.")
                return "" if v is None else str(v)
        if required:
            raise ValueError(f"Pole '{name}' je povinné.")
        return default
    return get


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
        if path.suffix.lower() == ".csv":
            return self._load_csv_text(path.read_text(encoding="utf-8"))
        if path.suffix.lower() == ".json":
            return self._load_json_obj(json.loads(path.read_text(encoding="utf-8")))
        raise ValueError("Podporované vstupy: .csv nebo .json")
    
    def load_from_bytes(
        self,
        data: bytes,
        *,
        content_type: str | None = None,
        filename: str | None = None,
    ) -> List[Task]:
        """
        Načti úkoly z bytů (např. upload v API). Provede autodetekci CSV/JSON podle
        content-type/přípony; fallback heuristika zkusí nejdřív JSON, pak CSV.
        """
        ctype = (content_type or "").lower()
        fname = (filename or "").lower()

        # 1) Preferuj content-type / příponu
        if "json" in ctype or fname.endswith(".json"):
            return self._load_json_bytes(data)
        if "csv" in ctype or fname.endswith(".csv") or ctype in ("text/plain", ""):
            return self._load_csv_bytes(data)

        # 2) Fallback heuristika
        try:
            return self._load_json_bytes(data)
        except Exception:
            return self._load_csv_bytes(data)

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
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for t in tasks:
                w.writerow({
                    "Title": t.title,
                    "Owner": t.owner,
                    "Deadline": "" if t.deadline is None else t.deadline.isoformat(),
                    "DaysToDeadline": "" if t.days_to_deadline is None else t.days_to_deadline,
                    "TimeEst": t.time_est,
                    "Energy": t.energy,
                    "Layer": t.layer,
                    "Impact": t.impact,
                    "Leverage": t.leverage,
                    "Effort": t.effort,
                    "LayerWeight": round(t.layer_weight, 3),
                    "UM": round(t.um, 3),
                    "ImportanceCore": round(t.importance_core, 3),
                    "Score": round(t.score, 3),
                    "Quadrant": t.quadrant,
                    "Tag": t.tag,
                    "Notes": t.notes,
                })
                
    # -------- Interní implementace (text/bytes/obj) --------

    def _load_csv_bytes(self, data: bytes) -> List[Task]:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
        return self._load_csv_text(text)
    
    def _load_csv_text(self, text: str) -> List[Task]:
        tasks: List[Task] = []
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            g = _case_get(row)
            tasks.append(Task(
                title=g("Title", required=True),
                owner=g("Owner", "já") or "já",
                deadline=parse_date(g("Deadline", "")),
                time_est=float(g("TimeEst", "1") or 1),
                energy=_norm_energy(g("Energy", "medium")),
                layer=g("Layer", "Support") or "Support",
                impact=float(g("Impact", "3") or 3),
                leverage=float(g("Leverage", "3") or 3),
                effort=float(g("Effort", "2") or 2),
                notes=g("Notes", ""),
            ))
        return tasks

    def _load_json_bytes(self, data: bytes) -> List[Task]:
        try:
            obj = json.loads(data.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Neplatný JSON: {e}")
        return self._load_json_obj(obj)

    def _load_json_obj(self, obj: Any) -> List[Task]:
        items = obj.get("tasks", obj) if isinstance(obj, dict) else obj
        if not isinstance(items, list):
            raise ValueError("JSON musí být seznam objektů nebo {'tasks': [...]}")

        tasks: List[Task] = []
        for it in items:
            if not isinstance(it, dict):
                raise ValueError("Každá položka musí být JSON objekt")
            tasks.append(Task(
                title=it.get("Title", ""),
                owner=it.get("Owner", "já"),
                deadline=parse_date(it.get("Deadline")),
                time_est=float(it.get("TimeEst", 1)),
                energy=_norm_energy(it.get("Energy", "medium")),
                layer=it.get("Layer", "Support"),
                impact=float(it.get("Impact", 3)),
                leverage=float(it.get("Leverage", 3)),
                effort=float(it.get("Effort", 2)),
                notes=it.get("Notes", ""),
            ))
        return tasks

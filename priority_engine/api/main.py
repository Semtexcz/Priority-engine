"""
Priority Engine API.

This module defines the FastAPI application, including its endpoints for
health check, task processing, and template generation. It also provides
an entrypoint for running the API server with uvicorn.

Endpoints
---------
- GET /health : Health check endpoint.
- POST /process : Process tasks and return prioritized results.
- POST /template : Return a sample template payload with example tasks.
"""

from __future__ import annotations
import csv
import io
import json
import os
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from typing import List

from priority_engine.repositories import TabularTaskRepository

from .schemas import ProcessRequest, ProcessResponse, TaskOut, TemplateResponse, TaskIn
from .factory import ApiEngineFactory
from ..models import Task

app = FastAPI(title="Priority Engine API", version="0.1.0")

# CORS – for local testing allow all origins; in production restrict domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Parsování CSV/JSON uploadu na seznam doménových Task ----------
def _tasks_from_csv_bytes(data: bytes) -> List[Task]:
    try:
        text = data.decode("utf-8-sig")  # podpora BOM
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    tasks: List[Task] = []
    for row in reader:
        # kompatibilní s tvou CSV hlavičkou
        def get(key: str, default: str = "") -> str:
            for k, v in row.items():
                if k and k.strip().lower() == key.strip().lower():
                    return "" if v is None else str(v)
            return default

        # Deadline: string -> date (použijeme stejnou logiku jako v repositories.py)
        from ..repositories import parse_date as _parse_date

        tasks.append(
            Task(
                title=get("Title", ""),
                owner=get("Owner", "já") or "já",
                deadline=_parse_date(get("Deadline", "")),
                time_est=float(get("TimeEst", "1") or 1),
                energy=(get("Energy", "medium") or "medium").strip().lower(),
                layer=get("Layer", "Support") or "Support",
                impact=float(get("Impact", "3") or 3),
                leverage=float(get("Leverage", "3") or 3),
                effort=float(get("Effort", "2") or 2),
                notes=get("Notes", ""),
            )
        )
    return tasks


def _tasks_from_json_bytes(data: bytes) -> List[Task]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Neplatný JSON: {e}")
    # JSON může být seznam úkolů, nebo {"tasks":[...]}
    items = payload.get("tasks", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise HTTPException(
            status_code=400, detail="JSON musí být seznam objektů nebo {'tasks': [...]}"
        )
    tasks: List[Task] = []
    from ..repositories import parse_date as _parse_date

    for it in items:
        if not isinstance(it, dict):
            raise HTTPException(
                status_code=400, detail="Každá položka musí být JSON objekt"
            )
        tasks.append(
            Task(
                title=it.get("Title", ""),
                owner=it.get("Owner", "já"),
                deadline=_parse_date(it.get("Deadline")),
                time_est=float(it.get("TimeEst", 1)),
                energy=(it.get("Energy", "medium") or "medium").strip().lower(),
                layer=it.get("Layer", "Support"),
                impact=float(it.get("Impact", 3)),
                leverage=float(it.get("Leverage", 3)),
                effort=float(it.get("Effort", 2)),
                notes=it.get("Notes", ""),
            )
        )
    return tasks


@app.get("/health")
def health() -> dict:
    """
    Health check endpoint.

    :return: JSON object with status information.
    :rtype: dict
    """
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
def process(payload: ProcessRequest) -> ProcessResponse:
    """
    Process tasks and return prioritized results.

    The request payload is validated via :class:`ProcessRequest`.
    Internally, the function:
    1. Builds a :class:`PriorityEngine` via :class:`ApiEngineFactory`.
    2. Maps input tasks (:class:`TaskIn`) to domain tasks (:class:`Task`).
    3. Applies pre-filters, scoring, and sorting.
    4. Optionally selects MITs.
    5. Returns the result as :class:`ProcessResponse`.

    :param payload: Request payload with tasks and optional parameters.
    :type payload: ProcessRequest
    :return: Prioritized tasks, optional MITs, and summary counts.
    :rtype: ProcessResponse
    """
    # Build engine
    engine = ApiEngineFactory.build(today=payload.today, alpha=payload.alpha)

    # Map TaskIn -> domain Task
    tasks: List[Task] = []
    for t in payload.tasks:
        tasks.append(
            Task(
                title=t.Title,
                owner=t.Owner,
                deadline=t.Deadline,
                time_est=t.TimeEst,
                energy=t.Energy,
                layer=t.Layer,
                impact=t.Impact,
                leverage=t.Leverage,
                effort=t.Effort,
                notes=t.Notes,
            )
        )

    # Process without physical I/O: use internal services only
    kept, delegated, dropped = engine.pre.filter(tasks)
    computed = [engine.computer.compute(x) for x in kept]
    sorted_tasks = engine.sorter.sort(computed)

    mits = []
    if payload.return_mits:
        mits = engine.mit_selector.select(sorted_tasks)

    def to_out(x: Task) -> TaskOut:
        """Map a domain :class:`Task` to an API output :class:`TaskOut`."""
        return TaskOut(
            Title=x.title,
            Owner=x.owner,
            Deadline=x.deadline,
            DaysToDeadline=x.days_to_deadline,
            TimeEst=x.time_est,
            Energy=x.energy,
            Layer=x.layer,
            Impact=x.impact,
            Leverage=x.leverage,
            Effort=x.effort,
            LayerWeight=round(x.layer_weight, 3),
            UM=round(x.um, 3),
            ImportanceCore=round(x.importance_core, 3),
            Score=round(x.score, 3),
            Quadrant=x.quadrant,
            Tag=x.tag,
            Notes=x.notes or "",
        )

    return ProcessResponse(
        prioritized=[to_out(x) for x in sorted_tasks],
        mits=[to_out(x) for x in mits] if payload.return_mits else None,
        counts={
            "total": len(tasks),
            "delegated": len(delegated),
            "dropped": len(dropped),
        },
    )


@app.post("/template", response_model=TemplateResponse)
def template() -> TemplateResponse:
    """
    Provide a sample template payload with example tasks.

    :return: Response containing example tasks to help clients
             understand the schema for `/process`.
    :rtype: TemplateResponse
    """
    samples = [
        TaskIn(
            Title="Nastavit zálohy",
            Owner="já",
            TimeEst=0.5,
            Energy="medium",
            Layer="Fundament",
            Impact=4,
            Leverage=3,
            Effort=2,
            Notes="Rclone + cron",
        ),
        TaskIn(
            Title="Automatizační skript",
            Owner="já",
            TimeEst=1.0,
            Energy="high",
            Layer="Strategic",
            Impact=5,
            Leverage=4,
            Effort=2,
        ),
        TaskIn(
            Title="Uklidit plochu",
            Owner="já",
            TimeEst=0.25,
            Energy="low",
            Layer="Support",
            Impact=2,
            Leverage=2,
            Effort=1,
        ),
        TaskIn(
            Title="Článek o ML",
            Owner="já",
            TimeEst=1.0,
            Energy="low",
            Layer="Leisure",
            Impact=1,
            Leverage=1,
            Effort=2,
        ),
    ]
    return TemplateResponse(tasks=samples)


@app.post("/process-file", response_model=ProcessResponse)
async def process_file(
    file: UploadFile = File(..., description="CSV nebo JSON soubor"),
    alpha: float = Form(0.7),
    today: date | None = Form(None),
    return_mits: bool = Form(True),
) -> ProcessResponse:
    raw = await file.read()
    repo = TabularTaskRepository()

    try:
        tasks = repo.load_from_bytes(
            raw,
            content_type=file.content_type,
            filename=file.filename,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Soubor se nepodařilo načíst: {e}")

    engine = ApiEngineFactory.build(today=today, alpha=alpha)

    kept, delegated, dropped = engine.pre.filter(tasks)
    computed = [engine.computer.compute(x) for x in kept]
    sorted_tasks = engine.sorter.sort(computed)
    mits = engine.mit_selector.select(sorted_tasks) if return_mits else []

    def to_out(x: Task) -> TaskOut:
        return TaskOut(
            Title=x.title,
            Owner=x.owner,
            Deadline=x.deadline,
            DaysToDeadline=x.days_to_deadline,
            TimeEst=x.time_est,
            Energy=x.energy,
            Layer=x.layer,
            Impact=x.impact,
            Leverage=x.leverage,
            Effort=x.effort,
            LayerWeight=round(x.layer_weight, 3),
            UM=round(x.um, 3),
            ImportanceCore=round(x.importance_core, 3),
            Score=round(x.score, 3),
            Quadrant=x.quadrant,
            Tag=x.tag,
            Notes=x.notes or "",
        )

    return ProcessResponse(
        prioritized=[to_out(x) for x in sorted_tasks],
        mits=[to_out(x) for x in mits] if return_mits else None,
        counts={
            "total": len(tasks),
            "delegated": len(delegated),
            "dropped": len(dropped),
        },
    )


def run() -> None:
    """
    Entrypoint for launching the API with uvicorn.

    Environment variables:
    - ``PRIO_API_HOST``: Host address (default: "127.0.0.1")
    - ``PRIO_API_PORT``: Port number (default: 8000)

    Example
    -------
    .. code-block:: bash

        export PRIO_API_HOST=0.0.0.0
        export PRIO_API_PORT=8080
        prio-api

    """
    import uvicorn

    host = os.getenv("PRIO_API_HOST", "127.0.0.1")
    port = int(os.getenv("PRIO_API_PORT", "8000"))
    uvicorn.run(
        "priority_engine.api.main:app",
        host=host,
        port=port,
        reload=False,
        factory=False,
    )

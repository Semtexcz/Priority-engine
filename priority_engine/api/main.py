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
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from typing import List

from .schemas import (
    ProcessRequest, ProcessResponse, TaskOut, TemplateResponse, TaskIn
)
from .factory import ApiEngineFactory
from ..models import Task

app = FastAPI(title="Priority Engine API", version="0.1.0")

# CORS – for local testing allow all origins; in production restrict domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


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
        tasks.append(Task(
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
        ))

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
        counts={"total": len(tasks), "delegated": len(delegated), "dropped": len(dropped)},
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
        TaskIn(Title="Nastavit zálohy", Owner="já", TimeEst=0.5, Energy="medium",
               Layer="Fundament", Impact=4, Leverage=3, Effort=2, Notes="Rclone + cron"),
        TaskIn(Title="Automatizační skript", Owner="já", TimeEst=1.0, Energy="high",
               Layer="Strategic", Impact=5, Leverage=4, Effort=2),
        TaskIn(Title="Uklidit plochu", Owner="já", TimeEst=0.25, Energy="low",
               Layer="Support", Impact=2, Leverage=2, Effort=1),
        TaskIn(Title="Článek o ML", Owner="já", TimeEst=1.0, Energy="low",
               Layer="Leisure", Impact=1, Leverage=1, Effort=2),
    ]
    return TemplateResponse(tasks=samples)


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
    uvicorn.run("priority_engine.api.main:app", host=host, port=port, reload=False, factory=False)

from __future__ import annotations
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, field_validator

# ====== Vstupní schémata ======

class TaskIn(BaseModel):
    """
    Input task sent by the client to the `/process` endpoint.

    :param Title: Task title.
    :param Owner: Responsible person. Defaults to `"já"`.
    :param Deadline: Task deadline in format `YYYY-MM-DD` or `null`.
    :param TimeEst: Estimated time in hours. Must be >= 0.
    :param Energy: Required energy level, one of `"low"`, `"medium"`, `"high"`.
    :param Layer: Task layer, one of `"Fundament"`, `"Strategic"`, `"Support"`, `"Leisure"`.
    :param Impact: Impact score from 0 to 5.
    :param Leverage: Leverage score from 0 to 5.
    :param Effort: Effort score, >= 1e-6, typically 1–5.
    :param Notes: Optional notes.
    """

    Title: str = Field(..., description="Task title")
    Owner: str = Field(default="já", description="Responsible person")
    Deadline: Optional[date] = Field(default=None, description="YYYY-MM-DD or null")
    TimeEst: float = Field(default=1.0, ge=0, description="Estimated time in hours")
    Energy: str = Field(default="medium", description="low/medium/high")
    Layer: str = Field(default="Support", description="Fundament|Strategic|Support|Leisure")
    Impact: float = Field(default=3.0, ge=0, le=5, description="0–5")
    Leverage: float = Field(default=3.0, ge=0, le=5, description="0–5")
    Effort: float = Field(default=2.0, ge=0.000001, description=">= ~0, typically 1–5")
    Notes: str = Field(default="", description="Notes")

    @field_validator("Energy")
    @classmethod
    def _energy_norm(cls, v: str) -> str:
        """
        Normalize the energy level string to lowercase.

        :param v: Input energy string.
        :return: Normalized string (`low`, `medium`, or `high`).
        """
        return (v or "medium").strip().lower()


class ProcessRequest(BaseModel):
    """
    Payload for `/process`: list of tasks and optional computation parameters.

    :param tasks: List of input tasks.
    :param alpha: Damping factor for Effort in denominator (> 0).
    :param today: Override for "today" (useful in testing).
    :param return_mits: Whether to include MITs in the response.
    """

    tasks: List[TaskIn]
    alpha: float = Field(default=0.7, gt=0, description="Damping factor for Effort in denominator")
    today: Optional[date] = Field(default=None, description="Override 'today' for tests")
    return_mits: bool = Field(default=True, description="Include MITs in output")


# ====== Výstupní schémata ======

class TaskOut(BaseModel):
    """
    Output task with computed prioritization fields.

    :param Title: Task title.
    :param Owner: Responsible person.
    :param Deadline: Deadline of the task.
    :param DaysToDeadline: Remaining days until deadline.
    :param TimeEst: Estimated time in hours.
    :param Energy: Energy level.
    :param Layer: Task layer.
    :param Impact: Impact score.
    :param Leverage: Leverage score.
    :param Effort: Effort score.
    :param LayerWeight: Computed layer weight.
    :param UM: Utility metric.
    :param ImportanceCore: Core importance value.
    :param Score: Final computed score.
    :param Quadrant: Eisenhower matrix quadrant.
    :param Tag: Tag such as `"BigBet"`, `"QuickWin"`, etc.
    :param Notes: Optional notes.
    """

    Title: str
    Owner: str
    Deadline: Optional[date]
    DaysToDeadline: Optional[int]
    TimeEst: float
    Energy: str
    Layer: str
    Impact: float
    Leverage: float
    Effort: float
    LayerWeight: float
    UM: float
    ImportanceCore: float
    Score: float
    Quadrant: str
    Tag: str
    Notes: str


class ProcessResponse(BaseModel):
    """
    Response of the `/process` endpoint.

    :param prioritized: List of prioritized tasks.
    :param mits: List of MIT tasks, if `return_mits=True`.
    :param counts: Summary counts (e.g. {"total": int, "delegated": int, "dropped": int}).
    """

    prioritized: List[TaskOut]
    mits: Optional[List[TaskOut]] = None
    counts: dict = Field(
        description="Summary counts: {'total': int, 'delegated': int, 'dropped': int}"
    )


class TemplateResponse(BaseModel):
    """
    Response containing a list of input tasks (template).

    :param tasks: List of input tasks.
    """

    tasks: List[TaskIn]

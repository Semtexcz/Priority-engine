from __future__ import annotations
from pathlib import Path
from datetime import date
import click
from .repositories import TabularTaskRepository
from .services import TaskPreFilter, TaskComputer, PriorityEngine
from .sorters import BacklogSorter
from .selectors import DefaultMITSelector
from .models import Task

@click.group(help="Priority Engine CLI — Eisenhower × Layers × Scoring")
def cli() -> None:
    ...

@cli.command("process", help="Zpracuj úkoly (CSV/JSON) a ulož CSV + volitelné MIT.md")
@click.option("--in", "in_path", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True)
@click.option("--out", "out_path", type=click.Path(dir_okay=False, path_type=Path), required=True)
@click.option("--mits-out", "mits_out", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--today", type=str, default=None, help="YYYY-MM-DD (přepis dneška)")
def process_cmd(in_path: Path, out_path: Path, mits_out: Path | None, today: str | None) -> None:
    today_dt = date.fromisoformat(today) if today else None
    engine = PriorityEngine(
        repo=TabularTaskRepository(),
        computer=TaskComputer(today=today_dt),
        pre=TaskPreFilter(),
        sorter=BacklogSorter(),
        mit_selector=DefaultMITSelector(),
    )
    sorted_tasks, delegated, dropped, mits = engine.process(in_path, out_path, mits_out)
    click.echo(f"Zpracováno: {len(sorted_tasks)} | Delegováno: {len(delegated)} | Archivováno: {len(dropped)}")
    click.echo(f"Výstup: {out_path}")
    if mits_out: click.echo(f"MIT: {mits_out}")

@cli.command("template", help="Vytvoř ukázkový CSV vstup")
@click.option("--out", "out_path", type=click.Path(dir_okay=False, path_type=Path), required=True)
def template_cmd(out_path: Path) -> None:
    samples = [
        Task(title="Nastavit zálohy", time_est=0.5, layer="Fundament", impact=4, leverage=3, effort=2, notes="Rclone+cron"),
        Task(title="Automatizační skript", time_est=1.0, layer="Strategic", impact=5, leverage=4, effort=2),
        Task(title="Uklidit plochu", time_est=0.25, layer="Support", impact=2, leverage=2, effort=1),
        Task(title="Článek o ML", time_est=1.0, layer="Leisure", impact=1, leverage=1, effort=2),
    ]
    repo = TabularTaskRepository()
    repo.dump_csv(out_path, samples)
    click.echo(f"Ukázka: {out_path}")

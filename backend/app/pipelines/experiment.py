import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Task, Experiment
from app.gateway.llm_gateway import gateway
from app.core.config import DATA_DIR


async def upload_experiment_log(
    task_id: int,
    log_content: str,
    filename: str,
    session: AsyncSession,
) -> Experiment:
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise ValueError(f"Task {task_id} not found")

    exp_dir = DATA_DIR / "tasks" / f"task-{task_id}" / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)

    log_path = exp_dir / filename
    log_path.write_text(log_content, encoding="utf-8")

    experiment = Experiment(
        task_id=task_id,
        log_path=str(log_path),
    )
    session.add(experiment)
    await session.commit()
    return experiment


async def analyze_experiment(
    experiment_id: int,
    session: AsyncSession,
) -> str:
    result = await session.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise ValueError(f"Experiment {experiment_id} not found")

    log_path = Path(experiment.log_path)
    if not log_path.exists():
        raise ValueError("Log file not found")

    log_content = log_path.read_text(encoding="utf-8")

    llm_result = await gateway.call_async("experiment_analysis", {
        "log_data": log_content[:12000],
    })

    report = llm_result.get("report", llm_result.get("raw", ""))
    experiment.analysis_report = report
    session.add(experiment)
    await session.commit()
    return report

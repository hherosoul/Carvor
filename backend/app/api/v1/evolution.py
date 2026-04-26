from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.models.database import EvolutionLog
from app.pipelines.evolution import confirm_evolution, rollback_evolution

router = APIRouter(prefix="/api/evolution-logs", tags=["evolution"])


@router.get("")
async def list_evolution_logs(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(EvolutionLog).order_by(EvolutionLog.created_at.desc())
    )
    logs = result.scalars().all()
    return [{
        "id": l.id,
        "content": l.content,
        "source": l.source,
        "dimension": l.dimension,
        "level": l.level,
        "skill_name": l.skill_name,
        "created_at": l.created_at,
    } for l in logs]


@router.delete("/{log_id}")
async def delete_evolution(log_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(EvolutionLog).where(EvolutionLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(404, "Evolution log not found")
    await session.delete(log)
    await session.commit()
    return {"ok": True}


@router.post("/{log_id}/confirm")
async def confirm_evolution_log(log_id: int, session: AsyncSession = Depends(get_session)):
    compressed = await confirm_evolution(log_id, session)
    return {"ok": True, "compressed": compressed}


@router.post("/{log_id}/rollback")
async def rollback_evolution_log(log_id: int, session: AsyncSession = Depends(get_session)):
    await rollback_evolution(log_id, session)
    return {"ok": True}

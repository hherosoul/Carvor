from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.models.database import OperationLog

router = APIRouter(prefix="/api/operation-logs", tags=["operation-logs"])


@router.get("")
async def list_operation_logs(
    page: int = 1,
    size: int = 50,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(OperationLog).order_by(OperationLog.timestamp.desc())
        .offset((page - 1) * size).limit(size)
    )
    logs = result.scalars().all()
    return [{
        "id": l.id,
        "operation_type": l.operation_type,
        "operation_object": l.operation_object,
        "result": l.result,
        "timestamp": l.timestamp,
    } for l in logs]

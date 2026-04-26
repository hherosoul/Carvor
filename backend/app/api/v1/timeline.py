import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.core.database import get_session
from app.models.database import Paper, PaperLibraryAssoc

logger = logging.getLogger("carvor.timeline")

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


def _week_range(week_str: str) -> dict:
    try:
        parts = week_str.split("-W")
        year = int(parts[0])
        week_num = int(parts[1])
        jan1 = datetime(year, 1, 1)
        jan1_weekday = jan1.weekday()
        first_monday = jan1 + timedelta(days=(7 - jan1_weekday) % 7)
        if week_num == 0:
            start_of_week = jan1
        else:
            start_of_week = first_monday + timedelta(weeks=week_num - 1)
        end_of_week = start_of_week + timedelta(days=6)
        return {
            "start": start_of_week.strftime("%m-%d"),
            "end": end_of_week.strftime("%m-%d"),
            "full_start": start_of_week.strftime("%Y-%m-%d"),
            "full_end": end_of_week.strftime("%Y-%m-%d"),
        }
    except Exception:
        return {"start": "", "end": "", "full_start": "", "full_end": ""}


@router.get("")
async def get_timeline(library_id: int = Query(...), session: AsyncSession = Depends(get_session)):
    logger.info(f"Getting timeline for library_id={library_id}")
    effective_date = case(
        (Paper.published_date.isnot(None), Paper.published_date),
        (Paper.published_date != "", Paper.published_date),
        else_=Paper.created_at,
    )
    result = await session.execute(
        select(
            func.strftime("%Y-W%W", effective_date).label("week"),
            func.count(Paper.id).label("count"),
        )
        .join(PaperLibraryAssoc, PaperLibraryAssoc.paper_id == Paper.id)
        .where(PaperLibraryAssoc.library_id == library_id)
        .group_by("week")
        .order_by("week")
    )
    weeks = result.all()
    logger.info(f"Timeline returned {len(weeks)} weeks")
    return [{"week": w.week, "count": w.count, **_week_range(w.week)} for w in weeks]


@router.get("/week/{week}")
async def get_week_papers(
    week: str,
    library_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
):
    logger.info(f"Getting papers for week={week}, library_id={library_id}")
    effective_date = case(
        (Paper.published_date.isnot(None), Paper.published_date),
        (Paper.published_date != "", Paper.published_date),
        else_=Paper.created_at,
    )
    result = await session.execute(
        select(Paper, PaperLibraryAssoc)
        .join(PaperLibraryAssoc, PaperLibraryAssoc.paper_id == Paper.id)
        .where(PaperLibraryAssoc.library_id == library_id)
        .where(func.strftime("%Y-W%W", effective_date) == week)
        .order_by(Paper.created_at.desc())
    )
    rows = result.all()
    logger.info(f"Week {week} has {len(rows)} papers")
    return [{
        "id": p.id,
        "title": p.title,
        "authors": p.authors,
        "institution": p.institution or "",
        "abstract": p.abstract or "",
        "structured_summary": p.structured_summary or "",
        "source": p.source,
        "published_date": p.published_date or p.created_at or "",
        "source_url": p.source_url or "",
        "is_read": a.is_read,
        "is_interested": a.is_interested,
    } for p, a in rows]

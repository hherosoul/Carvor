import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_session
from app.models.database import PaperNote, Paper
from app.gateway.llm_gateway import gateway

logger = logging.getLogger("carvor.notes")

router = APIRouter(prefix="/api/notes", tags=["notes"])


class NoteCreate(BaseModel):
    content: str


@router.get("")
async def list_notes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(PaperNote, Paper)
        .join(Paper, Paper.id == PaperNote.paper_id)
        .order_by(PaperNote.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = result.all()
    return [{
        "id": n.id,
        "paper_id": n.paper_id,
        "paper_title": p.title,
        "content": n.content,
        "created_at": n.created_at,
    } for n, p in rows]


@router.post("")
async def create_note(data: NoteCreate, paper_id: int = Query(...), session: AsyncSession = Depends(get_session)):
    paper = await session.execute(select(Paper).where(Paper.id == paper_id))
    if not paper.scalar_one_or_none():
        raise HTTPException(404, "Paper not found")
    note = PaperNote(paper_id=paper_id, content=data.content)
    session.add(note)
    await session.commit()
    await session.flush()
    return {"ok": True, "id": note.id}


@router.get("/{note_id}")
async def get_note(note_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(PaperNote, Paper)
        .join(Paper, Paper.id == PaperNote.paper_id)
        .where(PaperNote.id == note_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Note not found")
    n, p = row
    return {
        "id": n.id,
        "paper_id": n.paper_id,
        "paper_title": p.title,
        "content": n.content,
        "created_at": n.created_at,
    }


@router.delete("/{note_id}")
async def delete_note(note_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PaperNote).where(PaperNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(404, "Note not found")
    await session.delete(note)
    await session.commit()
    return {"ok": True}


class NoteOptimizeRequest(BaseModel):
    content: str
    paper_title: str = ""


@router.post("/optimize")
async def optimize_note(data: NoteOptimizeRequest):
    try:
        result = await gateway.call_async("note_optimize", {
            "note_content": data.content,
            "paper_title": data.paper_title,
        })
        return {"optimized_note": result.get("optimized_note", data.content)}
    except Exception as e:
        logger.warning(f"Note optimization failed: {e}")
        return {"optimized_note": data.content}

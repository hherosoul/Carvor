from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_session
from app.models.database import Idea, IdeaReference
from app.pipelines.idea import create_idea, analyze_idea, chat_idea, add_idea_reference, update_idea_status

router = APIRouter(prefix="/api/ideas", tags=["ideas"])


class IdeaCreate(BaseModel):
    title: str
    content: str | None = None


class IdeaUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class StatusUpdate(BaseModel):
    status: str


class RefPaper(BaseModel):
    paper_id: int


@router.get("")
async def list_ideas(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Idea).order_by(Idea.updated_at.desc()))
    ideas = result.scalars().all()
    return [{"id": i.id, "title": i.title, "status": i.status, "created_at": i.created_at, "updated_at": i.updated_at} for i in ideas]


@router.post("")
async def create_new_idea(data: IdeaCreate, session: AsyncSession = Depends(get_session)):
    idea = await create_idea(data.title, data.content or "", session)
    return {"id": idea.id, "title": idea.title, "content": idea.content, "status": idea.status}


@router.get("/{idea_id}")
async def get_idea(idea_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(404, "Idea not found")
    return {"id": idea.id, "title": idea.title, "content": idea.content, "status": idea.status, "created_at": idea.created_at}


@router.put("/{idea_id}")
async def update_idea(idea_id: int, data: IdeaUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(404, "Idea not found")
    if data.title is not None:
        idea.title = data.title
    if data.content is not None:
        idea.content = data.content
    session.add(idea)
    await session.commit()
    return {"id": idea.id, "title": idea.title, "content": idea.content}


@router.put("/{idea_id}/status")
async def update_status(idea_id: int, data: StatusUpdate, session: AsyncSession = Depends(get_session)):
    idea = await update_idea_status(idea_id, data.status, session)
    return {"id": idea.id, "status": idea.status}


@router.post("/{idea_id}/ref-paper")
async def add_reference(idea_id: int, data: RefPaper, session: AsyncSession = Depends(get_session)):
    await add_idea_reference(idea_id, data.paper_id, session)
    return {"ok": True}


@router.delete("/{idea_id}")
async def delete_idea(idea_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(404, "Idea not found")
    await session.delete(idea)
    await session.commit()
    return {"ok": True}

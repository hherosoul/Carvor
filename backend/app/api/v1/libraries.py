from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_session
from app.models.database import PaperLibrary, Paper, PaperLibraryAssoc

router = APIRouter(prefix="/api/libraries", tags=["libraries"])


class LibraryCreate(BaseModel):
    name: str
    domain_description: str


class LibraryUpdate(BaseModel):
    name: str | None = None
    domain_description: str | None = None


@router.get("")
async def list_libraries(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PaperLibrary))
    libraries = result.scalars().all()
    if not libraries:
        default = PaperLibrary(name="默认论文库", domain_description="")
        session.add(default)
        await session.commit()
        await session.refresh(default)
        libraries = [default]
    return [{"id": l.id, "name": l.name, "domain_description": l.domain_description, "created_at": l.created_at} for l in libraries]


@router.post("")
async def create_library(data: LibraryCreate, session: AsyncSession = Depends(get_session)):
    library = PaperLibrary(name=data.name, domain_description=data.domain_description)
    session.add(library)
    await session.commit()
    return {"id": library.id, "name": library.name, "domain_description": library.domain_description}


@router.put("/{library_id}")
async def update_library(library_id: int, data: LibraryUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PaperLibrary).where(PaperLibrary.id == library_id))
    library = result.scalar_one_or_none()
    if not library:
        raise HTTPException(404, "Library not found")
    if data.name is not None:
        library.name = data.name
    if data.domain_description is not None:
        library.domain_description = data.domain_description
    session.add(library)
    await session.commit()
    return {"id": library.id, "name": library.name, "domain_description": library.domain_description}


@router.delete("/{library_id}")
async def delete_library(library_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PaperLibrary).where(PaperLibrary.id == library_id))
    library = result.scalar_one_or_none()
    if not library:
        raise HTTPException(404, "Library not found")
    await session.delete(library)
    await session.commit()
    return {"ok": True}

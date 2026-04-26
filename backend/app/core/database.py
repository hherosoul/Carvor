from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from pathlib import Path

from app.models.database import Base
from app.core.config import DB_PATH, DATA_DIR, SKILLS_DIR, CONFIG_DIR


engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    for skill_name in ["文献跟踪", "idea锤炼", "代码提示词生成", "论文润色"]:
        skill_dir = SKILLS_DIR / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        for fname in ["SKILL.md", "candidate.md", "observing.md"]:
            fpath = skill_dir / fname
            if not fpath.exists():
                fpath.write_text("", encoding="utf-8")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

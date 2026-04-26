import json
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import PaperLibrary, Paper, PaperLibraryAssoc
from app.gateway.llm_gateway import gateway

logger = logging.getLogger("carvor.paper_search")


async def search_pipelines(library_id: int, session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(PaperLibrary).where(PaperLibrary.id == library_id)
    )
    library = result.scalar_one_or_none()
    if not library:
        raise ValueError(f"Paper library {library_id} not found")

    logger.info(f"Starting paper search for library '{library.name}' (id={library_id})")

    llm_result = await gateway.call_async("paper_search", {
        "domain_description": library.domain_description,
        "task": "搜索领域及强相关领域的最新论文，筛选与领域描述高度相关的论文（错过好过泛滥），生成结构化摘要（≤200字，非一句话）",
    })

    papers_data = llm_result.get("papers", [])
    logger.info(f"LLM returned {len(papers_data)} papers")

    saved = []
    for p in papers_data:
        existing = await session.execute(
            select(Paper).where(
                Paper.title == p.get("title", ""),
                Paper.source_url == p.get("source_url", ""),
            )
        )
        if existing.scalar_one_or_none():
            logger.debug(f"Skipping duplicate paper: {p.get('title', '')}")
            continue

        published_date = p.get("published_date", "")
        if not published_date:
            published_date = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")

        paper = Paper(
            title=p.get("title", ""),
            authors=json.dumps(p.get("authors", []), ensure_ascii=False),
            institution=p.get("institution", ""),
            abstract=p.get("abstract", ""),
            structured_summary=p.get("summary", ""),
            keywords=json.dumps(p.get("keywords", []), ensure_ascii=False),
            source="llm_search",
            published_date=published_date,
            source_url=p.get("source_url", ""),
        )
        session.add(paper)
        await session.flush()

        assoc = PaperLibraryAssoc(
            paper_id=paper.id,
            library_id=library_id,
        )
        session.add(assoc)
        saved.append({
            "id": paper.id,
            "title": paper.title,
            "summary": paper.structured_summary,
        })
        logger.info(f"Saved paper: {paper.title} (id={paper.id})")

    await session.commit()
    logger.info(f"Paper search complete: {len(saved)} new papers saved")
    return saved

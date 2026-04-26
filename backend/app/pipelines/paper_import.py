import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Paper, PaperLibraryAssoc
from app.gateway.llm_gateway import gateway
from app.core.config import DATA_DIR

logger = logging.getLogger("carvor.paper_import")


async def import_pdf(library_id: int, pdf_path: str, session: AsyncSession) -> Paper:
    from PyPDF2 import PdfReader

    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    title = Path(pdf_path).stem
    authors_json = "[]"
    institution = ""
    abstract = ""
    structured_summary = ""
    keywords_json = "[]"

    if text.strip():
        try:
            metadata_result = await gateway.call_async("paper_metadata", {
                "pdf_text": text[:8000],
            })
            title = metadata_result.get("title", title)
            authors_json = json.dumps(metadata_result.get("authors", []), ensure_ascii=False)
            institution = metadata_result.get("institution", "")
            abstract = metadata_result.get("abstract", "")
            keywords_json = json.dumps(metadata_result.get("keywords", []), ensure_ascii=False)

            summary_result = await gateway.call_async("paper_metadata", {
                "paper_metadata": metadata_result,
                "task": "基于论文元数据生成结构化摘要（≤200字，非一句话）",
            })
            structured_summary = summary_result.get("summary", "")
        except Exception as e:
            logger.warning(f"LLM metadata extraction failed, using basic info: {e}")

    existing = await session.execute(
        select(Paper).where(Paper.title == title)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Paper with title '{title}' already exists")

    paper_dir = DATA_DIR / "paper_libraries" / f"lib-{library_id}" / "papers"
    paper_dir.mkdir(parents=True, exist_ok=True)
    dest = paper_dir / Path(pdf_path).name
    if str(Path(pdf_path).resolve()) != str(dest.resolve()):
        import shutil
        shutil.copy2(pdf_path, dest)

    paper = Paper(
        title=title,
        authors=authors_json,
        institution=institution,
        abstract=abstract,
        structured_summary=structured_summary,
        keywords=keywords_json,
        source="manual",
        pdf_path=str(dest),
        published_date=datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"),
    )
    session.add(paper)
    await session.flush()

    assoc = PaperLibraryAssoc(
        paper_id=paper.id,
        library_id=library_id,
    )
    session.add(assoc)
    await session.commit()
    return paper

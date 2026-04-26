from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Paper, Conversation, ConversationMessage
from app.gateway.llm_gateway import gateway


async def start_deep_reading(paper_id: int, session: AsyncSession) -> dict:
    result = await session.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise ValueError(f"Paper {paper_id} not found")
    if not paper.pdf_path:
        raise ValueError("Paper full text not downloaded yet")

    return {"paper_id": paper.id, "title": paper.title}


async def chat_deep_reading(
    paper_id: int,
    question: str,
    conversation_id: int | None,
    session: AsyncSession,
) -> tuple[AsyncGenerator[str, None], int]:
    result = await session.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise ValueError(f"Paper {paper_id} not found")

    if conversation_id is None:
        conv = Conversation(scenario="deep_reading_chat")
        session.add(conv)
        await session.flush()
        conversation_id = conv.id

        msg = ConversationMessage(
            conversation_id=conversation_id,
            role="user",
            content=f"论文全文：{paper.abstract or ''}",
        )
        session.add(msg)
        await session.flush()

    msg = ConversationMessage(
        conversation_id=conversation_id,
        role="user",
        content=question,
    )
    session.add(msg)
    await session.commit()

    context_msgs = await _load_context(conversation_id, session)

    stream = gateway.call_stream("deep_reading_chat", {
        "paper_title": paper.title,
        "question": question,
    }, context=context_msgs)

    return stream, conversation_id


async def summarize_deep_reading(
    paper_id: int,
    conversation_id: int,
    session: AsyncSession,
) -> str:
    result = await session.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise ValueError(f"Paper {paper_id} not found")

    context_msgs = await _load_context(conversation_id, session)
    conversation_text = "\n".join(m["content"] for m in context_msgs if m["role"] in ("user", "assistant"))

    llm_result = await gateway.call_async("deep_reading_summary", {
        "conversation": conversation_text,
    })

    summary = llm_result.get("summary", "")
    paper.deep_reading_summary = summary
    session.add(paper)
    await session.commit()
    return summary


async def _load_context(conversation_id: int, session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.timestamp)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages]

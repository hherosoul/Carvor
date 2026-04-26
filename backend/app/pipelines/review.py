from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Task, TaskReference, Paper, Conversation, ConversationMessage
from app.gateway.llm_gateway import gateway


async def discuss_review(
    task_id: int,
    user_input: str,
    conversation_id: int | None,
    session: AsyncSession,
    existing_content: str = "",
) -> tuple[AsyncGenerator[str, None], int]:
    task = await _get_task(task_id, session)
    refs = await _get_task_references(task_id, session)

    if conversation_id is None:
        conv = Conversation(task_id=task_id, scenario="review_discuss")
        session.add(conv)
        await session.flush()
        conversation_id = conv.id

    msg = ConversationMessage(
        conversation_id=conversation_id,
        role="user",
        content=user_input,
    )
    session.add(msg)
    await session.commit()

    context_msgs = await _load_context(conversation_id, session)

    input_data = {
        "task_name": task.name,
        "research_goal": task.research_goal or "",
        "references": refs,
        "user_input": user_input,
    }
    if existing_content:
        input_data["existing_content"] = existing_content

    stream = gateway.call_stream("review_discuss", input_data, context=context_msgs)

    return stream, conversation_id


async def generate_review(
    task_id: int,
    conversation_id: int,
    session: AsyncSession,
) -> AsyncGenerator[str, None]:
    task = await _get_task(task_id, session)
    refs = await _get_task_references(task_id, session)
    context_msgs = await _load_context(conversation_id, session)

    return gateway.call_stream("review_generate", {
        "task_name": task.name,
        "research_goal": task.research_goal or "",
        "references": refs,
        "conversation": "\n".join(m["content"] for m in context_msgs if m["role"] in ("user", "assistant")),
    })


async def _get_task(task_id: int, session: AsyncSession) -> Task:
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise ValueError(f"Task {task_id} not found")
    return task


async def _get_task_references(task_id: int, session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(TaskReference).where(TaskReference.task_id == task_id)
    )
    refs = result.scalars().all()
    ref_data = []
    for ref in refs:
        paper_result = await session.execute(select(Paper).where(Paper.id == ref.paper_id))
        paper = paper_result.scalar_one_or_none()
        if paper:
            ref_data.append({
                "title": paper.title,
                "abstract": paper.abstract or "",
                "bibtex": ref.bibtex or "",
            })
    return ref_data


async def _load_context(conversation_id: int, session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.timestamp)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages]

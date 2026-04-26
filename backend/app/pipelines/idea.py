from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Idea, IdeaReference, Paper, Conversation, ConversationMessage
from app.gateway.llm_gateway import gateway


async def create_idea(title: str, content: str, session: AsyncSession) -> Idea:
    idea = Idea(title=title, content=content)
    session.add(idea)
    await session.commit()
    return idea


async def analyze_idea(
    idea_id: int,
    conversation_id: int | None,
    session: AsyncSession,
) -> tuple[AsyncGenerator[str, None], int]:
    result = await session.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise ValueError(f"Idea {idea_id} not found")

    if conversation_id is None:
        conv = Conversation(scenario="idea_analysis")
        session.add(conv)
        await session.flush()
        conversation_id = conv.id

    stream = gateway.call_stream("idea_analysis", {
        "idea_title": idea.title,
        "idea_content": idea.content or "",
    })

    return stream, conversation_id


async def chat_idea(
    idea_id: int,
    user_input: str,
    conversation_id: int,
    session: AsyncSession,
) -> AsyncGenerator[str, None]:
    result = await session.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise ValueError(f"Idea {idea_id} not found")

    msg = ConversationMessage(
        conversation_id=conversation_id,
        role="user",
        content=user_input,
    )
    session.add(msg)
    await session.commit()

    context_msgs = await _load_idea_context(conversation_id, session)

    return gateway.call_stream("idea_chat", {
        "idea_title": idea.title,
        "idea_content": idea.content or "",
        "user_input": user_input,
    }, context=context_msgs)


async def add_idea_reference(idea_id: int, paper_id: int, session: AsyncSession) -> None:
    ref = IdeaReference(idea_id=idea_id, paper_id=paper_id)
    session.add(ref)
    await session.commit()


async def update_idea_status(idea_id: int, status: str, session: AsyncSession) -> Idea:
    result = await session.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise ValueError(f"Idea {idea_id} not found")
    idea.status = status
    session.add(idea)
    await session.commit()
    return idea


async def _load_idea_context(conversation_id: int, session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.timestamp)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages]

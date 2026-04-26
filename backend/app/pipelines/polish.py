from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Task, Conversation, ConversationMessage
from app.pipelines.review import _get_task, _load_context
from app.gateway.llm_gateway import gateway


async def polish_paper(
    task_id: int,
    original_text: str,
    conversation_id: int | None,
    session: AsyncSession,
    existing_content: str = "",
) -> tuple[AsyncGenerator[str, None], int]:
    task = await _get_task(task_id, session)

    if conversation_id is None:
        conv = Conversation(task_id=task_id, scenario="paper_polish")
        session.add(conv)
        await session.flush()
        conversation_id = conv.id

    msg = ConversationMessage(
        conversation_id=conversation_id,
        role="user",
        content=f"请润色以下文本：\n{original_text}",
    )
    session.add(msg)
    await session.commit()

    context_msgs = await _load_context(conversation_id, session)

    input_data = {
        "original_text": original_text,
        "task_name": task.name,
    }
    if existing_content:
        input_data["existing_content"] = existing_content

    stream = gateway.call_stream("paper_polish", input_data, context=context_msgs)

    return stream, conversation_id

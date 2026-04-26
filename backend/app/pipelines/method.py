from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Task, Conversation, ConversationMessage
from app.pipelines.review import _get_task, _get_task_references, _load_context
from app.gateway.llm_gateway import gateway


async def discuss_method(
    task_id: int,
    user_input: str,
    conversation_id: int | None,
    session: AsyncSession,
    existing_content: str = "",
) -> tuple[AsyncGenerator[str, None], int]:
    task = await _get_task(task_id, session)
    refs = await _get_task_references(task_id, session)

    if conversation_id is None:
        conv = Conversation(task_id=task_id, scenario="method_discuss")
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

    stream = gateway.call_stream("method_discuss", input_data, context=context_msgs)

    return stream, conversation_id


async def generate_method(
    task_id: int,
    conversation_id: int,
    session: AsyncSession,
) -> AsyncGenerator[str, None]:
    task = await _get_task(task_id, session)
    refs = await _get_task_references(task_id, session)
    context_msgs = await _load_context(conversation_id, session)

    return gateway.call_stream("method_generate", {
        "task_name": task.name,
        "research_goal": task.research_goal or "",
        "references": refs,
        "conversation": "\n".join(m["content"] for m in context_msgs if m["role"] in ("user", "assistant")),
    })

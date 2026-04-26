from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Task, Conversation, ConversationMessage
from app.pipelines.review import _get_task, _load_context
from app.gateway.llm_gateway import gateway
from app.core.config import DATA_DIR


async def generate_prompt_doc(
    task_id: int,
    user_input: str,
    conversation_id: int | None,
    session: AsyncSession,
    existing_content: str = "",
) -> tuple[AsyncGenerator[str, None], int]:
    task = await _get_task(task_id, session)

    research_doc = _load_research_doc(task_id)

    if conversation_id is None:
        conv = Conversation(task_id=task_id, scenario="prompt_doc_generate")
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
        "research_doc": research_doc,
        "user_input": user_input,
    }
    if existing_content:
        input_data["existing_content"] = existing_content

    stream = gateway.call_stream("prompt_doc_generate", input_data, context=context_msgs)

    return stream, conversation_id


async def save_prompt_doc(task_id: int, content: str, filename: str) -> str:
    doc_dir = DATA_DIR / "tasks" / f"task-{task_id}" / "prompt-docs"
    doc_dir.mkdir(parents=True, exist_ok=True)
    path = doc_dir / filename
    path.write_text(content, encoding="utf-8")
    return str(path)


def _load_research_doc(task_id: int) -> str:
    path = DATA_DIR / "tasks" / f"task-{task_id}" / "research.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

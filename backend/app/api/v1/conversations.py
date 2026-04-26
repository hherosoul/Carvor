from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.models.database import Conversation, ConversationMessage

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/{conversation_id}/messages")
async def get_messages(conversation_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.timestamp)
    )
    messages = result.scalars().all()
    return [{
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "timestamp": m.timestamp,
    } for m in messages]


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(404, "Conversation not found")
    await session.delete(conv)
    await session.commit()
    return {"ok": True}

import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.pipelines.deep_reading import chat_deep_reading
from app.pipelines.idea import chat_idea
from app.pipelines.review import discuss_review
from app.pipelines.method import discuss_method
from app.pipelines.prompt_doc import generate_prompt_doc
from app.pipelines.polish import polish_paper

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger("carvor.chat")


class ChatRequest(BaseModel):
    scenario: str
    entity_id: int
    user_input: str
    conversation_id: int | None = None
    existing_content: str = ""


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def chat_stream(req: ChatRequest, session: AsyncSession = Depends(get_session)):
    async def generate():
        try:
            stream = None
            conv_id = None

            if req.scenario == "deep_reading":
                stream, conv_id = await chat_deep_reading(
                    paper_id=req.entity_id,
                    question=req.user_input,
                    conversation_id=req.conversation_id,
                    session=session,
                )
            elif req.scenario in ("idea_refine", "idea"):
                stream = await chat_idea(
                    idea_id=req.entity_id,
                    user_input=req.user_input,
                    conversation_id=req.conversation_id,
                    session=session,
                )
            elif req.scenario == "review":
                stream, conv_id = await discuss_review(
                    task_id=req.entity_id,
                    user_input=req.user_input,
                    conversation_id=req.conversation_id,
                    existing_content=req.existing_content,
                    session=session,
                )
            elif req.scenario == "method":
                stream, conv_id = await discuss_method(
                    task_id=req.entity_id,
                    user_input=req.user_input,
                    conversation_id=req.conversation_id,
                    existing_content=req.existing_content,
                    session=session,
                )
            elif req.scenario == "prompt_doc":
                stream, conv_id = await generate_prompt_doc(
                    task_id=req.entity_id,
                    user_input=req.user_input,
                    conversation_id=req.conversation_id,
                    existing_content=req.existing_content,
                    session=session,
                )
            elif req.scenario == "polish":
                stream, conv_id = await polish_paper(
                    task_id=req.entity_id,
                    original_text=req.user_input,
                    conversation_id=req.conversation_id,
                    existing_content=req.existing_content,
                    session=session,
                )
            else:
                yield _sse_event("error", {"message": f"Unknown scenario: {req.scenario}"})
                return

            if conv_id:
                yield _sse_event("conversation.created", {"conversation_id": conv_id})

            if stream:
                async for chunk in stream:
                    yield _sse_event("chunk", {"content": chunk})

            yield _sse_event("done", {})

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(generate(), media_type="text/event-stream")

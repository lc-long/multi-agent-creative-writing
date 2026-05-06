import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from enum import Enum

from app.services.orchestrator import get_orchestrator
from app.models.story import SessionStatus

logger = logging.getLogger(__name__)

router = APIRouter()


class Genre(str, Enum):
    SCIENCE_FICTION = "science_fiction"
    FANTASY = "fantasy"
    REALISM = "realism"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    HORROR = "horror"
    ADVENTURE = "adventure"
    HISTORICAL = "historical"


class StoryCreateRequest(BaseModel):
    theme: str = Field(..., description="故事主题", min_length=1, max_length=500)
    genre: Optional[Genre] = Field(None, description="故事类型")
    constraints: Optional[dict] = Field(None, description="其他约束条件")


class StoryResponse(BaseModel):
    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="状态")
    message: str = Field(..., description="消息")


class StoryDetailResponse(BaseModel):
    session_id: str
    status: str
    story: Optional[dict] = None
    progress_messages: Optional[list] = None


@router.post("", response_model=StoryResponse, summary="创建故事")
async def create_story(request: StoryCreateRequest):
    orchestrator = get_orchestrator()
    session = await orchestrator.create_session(
        theme=request.theme,
        genre=request.genre.value if request.genre else None,
        constraints=request.constraints,
    )
    return StoryResponse(
        session_id=session.id,
        status=session.status.value,
        message="Story generation session created.",
    )


@router.get("/{session_id}", response_model=StoryDetailResponse, summary="获取故事")
async def get_story(session_id: str):
    orchestrator = get_orchestrator()
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    story_data = None
    if session.story:
        story_data = {
            "title": session.story.title,
            "genre": session.story.genre,
            "synopsis": session.story.synopsis,
            "outline": session.story.outline.dict() if session.story.outline else None,
            "characters": [c.dict() for c in session.story.characters],
            "dialogues": [d.dict() for d in session.story.dialogues],
            "world_setting": session.story.world_setting.dict() if session.story.world_setting else None,
        }

    return StoryDetailResponse(
        session_id=session.id,
        status=session.status.value,
        story=story_data,
        progress_messages=session.progress_messages if session.progress_messages else [],
    )


@router.get("/{session_id}/stream", summary="流式获取生成过程")
async def stream_story(session_id: str):
    orchestrator = get_orchestrator()
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        async for event in orchestrator.generate_story_stream(session_id):
            # Embed type inside data JSON to avoid SSE named event issues
            # (JS EventSource.onmessage only fires for unnamed events)
            payload = json.dumps(event, ensure_ascii=False)
            yield f"data: {payload}\n\n"

        yield "data: {\"type\":\"end\",\"data\":{}}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

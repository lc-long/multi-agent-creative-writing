"""
Stories API Endpoints

故事相关的API接口。
"""

import json
import logging
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from enum import Enum

from app.services.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


class Genre(str, Enum):
    """故事类型枚举"""
    SCIENCE_FICTION = "science_fiction"
    FANTASY = "fantasy"
    REALISM = "realism"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    HORROR = "horror"
    ADVENTURE = "adventure"
    HISTORICAL = "historical"


class StoryCreateRequest(BaseModel):
    """创建故事请求"""
    theme: str = Field(..., description="故事主题", min_length=1, max_length=500)
    genre: Optional[Genre] = Field(None, description="故事类型")
    constraints: Optional[dict] = Field(None, description="其他约束条件")


class StoryResponse(BaseModel):
    """故事响应"""
    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="状态")
    message: str = Field(..., description="消息")


class StoryDetailResponse(BaseModel):
    """故事详情响应"""
    session_id: str
    status: str
    story: Optional[dict] = None
    discussion: Optional[list] = None


@router.post("", response_model=StoryResponse, summary="创建故事")
async def create_story(request: StoryCreateRequest):
    """
    创建新故事（触发Agent协作生成）
    """
    orchestrator = get_orchestrator()
    
    session = await orchestrator.create_session(
        theme=request.theme,
        genre=request.genre.value if request.genre else None,
        constraints=request.constraints,
    )
    
    return StoryResponse(
        session_id=session.id,
        status=session.status.value,
        message="Story generation session created. Use the session_id to start generation.",
    )


@router.post("/{session_id}/generate", response_model=StoryResponse, summary="开始生成故事")
async def generate_story(session_id: str):
    """
    开始生成故事
    """
    orchestrator = get_orchestrator()
    
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = await orchestrator.generate_story(session_id)
    except Exception as e:
        logger.error(f"Story generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return StoryResponse(
        session_id=session.id,
        status=session.status.value,
        message="Story generation completed" if session.status.value == "completed" else "Story generation failed",
    )


@router.get("/{session_id}", response_model=StoryDetailResponse, summary="获取故事")
async def get_story(session_id: str):
    """
    获取故事生成结果
    """
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
        discussion=None,
    )


@router.get("/{session_id}/stream", summary="流式获取生成过程")
async def stream_story(session_id: str):
    """
    流式获取故事生成过程（SSE）
    """
    orchestrator = get_orchestrator()
    
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    async def event_generator():
        """SSE事件生成器"""
        async for event in orchestrator.generate_story_stream(session_id):
            event_type = event.get("type", "message")
            data = event.get("data", {})
            yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        # 发送结束标记
        yield "event: end\ndata: {}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )

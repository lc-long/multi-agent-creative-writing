"""
Stories API Endpoints

故事相关的API接口。
"""

import logging
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
    
    - **theme**: 故事主题（必填）
    - **genre**: 故事类型（选填）
    - **constraints**: 其他约束条件（选填）
    
    返回会话ID，可用于查询生成进度和结果。
    """
    orchestrator = get_orchestrator()
    
    # 创建会话
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
    
    - **session_id**: 会话ID
    
    异步生成故事，完成后可通过GET /stories/{session_id}获取结果。
    """
    orchestrator = get_orchestrator()
    
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 异步生成（这里简化为同步调用，实际应该使用后台任务）
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
    
    - **session_id**: 会话ID
    
    返回故事的完整内容，包括大纲、角色、对话等。
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
        discussion=None,  # TODO: 添加讨论记录
    )


@router.get("/{session_id}/stream", summary="流式获取生成过程")
async def stream_story(session_id: str):
    """
    流式获取故事生成过程（SSE）
    
    - **session_id**: 会话ID
    
    返回Server-Sent Events流，实时展示Agent的生成过程。
    """
    orchestrator = get_orchestrator()
    
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    async def event_generator():
        """SSE事件生成器"""
        import json
        
        async for event in orchestrator.generate_story_stream(session_id):
            event_type = event.get("type", "message")
            data = json.dumps(event, ensure_ascii=False)
            yield f"event: {event_type}\ndata: {data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

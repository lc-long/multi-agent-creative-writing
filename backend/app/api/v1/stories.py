"""
Stories API Endpoints

故事相关的API接口。
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from enum import Enum

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
    # TODO: 实现故事创建逻辑
    import uuid
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    
    return StoryResponse(
        session_id=session_id,
        status="pending",
        message="Story generation started"
    )


@router.get("/{session_id}", response_model=StoryDetailResponse, summary="获取故事")
async def get_story(session_id: str):
    """
    获取故事生成结果
    
    - **session_id**: 会话ID
    
    返回故事的完整内容，包括大纲、角色、对话等。
    """
    # TODO: 实现故事获取逻辑
    raise HTTPException(status_code=404, detail="Story not found")


@router.get("/{session_id}/stream", summary="流式获取生成过程")
async def stream_story(session_id: str):
    """
    流式获取故事生成过程（SSE）
    
    - **session_id**: 会话ID
    
    返回Server-Sent Events流，实时展示Agent的生成过程。
    """
    # TODO: 实现SSE流式响应
    from fastapi.responses import StreamingResponse
    
    async def event_generator():
        yield "event: status\ndata: {\"message\": \"Not implemented yet\"}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

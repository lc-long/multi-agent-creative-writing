"""
Story Schemas

故事相关的Pydantic Schema，用于API请求和响应。
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


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
    theme: str = Field(
        ..., 
        description="故事主题",
        min_length=1,
        max_length=500,
        examples=["未来世界的AI觉醒"]
    )
    genre: Optional[Genre] = Field(
        None, 
        description="故事类型",
        examples=["science_fiction"]
    )
    constraints: Optional[Dict[str, Any]] = Field(
        None, 
        description="其他约束条件",
        examples=[{"target_audience": "青少年", "elements": ["哲学思考", "冒险"]}]
    )


class StoryResponse(BaseModel):
    """故事创建响应"""
    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="状态")
    message: str = Field(..., description="消息")


class ActOutlineResponse(BaseModel):
    """故事大纲 - 幕响应"""
    name: str
    description: str
    key_events: List[str]


class StoryOutlineResponse(BaseModel):
    """故事大纲响应"""
    title: str
    genre: str
    synopsis: str
    acts: List[ActOutlineResponse]
    themes: List[str]


class CharacterResponse(BaseModel):
    """角色响应"""
    name: str
    role: str
    age: Optional[int] = None
    personality: str
    background: str
    motivation: str
    arc: Optional[str] = None
    relationships: List[Dict[str, str]] = []


class DialogueLineResponse(BaseModel):
    """对话行响应"""
    character: str
    line: str


class DialogueResponse(BaseModel):
    """对话响应"""
    scene: str
    participants: List[str]
    content: List[DialogueLineResponse]


class WorldSettingResponse(BaseModel):
    """世界观设定响应"""
    era: str
    location: str
    rules: List[str]
    technology_level: Optional[str] = None
    culture: Optional[str] = None


class StoryDetailResponse(BaseModel):
    """故事详情响应"""
    session_id: str
    status: str
    story: Optional[Dict[str, Any]] = None
    discussion: Optional[List[Dict[str, Any]]] = None


class AgentMessageResponse(BaseModel):
    """Agent消息响应"""
    agent_id: str
    agent_name: str
    content: str
    message_type: str
    round: int

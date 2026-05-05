"""
Story Models

故事相关的数据模型。
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


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


class SessionStatus(str, Enum):
    """会话状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ActOutline(BaseModel):
    """故事大纲 - 幕"""
    name: str = Field(..., description="幕名称")
    description: str = Field(..., description="幕描述")
    key_events: List[str] = Field(default_factory=list, description="关键事件")


class StoryOutline(BaseModel):
    """故事大纲"""
    title: str = Field(..., description="故事标题")
    genre: Genre = Field(..., description="故事类型")
    synopsis: str = Field(..., description="一句话简介")
    acts: List[ActOutline] = Field(..., description="故事结构（幕）")
    themes: List[str] = Field(default_factory=list, description="主题")


class CharacterBase(BaseModel):
    """角色基础模型"""
    name: str = Field(..., description="角色名")
    role: str = Field(..., description="角色定位: protagonist, antagonist, supporting")
    age: Optional[int] = Field(None, description="年龄")
    personality: str = Field(..., description="性格描述")
    background: str = Field(..., description="背景故事")
    motivation: str = Field(..., description="核心动机")
    arc: Optional[str] = Field(None, description="成长弧线")


class CharacterRelationship(BaseModel):
    """角色关系"""
    character_name: str = Field(..., description="关联角色名")
    relation: str = Field(..., description="关系描述")


class Character(CharacterBase):
    """角色完整模型"""
    relationships: List[CharacterRelationship] = Field(
        default_factory=list,
        description="角色关系"
    )


class DialogueLine(BaseModel):
    """对话行"""
    character: str = Field(..., description="角色名")
    line: str = Field(..., description="台词")


class Dialogue(BaseModel):
    """对话场景"""
    scene: str = Field(..., description="场景描述")
    participants: List[str] = Field(..., description="参与者")
    content: List[DialogueLine] = Field(..., description="对话内容")


class WorldSetting(BaseModel):
    """世界观设定"""
    era: str = Field(..., description="时代背景")
    location: str = Field(..., description="地点设定")
    rules: List[str] = Field(default_factory=list, description="世界规则")
    technology_level: Optional[str] = Field(None, description="科技水平")
    culture: Optional[str] = Field(None, description="文化背景")


class Story(BaseModel):
    """故事完整模型"""
    id: str = Field(..., description="故事ID")
    session_id: str = Field(..., description="会话ID")
    title: str = Field(..., description="故事标题")
    genre: Genre = Field(..., description="故事类型")
    synopsis: str = Field(..., description="简介")
    outline: Optional[StoryOutline] = Field(None, description="故事大纲")
    characters: List[Character] = Field(default_factory=list, description="角色列表")
    dialogues: List[Dialogue] = Field(default_factory=list, description="对话列表")
    world_setting: Optional[WorldSetting] = Field(None, description="世界观设定")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class Session(BaseModel):
    """会话模型"""
    id: str = Field(..., description="会话ID")
    status: SessionStatus = Field(default=SessionStatus.PENDING, description="状态")
    theme: str = Field(..., description="故事主题")
    genre: Optional[Genre] = Field(None, description="故事类型")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")
    story: Optional[Story] = Field(None, description="生成的故事")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

"""
Agent Output Schemas

每个Agent输出的结构化数据模型，保证下游永远收到合法数据。
"""

from pydantic import BaseModel
from typing import Optional


class PlotCharacter(BaseModel):
    name: str = ""
    role: str = "supporting"
    description: str = ""


class Act(BaseModel):
    name: str = ""
    description: str = ""
    key_events: list[str] = []


class PlotOutput(BaseModel):
    title: str = "未命名"
    genre: str = ""
    synopsis: str = ""
    core_conflict: str = ""
    characters: list[PlotCharacter] = []
    acts: list[Act] = []
    themes: list[str] = []


class CharacterRelationship(BaseModel):
    character_name: str = ""
    relation: str = ""


class CharacterOutput(BaseModel):
    name: str = ""
    role: str = "supporting"
    age: Optional[int] = None
    personality: str = ""
    background: str = ""
    motivation: str = ""
    arc: Optional[str] = None
    relationships: list[CharacterRelationship] = []


class CharacterListOutput(BaseModel):
    characters: list[CharacterOutput] = []


class WorldSettingOutput(BaseModel):
    era: str = "现代"
    location: str = "未知"
    rules: list[str] = []
    technology_level: Optional[str] = None
    culture: Optional[str] = None
    history: Optional[str] = None
    factions: list[str] = []


class WorldOutput(BaseModel):
    world_setting: WorldSettingOutput = WorldSettingOutput()


class DialogueLine(BaseModel):
    character: str = ""
    line: str = ""


class DialogueScene(BaseModel):
    scene: str = ""
    participants: list[str] = []
    content: list[DialogueLine] = []


class DialogueOutput(BaseModel):
    dialogues: list[DialogueScene] = []

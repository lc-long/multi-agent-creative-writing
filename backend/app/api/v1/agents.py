"""
Agents API Endpoints

Agent相关的API接口。
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class AgentInfo(BaseModel):
    """Agent信息"""
    id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent名称")
    description: str = Field(..., description="Agent描述")
    status: str = Field(..., description="Agent状态")


class AgentListResponse(BaseModel):
    """Agent列表响应"""
    agents: List[AgentInfo]


@router.get("", response_model=AgentListResponse, summary="获取所有Agent")
async def list_agents():
    """
    获取所有可用的Agent信息
    
    返回系统中所有Agent的列表，包括ID、名称、描述和状态。
    """
    agents = [
        AgentInfo(
            id="plot_agent",
            name="剧情Agent",
            description="负责设计故事结构、起承转合、冲突和高潮",
            status="ready"
        ),
        AgentInfo(
            id="character_agent",
            name="人物Agent",
            description="负责设计角色性格、背景、动机和成长弧线",
            status="ready"
        ),
        AgentInfo(
            id="dialogue_agent",
            name="对话Agent",
            description="负责生成符合角色性格的对话示例",
            status="ready"
        ),
        AgentInfo(
            id="world_agent",
            name="世界观Agent",
            description="负责设定故事发生的世界和规则",
            status="ready"
        ),
    ]
    
    return AgentListResponse(agents=agents)


@router.get("/{agent_id}", response_model=AgentInfo, summary="获取Agent详情")
async def get_agent(agent_id: str):
    """
    获取指定Agent的详细信息
    
    - **agent_id**: Agent ID
    
    返回Agent的详细信息。
    """
    # TODO: 实现Agent详情获取
    from fastapi import HTTPException
    
    agents = {
        "plot_agent": AgentInfo(
            id="plot_agent",
            name="剧情Agent",
            description="负责设计故事结构、起承转合、冲突和高潮",
            status="ready"
        ),
        "character_agent": AgentInfo(
            id="character_agent",
            name="人物Agent",
            description="负责设计角色性格、背景、动机和成长弧线",
            status="ready"
        ),
        "dialogue_agent": AgentInfo(
            id="dialogue_agent",
            name="对话Agent",
            description="负责生成符合角色性格的对话示例",
            status="ready"
        ),
        "world_agent": AgentInfo(
            id="world_agent",
            name="世界观Agent",
            description="负责设定故事发生的世界和规则",
            status="ready"
        ),
    }
    
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agents[agent_id]

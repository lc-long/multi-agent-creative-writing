"""
Base Agent Module

所有Agent的基类，提供通用的LLM调用和消息处理功能。
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


class AgentMessage(BaseModel):
    """Agent消息模型"""
    agent_id: str = Field(..., description="Agent ID")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(default="proposal", description="消息类型: proposal, feedback, revision, consensus")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class AgentProposal(BaseModel):
    """Agent提案"""
    agent_id: str = Field(..., description="Agent ID")
    content: Dict[str, Any] = Field(..., description="提案内容")
    summary: str = Field(..., description="提案摘要")
    confidence: float = Field(default=0.8, description="置信度")


class AgentFeedback(BaseModel):
    """Agent反馈"""
    agent_id: str = Field(..., description="Agent ID")
    target_agent: str = Field(..., description="目标Agent")
    feedback: str = Field(..., description="反馈内容")
    suggestions: List[str] = Field(default_factory=list, description="建议")
    agreement: bool = Field(default=True, description="是否同意")


class ConsensusResult(BaseModel):
    """共识结果"""
    reached: bool = Field(..., description="是否达成共识")
    content: Dict[str, Any] = Field(default_factory=dict, description="共识内容")
    summary: str = Field(..., description="共识摘要")
    disagreements: List[str] = Field(default_factory=list, description="分歧点")


class BaseAgent(ABC):
    """
    Agent基类
    
    所有Agent都继承此类，实现具体的业务逻辑。
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        system_prompt: str,
    ):
        """
        初始化Agent
        
        Args:
            agent_id: Agent唯一标识
            name: Agent名称
            description: Agent描述
            system_prompt: 系统提示词
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.logger = logging.getLogger(f"agent.{agent_id}")
    
    async def call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )
        
        full_messages = [
            {"role": "system", "content": self.system_prompt},
            *messages,
        ]
        
        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=full_messages,
                temperature=temperature or settings.TEMPERATURE,
                max_tokens=max_tokens or settings.MAX_TOKENS,
            )
            
            content = response.choices[0].message.content
            self.logger.debug(f"LLM response: {content[:100]}...")
            return content
            
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从LLM响应中提取JSON，自动去除<think>块和markdown代码块包裹"""
        import re
        raw = text

        # 去除 <think>...</think> 块
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL)

        # 尝试直接解析
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # 尝试从 ```json ... ``` 中提取
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试从 { ... } 中提取
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法从响应中提取JSON: {text[:200]}...")
    
    @abstractmethod
    async def propose(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentProposal:
        """
        提出方案
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            Agent提案
        """
        pass
    
    @abstractmethod
    async def review(
        self,
        proposals: Dict[str, AgentProposal],
        discussion: List[AgentMessage],
    ) -> AgentFeedback:
        """
        Review其他Agent的方案
        
        Args:
            proposals: 所有Agent的提案
            discussion: 讨论记录
            
        Returns:
            Agent反馈
        """
        pass
    
    @abstractmethod
    async def revise(
        self,
        feedback: List[AgentFeedback],
        current_proposal: AgentProposal,
    ) -> AgentProposal:
        """
        根据反馈修改方案
        
        Args:
            feedback: 反馈列表
            current_proposal: 当前提案
            
        Returns:
            修改后的提案
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, name={self.name})"

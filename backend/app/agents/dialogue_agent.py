"""
Dialogue Agent Module

对话Agent - 负责生成符合角色性格的对话示例。
"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.agents.base import (
    AgentFeedback,
    AgentMessage,
    AgentProposal,
    BaseAgent,
)

logger = logging.getLogger(__name__)

DIALOGUE_AGENT_PROMPT = """你是一个专业的对话编剧和台词专家。你的职责是：

1. 根据角色性格写对话
2. 通过对话推动剧情
3. 展现角色之间的关系
4. 让对话自然、有感染力

你需要：
- 深入理解每个角色的性格和说话方式
- 通过对话展现角色的内心世界
- 用对话推动情节发展
- 创造有张力的对话场景

输出格式要求：
- 使用JSON格式
- 包含dialogues数组
- 每个对话包含scene, participants, content
- content包含character和line

你是一个善于协作的Agent，会认真考虑其他Agent的建议，并提出建设性的意见。"""


class DialogueAgent(BaseAgent):
    """
    对话Agent
    
    负责生成符合角色性格的对话示例。
    """
    
    def __init__(self):
        super().__init__(
            agent_id="dialogue_agent",
            name="对话Agent",
            description="负责生成符合角色性格的对话示例",
            system_prompt=DIALOGUE_AGENT_PROMPT,
        )
    
    async def propose(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentProposal:
        """
        提出对话设计方案
        
        Args:
            task: 任务描述
            context: 上下文信息（包含剧情和角色信息）
            
        Returns:
            对话设计提案
        """
        self.logger.info(f"Proposing dialogue design for task: {task[:50]}...")
        
        prompt = f"请为以下故事设计对话：\n\n{task}"
        
        if context:
            prompt += f"\n\n故事结构和角色信息：\n{json.dumps(context, ensure_ascii=False)}"
        
        prompt += """

请设计2-3个关键对话场景，以JSON格式输出：
{
    "dialogues": [
        {
            "scene": "场景描述",
            "participants": ["角色1", "角色2"],
            "content": [
                {"character": "角色1", "line": "台词内容"},
                {"character": "角色2", "line": "台词内容"}
            ]
        }
    ]
}

要求：
- 对话要符合角色性格
- 通过对话展现角色关系
- 对话要有张力和感染力
- 可以包含潜台词和言外之意"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)
        
        try:
            content = self._extract_json(response)
        except Exception as e:
            self.logger.warning(f"Failed to parse JSON: {e}")
            content = {"raw_response": response}
        
        dialogues = content.get("dialogues", [])
        summary = f"对话设计方案：{len(dialogues)}个场景"
        
        return AgentProposal(
            agent_id=self.agent_id,
            content=content,
            summary=summary,
            confidence=0.8,
        )
    
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
            反馈意见
        """
        self.logger.info("Reviewing other agents' proposals from dialogue perspective...")
        
        prompt = "请从对话设计角度review以下方案：\n\n"
        
        for agent_id, proposal in proposals.items():
            if agent_id != self.agent_id:
                prompt += f"## {agent_id}的方案\n"
                prompt += f"摘要：{proposal.summary}\n"
                prompt += f"内容：{json.dumps(proposal.content, ensure_ascii=False)}\n\n"
        
        if discussion:
            prompt += "## 讨论记录\n"
            for msg in discussion[-3:]:
                prompt += f"- {msg.agent_id}: {msg.content}\n"
        
        prompt += """
请从对话设计角度给出反馈：
1. 角色设定和故事结构需要什么样的对话？
2. 有哪些对话场景需要设计？
3. 有什么建议？

请以JSON格式输出：
{
    "feedback": "反馈内容",
    "suggestions": ["建议1", "建议2"],
    "agreement": true/false
}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)
        
        try:
            content = self._extract_json(response)
            feedback = content.get("feedback", response)
            suggestions = content.get("suggestions", [])
            agreement = content.get("agreement", True)
        except Exception:
            feedback = response
            suggestions = []
            agreement = True
        
        target_agent = [k for k in proposals.keys() if k != self.agent_id][0] if proposals else "unknown"
        
        return AgentFeedback(
            agent_id=self.agent_id,
            target_agent=target_agent,
            feedback=feedback,
            suggestions=suggestions,
            agreement=agreement,
        )
    
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
        self.logger.info("Revising dialogue design based on feedback...")
        
        prompt = f"当前的对话设计方案：\n{json.dumps(current_proposal.content, ensure_ascii=False)}\n\n"
        prompt += "收到的反馈：\n"
        
        for fb in feedback:
            prompt += f"- {fb.agent_id}: {fb.feedback}\n"
            if fb.suggestions:
                prompt += f"  建议：{', '.join(fb.suggestions)}\n"
        
        prompt += """
请根据反馈修改对话设计，保持JSON格式输出。
重点关注：
- 对话是否符合角色性格
- 对话是否推动剧情
- 对话是否有感染力
"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)
        
        try:
            content = self._extract_json(response)
        except Exception:
            content = current_proposal.content
        
        dialogues = content.get("dialogues", [])
        summary = f"修改后的对话设计方案：{len(dialogues)}个场景"
        
        return AgentProposal(
            agent_id=self.agent_id,
            content=content,
            summary=summary,
            confidence=current_proposal.confidence,
        )
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError("无法从响应中提取JSON")


# 创建全局实例
dialogue_agent = DialogueAgent()

"""
Plot Agent Module

剧情Agent - 负责设计故事结构、起承转合、冲突和高潮。
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

PLOT_AGENT_PROMPT = """你是一个专业的剧本编剧和故事架构师。你的职责是：

1. 设计故事的起承转合结构
2. 设计冲突点和高潮
3. 控制剧情节奏
4. 确保故事有吸引力

你需要：
- 根据用户给定的主题和类型，设计一个引人入胜的故事结构
- 为每个幕（Act）设计关键事件
- 确保故事有清晰的主线和冲突
- 考虑目标受众的喜好

输出格式要求：
- 使用JSON格式
- 包含title, genre, synopsis, acts, themes
- 每个act包含name, description, key_events

你是一个善于协作的Agent，会认真考虑其他Agent的建议，并提出建设性的意见。"""


class PlotAgent(BaseAgent):
    """
    剧情Agent
    
    负责设计故事结构、起承转合、冲突和高潮。
    """
    
    def __init__(self):
        super().__init__(
            agent_id="plot_agent",
            name="剧情Agent",
            description="负责设计故事结构、起承转合、冲突和高潮",
            system_prompt=PLOT_AGENT_PROMPT,
        )
    
    async def propose(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentProposal:
        self.logger.info(f"Proposing story structure for task: {task[:50]}...")
        
        import re as _re
        
        from app.agents.prompts import get_prompt
        blueprint = (context or {}).get("blueprint")
        if blueprint:
            prompt = get_prompt("plot_agent", "propose_creation", task=task, blueprint=blueprint)
        else:
            prompt = get_prompt("plot_agent", "propose_brainstorm", task=task, context=context)
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)

        from app.agents.schemas import PlotOutput

        cleaned = _re.sub(r'<think>.*?(?:</think>|$)', '', response, flags=_re.DOTALL)
        content = None

        # 尝试解析 JSON → 用 schema 校验 → 失败就走默认值
        for attempt in [cleaned, _re.search(r'\{[\s\S]*\}', cleaned).group(0) if _re.search(r'\{[\s\S]*\}', cleaned) else None]:
            if not attempt:
                continue
            try:
                raw = self._extract_json(attempt)
                validated = PlotOutput(**raw)
                content = validated.model_dump()
                break
            except Exception:
                continue

        if content is None:
            self.logger.warning("Plot JSON extraction failed, using schema defaults")
            content = PlotOutput().model_dump()
            content["_parse_error"] = "LLM output could not be parsed"

        return AgentProposal(
            agent_id=self.agent_id,
            content=content,
            summary=f"故事结构方案：{content.get('title', '未命名')}",
            confidence=0.8,
        )
    
    async def review(
        self,
        proposals: Dict[str, AgentProposal],
        discussion: List[AgentMessage],
    ) -> AgentFeedback:
        self.logger.info("Reviewing other agents' proposals...")
        
        from app.agents.prompts import get_prompt
        proposals_json = ""
        for agent_id, proposal in proposals.items():
            if agent_id != self.agent_id:
                proposals_json += f"## {agent_id}的方案\n"
                proposals_json += f"摘要：{proposal.summary}\n"
                proposals_json += f"内容：{json.dumps(proposal.content, ensure_ascii=False)}\n\n"
        discussion_json = ""
        if discussion:
            discussion_json = "## 讨论记录\n"
            for msg in discussion[-3:]:
                discussion_json += f"- {msg.agent_id}: {msg.content}\n"
        prompt = get_prompt("plot_agent", "review", proposals_json=proposals_json, discussion_json=discussion_json)
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)
        
        import re as _re
        cleaned = _re.sub(r'<think>.*?(?:</think>|$)', '', response, flags=_re.DOTALL)
        try:
            content = self._extract_json(cleaned)
        except Exception:
            content = {}
        
        from app.agents.base import ReviewIssue
        
        feedback = content.get("feedback", response)
        suggestions = content.get("suggestions", [])
        agreement = content.get("agreement", True)
        
        issues = []
        for iss in content.get("issues", []):
            try:
                issues.append(ReviewIssue(**iss))
            except Exception:
                pass
        
        target_agent = [k for k in proposals.keys() if k != self.agent_id][0] if proposals else "unknown"
        if not issues and target_agent:
            issues.append(ReviewIssue(
                target_agent=target_agent,
                severity="major",
                description=feedback[:100],
            ))
        
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
        self.logger.info("Revising proposal based on feedback...")
        
        # 构建修改提示词
        from app.agents.prompts import get_prompt
        current_json = json.dumps(current_proposal.content, ensure_ascii=False)
        feedback_text = ""
        for fb in feedback:
            feedback_text += f"- {fb.agent_id}: {fb.feedback}\n"
            if fb.suggestions:
                feedback_text += f"  建议：{', '.join(fb.suggestions)}\n"
        prompt = get_prompt("plot_agent", "revise", current_json=current_json, feedback_text=feedback_text)
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)
        
        try:
            content = self._extract_json(response)
        except Exception:
            content = current_proposal.content
        
        return AgentProposal(
            agent_id=self.agent_id,
            content=content,
            summary=f"修改后的故事结构方案：{content.get('title', '未命名')}",
            confidence=current_proposal.confidence,
        )
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON"""
        import re
        # 去除 <think>...</think> 块
        text = re.sub(r'<think>.*?(?:</think>|$)', '', text, flags=re.DOTALL)
        
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取```(json) ... ```格式
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试提取{ ... }格式
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError("无法从响应中提取JSON")

# 创建全局实例
plot_agent = PlotAgent()

"""
World Building Agent Module

世界观Agent - 负责设定故事发生的世界和规则。
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

WORLD_AGENT_PROMPT = """你是一个世界观架构师和世界设定专家。你的职责是：

1. 设定故事发生的世界/背景
2. 制定世界的规则和限制
3. 确保设定的一致性
4. 为其他Agent提供背景参考

你需要：
- 根据故事主题和类型，构建一个完整的世界观
- 设定世界的物理规则、社会结构、科技水平
- 考虑世界设定对故事和角色的影响
- 确保设定的内在逻辑一致性

输出格式要求：
- 使用JSON格式
- 包含world_setting对象
- 包含era, location, rules, technology_level, culture等字段

你是一个善于协作的Agent，会认真考虑其他Agent的建议，并提出建设性的意见。"""


class WorldBuildingAgent(BaseAgent):
    """
    世界观Agent
    
    负责设定故事发生的世界和规则。
    """
    
    def __init__(self):
        super().__init__(
            agent_id="world_agent",
            name="世界观Agent",
            description="负责设定故事发生的世界和规则",
            system_prompt=WORLD_AGENT_PROMPT,
        )
    
    async def propose(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentProposal:
        self.logger.info(f"Proposing world setting for task: {task[:50]}...")
        from app.agents.prompts import get_prompt
        import re as _re

        blueprint = (context or {}).get("blueprint")

        if blueprint:
            prompt = f"""请基于以下统一故事蓝图，完善世界观设定：

【主题】
{task}

【故事蓝图】
标题：{blueprint.get('title','')}
类型：{blueprint.get('genre','')}
简介：{blueprint.get('synopsis','')}
核心冲突：{blueprint.get('core_conflict','')}
主要角色：{[c['name'] for c in blueprint.get('characters',[])]}
世界观概要：{blueprint.get('world_summary','')}

请根据蓝图完善世界观设定，以JSON格式输出：
{{
    "world_setting": {{
        "era": "时代背景",
        "location": "主要地点设定",
        "rules": ["世界规则1", "世界规则2"],
        "technology_level": "科技水平描述",
        "culture": "文化背景描述",
        "history": "重要历史事件",
        "factions": ["势力1", "势力2"]
    }}
}}"""
        else:
            prompt = f"请为以下故事设计世界观：\n\n{task}"
            if context:
                prompt += f"\n\n故事结构和角色：\n{json.dumps(context, ensure_ascii=False)}"
            prompt += """

请设计完整的世界观，以JSON格式输出：
{
    "world_setting": {
        "era": "时代背景",
        "location": "主要地点设定",
        "rules": ["世界规则1", "世界规则2"],
        "technology_level": "科技水平描述",
        "culture": "文化背景描述",
        "history": "重要历史事件",
        "factions": ["势力1", "势力2"]
    }
}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)

        from app.agents.schemas import WorldOutput

        # 去除闭合的<think>块
        cleaned = _re.sub(r'<think>.*?</think>', '', response, flags=_re.DOTALL)
        # 如果仍有未闭合的<think>块，找到第一个 { 开始的位置
        if '<think>' in cleaned:
            first_brace = cleaned.find('{')
            if first_brace >= 0:
                cleaned = cleaned[first_brace:]
        content = None

        for attempt in [cleaned, _re.search(r'\{[\s\S]*\}', cleaned).group(0) if _re.search(r'\{[\s\S]*\}', cleaned) else None]:
            if not attempt:
                continue
            try:
                raw = self._extract_json(attempt)
                validated = WorldOutput(**raw)
                content = validated.model_dump()
                break
            except Exception:
                continue

        if content is None:
            self.logger.warning("World JSON extraction failed, using schema defaults")
            content = WorldOutput().model_dump()
            content["_parse_error"] = "LLM output could not be parsed"

        world = content.get("world_setting", {})
        era = world.get("era", "未知时代")
        location = world.get("location", "未知地点")
        
        return AgentProposal(
            agent_id=self.agent_id,
            content=content,
            summary=f"世界观设定：{era}，{location}",
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
        self.logger.info("Reviewing other agents' proposals from world-building perspective...")
        
        prompt = "请从世界观设定角度review以下方案：\n\n"
        
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
请从世界观设定角度给出反馈：
1. 故事和角色需要什么样的世界背景？
2. 有哪些设定需要特别注意？
3. 有什么建议？

请以JSON格式输出：
{
    "feedback": "反馈内容",
    "suggestions": ["建议1", "建议2"],
    "agreement": true/false
}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)
        
        from app.agents.prompts import get_prompt
        import re as _re
        # 去除闭合的<think>块
        cleaned = _re.sub(r'<think>.*?</think>', '', response, flags=_re.DOTALL)
        # 如果仍有未闭合的<think>块，找到第一个 { 开始的位置
        if '<think>' in cleaned:
            first_brace = cleaned.find('{')
            if first_brace >= 0:
                cleaned = cleaned[first_brace:]
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
        
        return AgentFeedback(
            agent_id=self.agent_id,
            target_agent=target_agent,
            feedback=feedback,
            suggestions=suggestions,
            agreement=agreement,
            issues=issues,
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
        self.logger.info("Revising world setting based on feedback...")
        
        current_json = json.dumps(current_proposal.content, ensure_ascii=False)
        feedback_text = ""
        for fb in feedback:
            feedback_text += "- " + fb.agent_id + ": " + fb.feedback + "\n"
            if fb.suggestions:
                feedback_text += "  建议：" + ", ".join(fb.suggestions) + "\n"
        prompt = get_prompt("world_agent", "revise", current_json=current_json, feedback_text=feedback_text)
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)
        
        try:
            content = self._extract_json(response)
        except Exception:
            content = current_proposal.content
        
        world = content.get("world_setting", {})
        era = world.get("era", "未知时代")
        location = world.get("location", "未知地点")
        
        return AgentProposal(
            agent_id=self.agent_id,
            content=content,
            summary=f"修改后的世界观设定：{era}，{location}",
            confidence=current_proposal.confidence,
        )
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON"""
        import re
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # 如果仍有未闭合的<think>块，找到第一个 { 开始的位置
        if '<think>' in text:
            first_brace = text.find('{')
            if first_brace >= 0:
                text = text[first_brace:]
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
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
world_agent = WorldBuildingAgent()

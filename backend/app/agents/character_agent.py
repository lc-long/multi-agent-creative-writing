"""
Character Agent Module

人物Agent - 负责设计角色性格、背景、动机和成长弧线。
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

CHARACTER_AGENT_PROMPT = """你是一个专业的角色设计师和人物塑造专家。你的职责是：

1. 设计角色的性格、背景、动机
2. 设计角色的成长弧线
3. 确保角色之间的关系合理
4. 让角色有深度和复杂性

你需要：
- 根据故事主题和结构，设计有血有肉的角色
- 为每个角色创建独特的性格特征
- 设计角色的内在动机和外在目标
- 规划角色的成长和变化轨迹
- 建立角色之间的关系网络

输出格式要求：
- 使用JSON格式
- 包含characters数组
- 每个角色包含name, role, age, personality, background, motivation, arc, relationships

你是一个善于协作的Agent，会认真考虑其他Agent的建议，并提出建设性的意见。"""


class CharacterAgent(BaseAgent):
    """
    人物Agent
    
    负责设计角色性格、背景、动机和成长弧线。
    """
    
    def __init__(self):
        super().__init__(
            agent_id="character_agent",
            name="人物Agent",
            description="负责设计角色性格、背景、动机和成长弧线",
            system_prompt=CHARACTER_AGENT_PROMPT,
        )
    
    async def propose(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentProposal:
        self.logger.info(f"Proposing character design for task: {task[:50]}...")
        import re as _re

        from app.agents.prompts import get_prompt
        blueprint = (context or {}).get("blueprint")
        if blueprint:
            chars_list = "\n".join(
                f"  - {c['name']}（{c.get('role','?')}）: {c.get('description','')}"
                for c in blueprint["characters"]
            )
            prompt = f"""请基于以下统一故事蓝图，进行详细的角色设计：

【主题】
{task}

【故事蓝图】
标题：{blueprint.get('title','')}
类型：{blueprint.get('genre','')}
简介：{blueprint.get('synopsis','')}
核心冲突：{blueprint.get('core_conflict','')}
世界观：{blueprint.get('world_summary','')}

【故事中已出现的角色】
{chars_list}

请根据蓝图中的角色列表，为每个角色进行完整的详细设计。可以适当增减角色。
以JSON格式输出：
{{
    "characters": [
        {{
            "name": "角色名",
            "role": "protagonist/antagonist/supporting",
            "age": 25,
            "personality": "性格描述（2-3句话）",
            "background": "背景故事（3-4句话）",
            "motivation": "核心动机",
            "arc": "成长弧线描述",
            "relationships": [
                {{"character_name": "其他角色名", "relation": "关系描述"}}
            ]
        }}
    ]
}}"""
        else:
            prompt = f"请为以下故事设计角色：\n\n{task}"
            if context:
                prompt += f"\n\n故事结构：\n{json.dumps(context, ensure_ascii=False)}"
            prompt += """

请设计3-5个主要角色，以JSON格式输出：
{
    "characters": [
        {
            "name": "角色名",
            "role": "protagonist/antagonist/supporting",
            "age": 25,
            "personality": "性格描述",
            "background": "背景故事",
            "motivation": "核心动机",
            "arc": "成长弧线描述",
            "relationships": [
                {"character_name": "其他角色名", "relation": "关系描述"}
            ]
        }
    ]
}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)

        from app.agents.schemas import CharacterListOutput

        cleaned = _re.sub(r'<think>.*?</think>', '', response, flags=_re.DOTALL)
        content = None

        for attempt in [cleaned, _re.search(r'\{[\s\S]*\}', cleaned).group(0) if _re.search(r'\{[\s\S]*\}', cleaned) else None]:
            if not attempt:
                continue
            try:
                raw = self._extract_json(attempt)
                validated = CharacterListOutput(**raw)
                content = validated.model_dump()
                break
            except Exception:
                continue

        if content is None:
            self.logger.warning("Character JSON extraction failed, using schema defaults")
            content = CharacterListOutput().model_dump()
            content["_parse_error"] = "LLM output could not be parsed"

        characters = content.get("characters", [])
        summary = f"角色设计方案：{len(characters)}个角色"
        if characters:
            names = [c.get("name", "") for c in characters[:3]]
            summary += f"（{', '.join(names)}等）"
        
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
        self.logger.info("Reviewing other agents' proposals from character perspective...")
        
        prompt = "请从角色设计角度review以下方案：\n\n"
        
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
请从角色设计角度给出反馈：
1. 故事结构对角色设计有什么要求？
2. 需要什么样的角色来支撑这个故事？
3. 有什么建议？

请以JSON格式输出：
{
    "feedback": "反馈内容",
    "suggestions": ["建议1", "建议2"],
    "agreement": true/false
}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)
        
        import re as _re
        cleaned = _re.sub(r'<think>.*?</think>', '', response, flags=_re.DOTALL)
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
        self.logger.info("Revising character design based on feedback...")
        
        current_json = json.dumps(current_proposal.content, ensure_ascii=False)
        feedback_text = ""
        for fb in feedback:
            feedback_text += "- " + fb.agent_id + ": " + fb.feedback + "\n"
            if fb.suggestions:
                feedback_text += "  建议：" + ", ".join(fb.suggestions) + "\n"
        prompt = get_prompt("character_agent", "revise", current_json=current_json, feedback_text=feedback_text)
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)
        
        try:
            content = self._extract_json(response)
        except Exception:
            content = current_proposal.content
        
        characters = content.get("characters", [])
        summary = f"修改后的角色设计方案：{len(characters)}个角色"
        
        return AgentProposal(
            agent_id=self.agent_id,
            content=content,
            summary=summary,
            confidence=current_proposal.confidence,
        )
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON"""
        import re
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
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
character_agent = CharacterAgent()

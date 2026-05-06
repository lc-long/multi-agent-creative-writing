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
        
        blueprint = (context or {}).get("blueprint")
        
        if blueprint:
            # Phase 3: 基于蓝图进行详细创作
            chars_desc = "\n".join(
                f"  - {c['name']}（{c.get('role','?')}）: {c.get('description','')}"
                for c in blueprint.get("characters", [])
            )
            prompt = f"""请基于以下统一故事蓝图，进行详细的故事结构创作：

【主题】
{task}

【故事蓝图】
标题：{blueprint.get('title','')}
类型：{blueprint.get('genre','')}
简介：{blueprint.get('synopsis','')}
核心冲突：{blueprint.get('core_conflict','')}
主要角色：
{chars_desc or '  待设计'}
世界观概要：{blueprint.get('world_summary','')}

请以JSON格式输出完整的故事结构，包含以下字段：
{{
    "title": "故事标题",
    "genre": "故事类型",
    "synopsis": "一句话简介（200字以内）",
    "core_conflict": "核心冲突描述",
    "acts": [
        {{"name": "开篇", "description": "故事起始", "key_events": ["事件1", "事件2"]}},
        {{"name": "发展", "description": "冲突升级", "key_events": ["事件1", "事件2"]}},
        {{"name": "高潮", "description": "高潮对决", "key_events": ["事件1", "事件2"]}},
        {{"name": "结局", "description": "收尾", "key_events": ["事件1", "事件2"]}}
    ],
    "themes": ["主题1", "主题2"]
}}"""
        else:
            # Phase 1: 脑暴模式——输出故事框架+角色需求
            prompt = f"请为以下主题设计一个故事结构：\n\n{task}"
            if context:
                prompt += f"\n\n额外约束：{json.dumps(context, ensure_ascii=False)}"
            prompt += """

请以JSON格式输出故事结构，包含以下字段：
{
    "title": "故事标题",
    "genre": "故事类型",
    "synopsis": "一句话简介",
    "core_conflict": "核心冲突描述",
    "characters": [
        {"name": "角色名", "role": "主角/反派/配角", "description": "角色简要描述"}
    ],
    "acts": [
        {"name": "开篇", "description": "故事起始", "key_events": ["事件1", "事件2"]},
        {"name": "发展", "description": "冲突升级", "key_events": ["事件1", "事件2"]},
        {"name": "高潮", "description": "高潮对决", "key_events": ["事件1", "事件2"]},
        {"name": "结局", "description": "收尾", "key_events": ["事件1", "事件2"]}
    ],
    "themes": ["主题1", "主题2"]
}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.call_llm(messages)
        
        cleaned = _re.sub(r'<think>.*?</think>', '', response, flags=_re.DOTALL).strip()
        
        try:
            content = self._extract_json(cleaned)
        except Exception as e:
            self.logger.warning(f"Failed to parse JSON, using raw response: {e}")
            brace = _re.search(r'\{[\s\S]*\}', cleaned)
            if brace:
                try:
                    content = json.loads(brace.group(0))
                except Exception:
                    content = {"raw_response": response}
            else:
                content = {"raw_response": response}
        
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
        """
        Review其他Agent的方案
        
        Args:
            proposals: 所有Agent的提案
            discussion: 讨论记录
            
        Returns:
            反馈意见
        """
        self.logger.info("Reviewing other agents' proposals...")
        
        # 构建review提示词
        prompt = "请从剧情角度review以下方案：\n\n"
        
        for agent_id, proposal in proposals.items():
            if agent_id != self.agent_id:
                prompt += f"## {agent_id}的方案\n"
                prompt += f"摘要：{proposal.summary}\n"
                prompt += f"内容：{json.dumps(proposal.content, ensure_ascii=False)}\n\n"
        
        if discussion:
            prompt += "## 讨论记录\n"
            for msg in discussion[-3:]:  # 只看最近3条
                prompt += f"- {msg.agent_id}: {msg.content}\n"
        
        prompt += """
请从剧情角度给出反馈：
1. 这些方案对故事结构有什么影响？
2. 有哪些需要调整的地方？
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
        
        # 找到主要review的对象
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
        self.logger.info("Revising proposal based on feedback...")
        
        # 构建修改提示词
        prompt = f"当前的故事结构方案：\n{json.dumps(current_proposal.content, ensure_ascii=False)}\n\n"
        prompt += "收到的反馈：\n"
        
        for fb in feedback:
            prompt += f"- {fb.agent_id}: {fb.feedback}\n"
            if fb.suggestions:
                prompt += f"  建议：{', '.join(fb.suggestions)}\n"
        
        prompt += """
请根据反馈修改故事结构，保持JSON格式输出。
如果反馈合理，请做出相应调整；如果不合理，请保持原方案并说明理由。
"""
        
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
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
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

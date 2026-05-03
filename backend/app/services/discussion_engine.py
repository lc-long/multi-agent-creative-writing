"""
Discussion Engine Module

讨论引擎 - 管理Agent之间的讨论和协作。
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from app.agents.base import (
    AgentFeedback,
    AgentMessage,
    AgentProposal,
    BaseAgent,
    ConsensusResult,
)

logger = logging.getLogger(__name__)


@dataclass
class DiscussionRound:
    """讨论轮次"""
    round_number: int
    proposals: Dict[str, AgentProposal]
    feedback: List[AgentFeedback]
    messages: List[AgentMessage]


@dataclass
class DiscussionResult:
    """讨论结果"""
    rounds: List[DiscussionRound]
    final_proposals: Dict[str, AgentProposal]
    consensus: ConsensusResult
    summary: str


class DiscussionEngine:
    """
    讨论引擎
    
    管理Agent之间的讨论，协调多个Agent协作生成内容。
    """
    
    def __init__(self, agents: Dict[str, BaseAgent], max_rounds: int = 3):
        """
        初始化讨论引擎
        
        Args:
            agents: Agent字典，key为agent_id，value为Agent实例
            max_rounds: 最大讨论轮数
        """
        self.agents = agents
        self.max_rounds = max_rounds
        self.logger = logging.getLogger("discussion_engine")
    
    async def run_discussion(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        callback: Optional[Any] = None,
    ) -> DiscussionResult:
        """
        运行讨论流程
        
        Args:
            task: 任务描述
            context: 上下文信息
            callback: 回调函数，用于报告进度
            
        Returns:
            讨论结果
        """
        self.logger.info(f"Starting discussion for task: {task[:50]}...")
        
        rounds: List[DiscussionRound] = []
        all_messages: List[AgentMessage] = []
        
        # 第一轮：各Agent独立提出方案
        self.logger.info("Round 1: Collecting initial proposals...")
        if callback:
            await callback("status", {"phase": "proposal", "message": "各Agent正在提出初始方案..."})
        
        proposals = await self._collect_proposals(task, context)
        
        rounds.append(DiscussionRound(
            round_number=1,
            proposals=proposals,
            feedback=[],
            messages=[],
        ))
        
        # 后续轮次：互相Review和讨论
        for round_num in range(2, self.max_rounds + 1):
            self.logger.info(f"Round {round_num}: Running discussion...")
            if callback:
                await callback("status", {
                    "phase": "discussion",
                    "round": round_num,
                    "message": f"第{round_num}轮讨论开始..."
                })
            
            # 收集反馈
            feedback = await self._collect_feedback(proposals, all_messages)
            
            # 生成讨论消息
            round_messages = self._generate_discussion_messages(feedback, round_num)
            all_messages.extend(round_messages)
            
            # 根据反馈修改方案
            proposals = await self._revise_proposals(proposals, feedback)
            
            rounds.append(DiscussionRound(
                round_number=round_num,
                proposals=proposals,
                feedback=feedback,
                messages=round_messages,
            ))
            
            # 检查是否达成共识
            consensus = await self._check_consensus(proposals, all_messages)
            if consensus.reached:
                self.logger.info(f"Consensus reached at round {round_num}")
                break
        
        # 生成最终结果
        if callback:
            await callback("status", {"phase": "consensus", "message": "讨论结束，生成最终结果..."})
        
        final_consensus = await self._check_consensus(proposals, all_messages)
        summary = self._generate_summary(rounds, final_consensus)
        
        return DiscussionResult(
            rounds=rounds,
            final_proposals=proposals,
            consensus=final_consensus,
            summary=summary,
        )
    
    async def _collect_proposals(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, AgentProposal]:
        """收集所有Agent的初始提案"""
        proposals = {}
        
        for agent_id, agent in self.agents.items():
            try:
                self.logger.info(f"Collecting proposal from {agent_id}...")
                proposal = await agent.propose(task, context)
                proposals[agent_id] = proposal
                self.logger.info(f"Received proposal from {agent_id}: {proposal.summary}")
            except Exception as e:
                self.logger.error(f"Failed to get proposal from {agent_id}: {e}")
                # 创建一个默认提案
                proposals[agent_id] = AgentProposal(
                    agent_id=agent_id,
                    content={"error": str(e)},
                    summary=f"{agent.name}提案生成失败",
                    confidence=0.0,
                )
        
        return proposals
    
    async def _collect_feedback(
        self,
        proposals: Dict[str, AgentProposal],
        discussion: List[AgentMessage],
    ) -> List[AgentFeedback]:
        """收集所有Agent的反馈"""
        feedback_list = []
        
        for agent_id, agent in self.agents.items():
            try:
                self.logger.info(f"Collecting feedback from {agent_id}...")
                feedback = await agent.review(proposals, discussion)
                feedback_list.append(feedback)
                self.logger.info(f"Received feedback from {agent_id}")
            except Exception as e:
                self.logger.error(f"Failed to get feedback from {agent_id}: {e}")
        
        return feedback_list
    
    async def _revise_proposals(
        self,
        proposals: Dict[str, AgentProposal],
        feedback: List[AgentFeedback],
    ) -> Dict[str, AgentProposal]:
        """根据反馈修改提案"""
        revised_proposals = {}
        
        for agent_id, agent in self.agents.items():
            # 只收集针对该Agent的反馈
            agent_feedback = [f for f in feedback if f.target_agent == agent_id]
            
            if agent_feedback and agent_id in proposals:
                try:
                    self.logger.info(f"Revising proposal for {agent_id}...")
                    revised = await agent.revise(agent_feedback, proposals[agent_id])
                    revised_proposals[agent_id] = revised
                except Exception as e:
                    self.logger.error(f"Failed to revise proposal for {agent_id}: {e}")
                    revised_proposals[agent_id] = proposals[agent_id]
            else:
                revised_proposals[agent_id] = proposals[agent_id]
        
        return revised_proposals
    
    async def _check_consensus(
        self,
        proposals: Dict[str, AgentProposal],
        discussion: List[AgentMessage],
    ) -> ConsensusResult:
        """检查是否达成共识"""
        # 简单的共识检测：如果所有Agent的置信度都高于阈值，则认为达成共识
        threshold = 0.7
        
        all_high_confidence = all(
            p.confidence >= threshold
            for p in proposals.values()
            if p.confidence > 0  # 排除错误的提案
        )
        
        if all_high_confidence and len(proposals) == len(self.agents):
            # 合并所有提案的内容
            merged_content = {}
            for agent_id, proposal in proposals.items():
                merged_content[agent_id] = proposal.content
            
            return ConsensusResult(
                reached=True,
                content=merged_content,
                summary="所有Agent达成共识",
                disagreements=[],
            )
        
        return ConsensusResult(
            reached=False,
            content={},
            summary="尚未达成共识，需要更多讨论",
            disagreements=["置信度不足或提案不完整"],
        )
    
    def _generate_discussion_messages(
        self,
        feedback: List[AgentFeedback],
        round_number: int,
    ) -> List[AgentMessage]:
        """生成讨论消息"""
        messages = []
        
        for fb in feedback:
            content = f"对{fb.target_agent}的反馈：{fb.feedback}"
            if fb.suggestions:
                content += f"\n建议：{', '.join(fb.suggestions)}"
            
            messages.append(AgentMessage(
                agent_id=fb.agent_id,
                content=content,
                message_type="feedback",
                metadata={"round": round_number},
            ))
        
        return messages
    
    def _generate_summary(
        self,
        rounds: List[DiscussionRound],
        consensus: ConsensusResult,
    ) -> str:
        """生成讨论总结"""
        summary_parts = [
            f"讨论共进行了{len(rounds)}轮。",
        ]
        
        if consensus.reached:
            summary_parts.append("最终达成了共识。")
        else:
            summary_parts.append("尚未完全达成共识，但已生成综合方案。")
        
        # 添加各Agent的最终提案摘要
        if rounds:
            final_round = rounds[-1]
            summary_parts.append("各Agent最终方案：")
            for agent_id, proposal in final_round.proposals.items():
                summary_parts.append(f"- {agent_id}: {proposal.summary}")
        
        return "\n".join(summary_parts)


# 全局讨论引擎实例（需要在应用启动时初始化）
discussion_engine: Optional[DiscussionEngine] = None


def get_discussion_engine() -> DiscussionEngine:
    """获取讨论引擎实例"""
    global discussion_engine
    if discussion_engine is None:
        from app.agents.plot_agent import plot_agent
        from app.agents.character_agent import character_agent
        from app.agents.world_agent import world_agent
        from app.agents.dialogue_agent import dialogue_agent
        
        agents = {
            "plot_agent": plot_agent,
            "character_agent": character_agent,
            "world_agent": world_agent,
            "dialogue_agent": dialogue_agent,
        }
        
        from app.config import settings
        discussion_engine = DiscussionEngine(agents, max_rounds=settings.DISCUSSION_ROUNDS)
    
    return discussion_engine

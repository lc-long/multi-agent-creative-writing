"""
Orchestrator Service Module

编排器 - 协调整个故事生成流程。
"""

import logging
import uuid
from typing import Any, AsyncGenerator, Dict, Optional
from datetime import datetime

from app.models.story import Session, SessionStatus, Story
from app.services.discussion_engine import DiscussionEngine, get_discussion_engine

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    编排器
    
    协调整个故事生成流程，管理会话状态。
    """
    
    def __init__(self):
        """初始化编排器"""
        self.sessions: Dict[str, Session] = {}
        self.logger = logging.getLogger("orchestrator")
    
    async def create_session(
        self,
        theme: str,
        genre: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """
        创建新的生成会话
        
        Args:
            theme: 故事主题
            genre: 故事类型
            constraints: 约束条件
            
        Returns:
            创建的会话
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        session = Session(
            id=session_id,
            status=SessionStatus.PENDING,
            theme=theme,
            genre=genre,
            constraints=constraints,
        )
        
        self.sessions[session_id] = session
        self.logger.info(f"Created session {session_id} for theme: {theme[:50]}...")
        
        return session
    
    async def generate_story(self, session_id: str) -> Session:
        """
        生成故事
        
        Args:
            session_id: 会话ID
            
        Returns:
            更新后的会话
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 更新状态为处理中
        session.status = SessionStatus.PROCESSING
        session.updated_at = datetime.now()
        
        try:
            # 构建任务描述
            task = self._build_task_description(session)
            
            # 获取讨论引擎
            engine = get_discussion_engine()
            
            # 运行讨论
            result = await engine.run_discussion(task)
            
            # 构建故事对象
            story = self._build_story_from_result(session_id, result)
            
            # 更新会话
            session.story = story
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.now()
            
            self.logger.info(f"Story generation completed for session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Story generation failed for session {session_id}: {e}")
            session.status = SessionStatus.FAILED
            session.error_message = str(e)
        
        session.updated_at = datetime.now()
        return session
    
    async def generate_story_stream(
        self,
        session_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成故事
        
        Args:
            session_id: 会话ID
            
        Yields:
            生成过程中的事件
        """
        session = self.sessions.get(session_id)
        if not session:
            yield {"type": "error", "message": f"Session {session_id} not found"}
            return
        
        # 更新状态
        session.status = SessionStatus.PROCESSING
        yield {"type": "status", "status": "processing", "message": "开始生成故事..."}
        
        try:
            # 构建任务描述
            task = self._build_task_description(session)
            
            # 获取讨论引擎
            engine = get_discussion_engine()
            
            # 定义回调函数
            async def callback(event_type: str, data: Dict[str, Any]):
                yield {"type": event_type, **data}
            
            # 运行讨论（这里简化处理，实际应该使用异步生成器）
            result = await engine.run_discussion(task, callback=None)
            
            # 发送各阶段结果
            for round_data in result.rounds:
                yield {
                    "type": "round",
                    "round": round_data.round_number,
                    "proposals": {
                        k: {"summary": v.summary, "confidence": v.confidence}
                        for k, v in round_data.proposals.items()
                    },
                }
            
            # 构建故事
            story = self._build_story_from_result(session_id, result)
            
            # 更新会话
            session.story = story
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.now()
            
            yield {
                "type": "complete",
                "story": story.dict() if story else None,
                "message": "故事生成完成！",
            }
            
        except Exception as e:
            self.logger.error(f"Story generation failed: {e}")
            session.status = SessionStatus.FAILED
            session.error_message = str(e)
            yield {"type": "error", "message": str(e)}
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def _build_task_description(self, session: Session) -> str:
        """构建任务描述"""
        parts = [f"主题：{session.theme}"]
        
        if session.genre:
            parts.append(f"类型：{session.genre}")
        
        if session.constraints:
            constraints_str = ", ".join(f"{k}: {v}" for k, v in session.constraints.items())
            parts.append(f"约束：{constraints_str}")
        
        return "\n".join(parts)
    
    def _build_story_from_result(self, session_id: str, result: Any) -> Optional[Story]:
        """从讨论结果构建故事对象"""
        try:
            proposals = result.final_proposals
            
            # 提取各Agent的输出
            plot_content = proposals.get("plot_agent", {}).content if "plot_agent" in proposals else {}
            character_content = proposals.get("character_agent", {}).content if "character_agent" in proposals else {}
            world_content = proposals.get("world_agent", {}).content if "world_agent" in proposals else {}
            dialogue_content = proposals.get("dialogue_agent", {}).content if "dialogue_agent" in proposals else {}
            
            # 构建故事对象（简化版本，实际应该更详细）
            from app.models.story import (
                StoryOutline, Character, WorldSetting, Dialogue
            )
            
            # 解析大纲
            outline = None
            if plot_content and "title" in plot_content:
                outline = StoryOutline(
                    title=plot_content.get("title", "未命名"),
                    genre=plot_content.get("genre", "未知"),
                    synopsis=plot_content.get("synopsis", ""),
                    acts=plot_content.get("acts", []),
                    themes=plot_content.get("themes", []),
                )
            
            # 解析角色
            characters = []
            if "characters" in character_content:
                for char_data in character_content["characters"]:
                    characters.append(Character(
                        name=char_data.get("name", ""),
                        role=char_data.get("role", "supporting"),
                        age=char_data.get("age"),
                        personality=char_data.get("personality", ""),
                        background=char_data.get("background", ""),
                        motivation=char_data.get("motivation", ""),
                        arc=char_data.get("arc"),
                        relationships=char_data.get("relationships", []),
                    ))
            
            # 解析世界设定
            world_setting = None
            if "world_setting" in world_content:
                ws = world_content["world_setting"]
                world_setting = WorldSetting(
                    era=ws.get("era", ""),
                    location=ws.get("location", ""),
                    rules=ws.get("rules", []),
                    technology_level=ws.get("technology_level"),
                    culture=ws.get("culture"),
                )
            
            # 解析对话
            dialogues = []
            if "dialogues" in dialogue_content:
                for dial_data in dialogue_content["dialogues"]:
                    from app.models.story import DialogueLine
                    content = [
                        DialogueLine(character=line.get("character", ""), line=line.get("line", ""))
                        for line in dial_data.get("content", [])
                    ]
                    dialogues.append(Dialogue(
                        scene=dial_data.get("scene", ""),
                        participants=dial_data.get("participants", []),
                        content=content,
                    ))
            
            return Story(
                id=f"story_{uuid.uuid4().hex[:12]}",
                session_id=session_id,
                title=outline.title if outline else "未命名",
                genre=outline.genre if outline else "未知",
                synopsis=outline.synopsis if outline else "",
                outline=outline,
                characters=characters,
                dialogues=dialogues,
                world_setting=world_setting,
            )
            
        except Exception as e:
            self.logger.error(f"Failed to build story from result: {e}")
            return None


# 全局编排器实例
orchestrator = Orchestrator()


def get_orchestrator() -> Orchestrator:
    """获取编排器实例"""
    return orchestrator

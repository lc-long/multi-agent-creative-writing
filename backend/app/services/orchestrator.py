"""
Orchestrator Service Module

编排器 - 协调整个故事生成流程。
"""

import logging
import uuid
import asyncio
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
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = SessionStatus.PROCESSING
        session.updated_at = datetime.now()
        
        try:
            task = self._build_task_description(session)
            engine = get_discussion_engine()
            result = await engine.run_discussion(task)
            
            story = self._build_story_from_result(session_id, result)
            
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
        流式生成故事，返回生成过程中的事件
        """
        session = self.sessions.get(session_id)
        if not session:
            yield {"type": "error", "data": {"message": f"Session {session_id} not found"}}
            return
        
        session.status = SessionStatus.PROCESSING
        yield {"type": "status", "data": {"message": "开始生成故事..."}}
        
        try:
            task = self._build_task_description(session)
            engine = get_discussion_engine()
            
            # 第一轮：收集提案
            yield {"type": "status", "data": {"message": "各Agent正在提出初始方案..."}}
            
            proposals = await engine._collect_proposals(task)
            
            for agent_id, proposal in proposals.items():
                yield {
                    "type": "proposal",
                    "data": {
                        "agent_id": agent_id,
                        "agent_name": self._get_agent_name(agent_id),
                        "summary": proposal.summary,
                        "confidence": proposal.confidence,
                    }
                }
                await asyncio.sleep(0.1)  # 小延迟，让前端能顺序显示
            
            # 讨论轮次
            for round_num in range(2, engine.max_rounds + 1):
                yield {
                    "type": "round",
                    "data": {"round": round_num}
                }
                
                yield {
                    "type": "status",
                    "data": {"message": f"第{round_num}轮讨论开始..."}
                }
                
                # 收集反馈
                feedback = await engine._collect_feedback(proposals, [])
                
                for fb in feedback:
                    yield {
                        "type": "discussion",
                        "data": {
                            "agent_id": fb.agent_id,
                            "agent_name": self._get_agent_name(fb.agent_id),
                            "content": fb.feedback,
                            "round": round_num,
                            "suggestions": fb.suggestions,
                        }
                    }
                    await asyncio.sleep(0.1)
                
                # 修改提案
                proposals = await engine._revise_proposals(proposals, feedback)
                
                for agent_id, proposal in proposals.items():
                    yield {
                        "type": "proposal",
                        "data": {
                            "agent_id": agent_id,
                            "agent_name": self._get_agent_name(agent_id),
                            "summary": proposal.summary,
                            "confidence": proposal.confidence,
                            "round": round_num,
                        }
                    }
            
            # 构建最终故事
            yield {"type": "status", "data": {"message": "正在生成最终故事..."}}
            
            from app.agents.base import ConsensusResult
            consensus = ConsensusResult(
                reached=True,
                content={},
                summary="讨论完成",
                disagreements=[],
            )
            
            result = type('DiscussionResult', (), {
                'rounds': [],
                'final_proposals': proposals,
                'consensus': consensus,
                'summary': '讨论完成',
            })()
            
            story = self._build_story_from_result(session_id, result)
            
            session.story = story
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.now()
            
            yield {
                "type": "complete",
                "data": {
                    "message": "故事生成完成！",
                    "story": self._serialize_story(story) if story else None,
                }
            }
            
        except Exception as e:
            self.logger.error(f"Story generation failed: {e}")
            session.status = SessionStatus.FAILED
            session.error_message = str(e)
            yield {"type": "error", "data": {"message": str(e)}}
    
    def _get_agent_name(self, agent_id: str) -> str:
        """获取Agent名称"""
        names = {
            "plot_agent": "剧情Agent",
            "character_agent": "人物Agent",
            "world_agent": "世界观Agent",
            "dialogue_agent": "对话Agent",
        }
        return names.get(agent_id, agent_id)
    
    def _serialize_story(self, story: Story) -> Dict[str, Any]:
        """序列化故事对象"""
        return {
            "title": story.title,
            "genre": story.genre,
            "synopsis": story.synopsis,
            "outline": story.outline.dict() if story.outline else None,
            "characters": [c.dict() for c in story.characters],
            "dialogues": [d.dict() for d in story.dialogues],
            "world_setting": story.world_setting.dict() if story.world_setting else None,
        }
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def _build_task_description(self, session: Session) -> str:
        """构建任务描述"""
        parts = [f"主题：{session.theme}"]
        
        if session.genre:
            genre_names = {
                "science_fiction": "科幻",
                "fantasy": "奇幻",
                "realism": "现实",
                "mystery": "悬疑",
                "romance": "爱情",
                "horror": "恐怖",
                "adventure": "冒险",
                "historical": "历史",
            }
            parts.append(f"类型：{genre_names.get(session.genre, session.genre)}")
        
        if session.constraints:
            constraints_str = ", ".join(f"{k}: {v}" for k, v in session.constraints.items())
            parts.append(f"约束：{constraints_str}")
        
        return "\n".join(parts)
    
    def _build_story_from_result(self, session_id: str, result: Any) -> Optional[Story]:
        """从讨论结果构建故事对象"""
        try:
            proposals = result.final_proposals
            
            plot_content = proposals.get("plot_agent", {}).content if "plot_agent" in proposals else {}
            character_content = proposals.get("character_agent", {}).content if "character_agent" in proposals else {}
            world_content = proposals.get("world_agent", {}).content if "world_agent" in proposals else {}
            dialogue_content = proposals.get("dialogue_agent", {}).content if "dialogue_agent" in proposals else {}
            
            from app.models.story import (
                StoryOutline, Character, WorldSetting, Dialogue, Genre
            )
            
            # 中文类型到枚举的映射
            genre_map = {
                "科幻": Genre.SCIENCE_FICTION,
                "奇幻": Genre.FANTASY,
                "现实": Genre.REALISM,
                "悬疑": Genre.MYSTERY,
                "爱情": Genre.ROMANCE,
                "恐怖": Genre.HORROR,
                "冒险": Genre.ADVENTURE,
                "历史": Genre.HISTORICAL,
            }
            
            def parse_genre(genre_str: str) -> Genre:
                """解析类型字符串"""
                if not genre_str:
                    return Genre.SCIENCE_FICTION
                genre_str = str(genre_str)
                if genre_str in [g.value for g in Genre]:
                    return Genre(genre_str)
                return genre_map.get(genre_str, Genre.SCIENCE_FICTION)
            
            outline = None
            if plot_content and "title" in plot_content:
                from app.models.story import ActOutline
                acts = []
                for act_data in plot_content.get("acts", []):
                    acts.append(ActOutline(
                        name=act_data.get("name", ""),
                        description=act_data.get("description", ""),
                        key_events=act_data.get("key_events", []) or [],
                    ))
                
                outline_genre = plot_content.get("genre", "科幻")
                outline = StoryOutline(
                    title=plot_content.get("title", "未命名"),
                    genre=parse_genre(outline_genre),
                    synopsis=plot_content.get("synopsis", ""),
                    acts=acts,
                    themes=plot_content.get("themes", []) or [],
                )
            
            characters = []
            if character_content and "characters" in character_content:
                chars_data = character_content["characters"]
                if isinstance(chars_data, list):
                    for char_data in chars_data:
                        rels = char_data.get("relationships", []) or []
                        if isinstance(rels, list) and len(rels) > 0:
                            if isinstance(rels[0], dict):
                                from app.models.story import CharacterRelationship
                                rels = [CharacterRelationship(**r) for r in rels]
                        age_val = char_data.get("age")
                        if isinstance(age_val, int):
                            pass
                        elif isinstance(age_val, str):
                            try:
                                age_val = int(age_val)
                            except (ValueError, TypeError):
                                age_val = None
                        else:
                            age_val = None
                        characters.append(Character(
                            name=char_data.get("name", ""),
                            role=char_data.get("role", "supporting"),
                            age=age_val,
                            personality=char_data.get("personality", ""),
                            background=char_data.get("background", ""),
                            motivation=char_data.get("motivation", ""),
                            arc=char_data.get("arc"),
                            relationships=rels,
                        ))
            
            # 构建世界设定
            world_setting = None
            if world_content and "world_setting" in world_content:
                ws = world_content["world_setting"]
                world_setting = WorldSetting(
                    era=ws.get("era", "现代") or "现代",
                    location=ws.get("location", "未知") or "未知",
                    rules=ws.get("rules", []) or [],
                    technology_level=ws.get("technology_level"),
                    culture=ws.get("culture"),
                )
            else:
                world_setting = WorldSetting(
                    era="现代",
                    location="未知",
                    rules=[],
                )
            
            dialogues = []
            if dialogue_content and "dialogues" in dialogue_content:
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
                genre=outline.genre if outline else Genre.SCIENCE_FICTION,
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

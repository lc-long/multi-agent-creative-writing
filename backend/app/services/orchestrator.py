import json
import logging
import uuid
import asyncio
import os
import re
from typing import Any, AsyncGenerator, Dict, Optional
from datetime import datetime

from app.models.story import Session, SessionStatus, Story
from app.services.discussion_engine import DiscussionEngine, get_discussion_engine

logger = logging.getLogger(__name__)

SESSION_FILE = os.path.join("data", "sessions.json")


class Orchestrator:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self._generation_tasks: Dict[str, asyncio.Task] = {}
        self._event_queues: Dict[str, asyncio.Queue] = {}
        self.logger = logging.getLogger("orchestrator")
        self._load_sessions()

    def _save_sessions_sync(self) -> None:
        data = {}
        for sid, session in self.sessions.items():
            try:
                data[sid] = session.model_dump(mode="json")
            except Exception:
                data[sid] = session.model_dump()
        os.makedirs("data", exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    async def _save_sessions(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_sessions_sync)

    def _load_sessions(self) -> None:
        try:
            with open(SESSION_FILE) as f:
                raw = json.load(f)
            for sid, sdata in raw.items():
                self.sessions[sid] = Session(**sdata)
            self.logger.info(f"Loaded {len(raw)} persisted sessions")
        except (FileNotFoundError, json.JSONDecodeError):
            self.logger.info("No persisted sessions to load")

    async def create_session(
        self,
        theme: str,
        genre: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Session:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session = Session(
            id=session_id,
            status=SessionStatus.PENDING,
            theme=theme,
            genre=genre,
            constraints=constraints,
        )
        self.sessions[session_id] = session
        self._event_queues[session_id] = asyncio.Queue()
        await self._save_sessions()
        self.logger.info(f"Created session {session_id} for theme: {theme[:50]}...")
        return session

    def start_generation(self, session_id: str) -> None:
        generation_active = (
            session_id in self._generation_tasks
            and not self._generation_tasks[session_id].done()
        )
        if not generation_active:
            self._generation_tasks[session_id] = asyncio.create_task(
                self._run_generation(session_id)
            )

    async def generate_story_stream(
        self, session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        session = self.sessions.get(session_id)
        if not session:
            yield {"type": "error", "data": {"message": f"Session {session_id} not found"}}
            return

        for msg in session.progress_messages:
            yield msg

        if session.status == SessionStatus.COMPLETED:
            yield {
                "type": "complete",
                "data": {
                    "message": "故事生成完成！",
                    "story": self._serialize_story(session.story) if session.story else None,
                },
            }
            return

        if session.status == SessionStatus.FAILED:
            yield {"type": "error", "data": {"message": session.error_message or "生成失败"}}
            return

        if session.status == SessionStatus.PENDING:
            self.start_generation(session_id)

        queue = self._event_queues.get(session_id)
        if queue is None:
            yield {"type": "error", "data": {"message": "事件队列未初始化"}}
            return

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=10.0)
            except asyncio.TimeoutError:
                if session.status in (SessionStatus.COMPLETED, SessionStatus.FAILED):
                    break
                yield {"type": "heartbeat", "data": {"message": "generation in progress"}}
                continue
            if event is None:
                break
            yield event
            if event["type"] in ("complete", "error"):
                break

    async def _run_generation(self, session_id: str) -> None:
        session = self.sessions[session_id]
        queue = self._event_queues[session_id]
        session.status = SessionStatus.PROCESSING

        async def emit(event_type: str, data: Dict[str, Any]) -> None:
            event = {"type": event_type, "data": data}
            session.progress_messages.append(event)
            await queue.put(event)
            await self._save_sessions()

        try:
            task = self._build_task_description(session)
            engine = get_discussion_engine()

            # =========================================================
            # Phase 1: Brainstorm — plot + world in parallel
            # =========================================================
            await emit("status", {"message": "Phase 1/5: 各Agent正在脑暴初始方案..."})

            plot_agent = engine.agents["plot_agent"]
            world_agent = engine.agents["world_agent"]

            plot_task = asyncio.create_task(plot_agent.propose(task, None))
            world_task = asyncio.create_task(world_agent.propose(task, None))

            await emit("thinking", {"agent_id": "plot_agent", "agent_name": "剧情Agent", "content": "剧情Agent正在构思故事框架和角色需求..."})
            await emit("thinking", {"agent_id": "world_agent", "agent_name": "世界观Agent", "content": "世界观Agent正在构思世界观草案..."})

            plot_result, world_result = await asyncio.gather(plot_task, world_task)

            proposals = {}

            if plot_result:
                proposals["plot_agent"] = plot_result
                await emit("proposal", {
                    "agent_id": "plot_agent",
                    "agent_name": "剧情Agent",
                    "summary": plot_result.summary,
                    "confidence": plot_result.confidence,
                    "content": plot_result.content,
                })

            if world_result:
                proposals["world_agent"] = world_result
                await emit("proposal", {
                    "agent_id": "world_agent",
                    "agent_name": "世界观Agent",
                    "summary": world_result.summary,
                    "confidence": world_result.confidence,
                    "content": world_result.content,
                })

            # =========================================================
            # Phase 2: Integration — build unified blueprint
            # =========================================================
            await emit("status", {"message": "Phase 2/5: 正在整合为统一故事蓝图..."})

            blueprint = self._build_blueprint(plot_result, world_result)
            await emit("blueprint", {
                "title": blueprint.get("title", ""),
                "genre": blueprint.get("genre", ""),
                "synopsis": blueprint.get("synopsis", ""),
                "core_conflict": blueprint.get("core_conflict", ""),
                "characters": blueprint.get("characters", []),
                "world_summary": blueprint.get("world_summary", ""),
            })

            # =========================================================
            # Phase 3: Detailed creation — all 4 agents in parallel
            # =========================================================
            await emit("status", {"message": "Phase 3/5: 各Agent正在基于蓝图进行详细创作..."})

            plot_context = {"phase": "creation", "blueprint": blueprint}
            char_context = {"phase": "creation", "blueprint": blueprint}
            world_context = {"phase": "creation", "blueprint": blueprint}
            dial_context = {"phase": "creation", "blueprint": blueprint}

            tasks = {
                "plot_agent": asyncio.create_task(plot_agent.propose(task, plot_context)),
                "character_agent": asyncio.create_task(engine.agents["character_agent"].propose(task, char_context)),
                "world_agent": asyncio.create_task(world_agent.propose(task, world_context)),
                "dialogue_agent": asyncio.create_task(engine.agents["dialogue_agent"].propose(task, dial_context)),
            }

            for aid, t in tasks.items():
                await emit("thinking", {
                    "agent_id": aid,
                    "agent_name": self._get_agent_name(aid),
                    "content": f"{self._get_agent_name(aid)}正在根据蓝图进行详细创作...",
                })

            detailed_results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            for aid, result in zip(tasks.keys(), detailed_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Detailed creation failed for {aid}: {result}")
                    await emit("error", {"message": f"{self._get_agent_name(aid)}详细创作失败: {str(result)}"})
                    continue
                proposals[aid] = result
                await emit("proposal", {
                    "agent_id": aid,
                    "agent_name": self._get_agent_name(aid),
                    "summary": result.summary,
                    "confidence": result.confidence,
                    "content": result.content,
                })

            # =========================================================
            # Phase 4: Iterative cross review — loop until resolved
            # =========================================================
            await emit("status", {"message": "Phase 4/5: 正在进行交叉审阅..."})

            max_review_rounds = 2
            for review_round in range(1, max_review_rounds + 1):
                if review_round > 1:
                    await emit("status", {"message": f"审阅第{review_round}轮：仍有未解决的问题..."})

                feedback_list = []
                for agent_id, agent in engine.agents.items():
                    if agent_id not in proposals:
                        continue
                    await emit("thinking", {
                        "agent_id": agent_id,
                        "agent_name": self._get_agent_name(agent_id),
                        "content": f"{self._get_agent_name(agent_id)}正在审阅其他Agent的成果...",
                    })
                    try:
                        feedback = await agent.review(proposals, [])
                    except Exception as e:
                        self.logger.error(f"Review failed for {agent_id}: {e}")
                        continue
                    feedback_list.append(feedback)
                    target_name = self._get_agent_name(feedback.target_agent) if feedback.target_agent else "其他Agent"
                    await emit("discussion", {
                        "agent_id": agent_id,
                        "agent_name": self._get_agent_name(agent_id),
                        "content": f"对{target_name}的审阅意见：{feedback.feedback}",
                        "suggestions": feedback.suggestions,
                        "target_agent": feedback.target_agent,
                    })

                # 检查是否还有 critical / major 问题
                critical_issues = [
                    iss for fb in feedback_list
                    for iss in (fb.issues or [])
                    if iss.severity in ("critical", "major")
                ]
                if not critical_issues:
                    await emit("status", {"message": "审阅通过，无重大问题"})
                    break

                await emit("status", {"message": f"发现 {len(critical_issues)} 个需要修改的问题，正在进行修改..."})

                # Revise based on feedback
                for agent_id, agent in engine.agents.items():
                    agent_feedback = [f for f in feedback_list if f.target_agent == agent_id]
                    if agent_feedback and agent_id in proposals:
                        await emit("thinking", {
                            "agent_id": agent_id,
                            "agent_name": self._get_agent_name(agent_id),
                            "content": f"{self._get_agent_name(agent_id)}正在根据审阅意见进行修改...",
                        })
                        try:
                            revised = await agent.revise(agent_feedback, proposals[agent_id])
                            proposals[agent_id] = revised
                            await emit("proposal", {
                                "agent_id": agent_id,
                                "agent_name": self._get_agent_name(agent_id),
                                "summary": revised.summary,
                                "confidence": revised.confidence,
                                "content": revised.content,
                            })
                        except Exception as e:
                            self.logger.error(f"Revision failed for {agent_id}: {e}")

            # =========================================================
            # Phase 5: Final assembly
            # =========================================================
            await emit("status", {"message": "Phase 5/5: 正在生成最终故事..."})

            from app.agents.base import ConsensusResult
            consensus = ConsensusResult(
                reached=True, content={}, summary="讨论完成", disagreements=[]
            )
            result = type('DiscussionResult', (), {
                'rounds': [],
                'final_proposals': proposals,
                'consensus': consensus,
                'summary': '创作完成',
            })()
            story = self._build_story_from_result(session_id, result)

            session.story = story
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.now()

            story_data = self._serialize_story(story) if story else None
            await emit("complete", {
                "message": "故事生成完成！",
                "story": story_data,
            })

        except Exception as e:
            self.logger.error(f"Story generation failed: {e}")
            session.status = SessionStatus.FAILED
            session.error_message = str(e)
            await emit("error", {"message": str(e)})

        await queue.put(None)

    def _build_blueprint(self, plot_result, world_result) -> Dict[str, Any]:
        blueprint = {
            "title": "",
            "genre": "",
            "synopsis": "",
            "core_conflict": "",
            "characters": [],
            "world_summary": "",
        }

        if plot_result and plot_result.content:
            pc = plot_result.content
            blueprint["title"] = pc.get("title", "")
            blueprint["genre"] = pc.get("genre", "")
            blueprint["synopsis"] = pc.get("synopsis", "")
            blueprint["core_conflict"] = pc.get("core_conflict", "")

            # Extract character names from acts
            seen = set()
            for act in pc.get("acts", []):
                for evt in act.get("key_events", []):
                    # Find quoted names like 「张三」 or "张三"
                    names = re.findall(r'[「""]([^「」""]{1,8})[」""]', str(evt))
                    for n in names:
                        if n not in seen:
                            seen.add(n)
                            blueprint["characters"].append({
                                "name": n,
                                "role": "未知",
                                "description": "",
                            })

        if world_result and world_result.content:
            ws = world_result.content.get("world_setting", {})
            parts = []
            if ws.get("era"):
                parts.append(f"时代：{ws['era']}")
            if ws.get("location"):
                parts.append(f"地点：{ws['location']}")
            if ws.get("rules"):
                parts.append(f"规则：{'；'.join(ws['rules'][:3])}")
            blueprint["world_summary"] = "；".join(parts)

        return blueprint

    def _get_agent_name(self, agent_id: str) -> str:
        names = {
            "plot_agent": "剧情Agent",
            "character_agent": "人物Agent",
            "world_agent": "世界观Agent",
            "dialogue_agent": "对话Agent",
        }
        return names.get(agent_id, agent_id)

    def _serialize_story(self, story: Story) -> Dict[str, Any]:
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
        return self.sessions.get(session_id)

    def _build_task_description(self, session: Session) -> str:
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
            constraints_str = ", ".join(
                f"{k}: {v}" for k, v in session.constraints.items()
            )
            parts.append(f"约束：{constraints_str}")
        return "\n".join(parts)

    def _build_story_from_result(self, session_id: str, result: Any) -> Optional[Story]:
        try:
            proposals = result.final_proposals

            plot_content = (
                proposals.get("plot_agent", {}).content
                if "plot_agent" in proposals
                else {}
            )
            character_content = (
                proposals.get("character_agent", {}).content
                if "character_agent" in proposals
                else {}
            )
            world_content = (
                proposals.get("world_agent", {}).content
                if "world_agent" in proposals
                else {}
            )
            dialogue_content = (
                proposals.get("dialogue_agent", {}).content
                if "dialogue_agent" in proposals
                else {}
            )

            from app.models.story import (
                StoryOutline,
                Character,
                WorldSetting,
                Dialogue,
                Genre,
            )

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
                    acts.append(
                        ActOutline(
                            name=act_data.get("name", ""),
                            description=act_data.get("description", ""),
                            key_events=act_data.get("key_events", []) or [],
                        )
                    )

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
                        characters.append(
                            Character(
                                name=char_data.get("name", ""),
                                role=char_data.get("role", "supporting"),
                                age=age_val,
                                personality=char_data.get("personality", ""),
                                background=char_data.get("background", ""),
                                motivation=char_data.get("motivation", ""),
                                arc=char_data.get("arc"),
                                relationships=rels,
                            )
                        )

            world_setting = None
            if world_content and isinstance(world_content, dict):
                ws = world_content.get("world_setting")
                if isinstance(ws, dict):
                    try:
                        world_setting = WorldSetting(
                            era=str(ws.get("era", "现代") or "现代"),
                            location=str(ws.get("location", "未知") or "未知"),
                            rules=[str(r) for r in (ws.get("rules", []) or [])],
                            technology_level=str(ws["technology_level"]) if ws.get("technology_level") else None,
                            culture=str(ws["culture"]) if ws.get("culture") else None,
                        )
                    except Exception:
                        world_setting = WorldSetting(era="现代", location="未知", rules=[])
                else:
                    world_setting = WorldSetting(era="现代", location="未知", rules=[])
            else:
                world_setting = WorldSetting(era="现代", location="未知", rules=[])

            dialogues = []
            if dialogue_content and "dialogues" in dialogue_content:
                for dial_data in dialogue_content["dialogues"]:
                    from app.models.story import DialogueLine
                    content = [
                        DialogueLine(
                            character=line.get("character", ""),
                            line=line.get("line", ""),
                        )
                        for line in dial_data.get("content", [])
                    ]
                    dialogues.append(
                        Dialogue(
                            scene=dial_data.get("scene", ""),
                            participants=dial_data.get("participants", []),
                            content=content,
                        )
                    )

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


orchestrator = Orchestrator()


def get_orchestrator() -> Orchestrator:
    return orchestrator

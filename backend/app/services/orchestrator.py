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
                self._event_queues[sid] = asyncio.Queue()
            self.logger.info(f"Loaded {len(raw)} persisted sessions with queues")
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

        pipeline = [
            ("brainstorm",   {"agents": ["plot_agent", "world_agent"], "mode": "parallel"}),
            ("integrate",    {}),
            ("create",       {"agents": list(get_discussion_engine().agents.keys()), "mode": "parallel", "context": "blueprint"}),
            ("review",       {"max_rounds": 2}),
            ("assemble",     {}),
            ("narrate",      {}),
        ]

        try:
            task = self._build_task_description(session)
            engine = get_discussion_engine()
            proposals: Dict[str, Any] = {}
            blueprint: Dict[str, Any] = {}
            total = len(pipeline)

            for idx, (phase, cfg) in enumerate(pipeline, 1):
                name = {"brainstorm": "脑暴", "integrate": "整合蓝图", "create": "详细创作", "review": "交叉审阅", "assemble": "组装故事", "narrate": "撰写完整故事"}.get(phase, phase)
                await emit("status", {"message": f"Phase {idx}/{total}: {name}..."})

                if phase == "brainstorm":
                    await self._phase_run_agents(engine, cfg["agents"], task, None, proposals, emit, cfg["mode"])

                elif phase == "integrate":
                    blueprint = self._build_blueprint(
                        proposals.get("plot_agent"),
                        proposals.get("world_agent"),
                    )
                    await emit("blueprint", {
                        "title": blueprint.get("title", ""),
                        "genre": blueprint.get("genre", ""),
                        "synopsis": blueprint.get("synopsis", ""),
                        "core_conflict": blueprint.get("core_conflict", ""),
                        "characters": blueprint.get("characters", []),
                        "world_summary": blueprint.get("world_summary", ""),
                    })

                elif phase == "create":
                    ctx = {"phase": "creation", "blueprint": blueprint}
                    await self._phase_run_agents(engine, cfg["agents"], task, ctx, proposals, emit, cfg["mode"])

                elif phase == "review":
                    await self._phase_review(engine, proposals, emit, cfg.get("max_rounds", 2))

                elif phase == "assemble":
                    story = self._build_story_from_result(session_id, proposals)
                    session.story = story

                elif phase == "narrate":
                    if session.story:
                        narrative = await self._phase_narrate(engine, session.story, emit)
                        session.story.narrative = narrative

                    session.status = SessionStatus.COMPLETED
                    session.completed_at = datetime.now()
                    story_data = self._serialize_story(session.story) if session.story else None
                    await emit("complete", {"message": "故事生成完成！", "story": story_data})

        except Exception as e:
            self.logger.error(f"Story generation failed: {e}")
            session.status = SessionStatus.FAILED
            session.error_message = str(e)
            await emit("error", {"message": str(e)})

        await queue.put(None)

    async def _phase_run_agents(
        self, engine, agent_ids: list, task: str, context: dict | None,
        proposals: dict, emit, mode: str = "parallel",
    ) -> None:
        agents_to_run = [(aid, engine.agents[aid]) for aid in agent_ids if aid in engine.agents]

        if mode == "parallel":
            async def run_one(aid, agent):
                await emit("thinking", {"agent_id": aid, "agent_name": self._get_agent_name(aid), "content": f"{self._get_agent_name(aid)}正在创作..."})
                try:
                    result = await agent.propose(task, context)
                    if result:
                        proposals[aid] = result
                        await emit("proposal", {"agent_id": aid, "agent_name": self._get_agent_name(aid), "summary": result.summary, "confidence": result.confidence, "content": result.content})
                except Exception as e:
                    self.logger.error(f"Agent {aid} failed: {e}")

            tasks = [asyncio.create_task(run_one(aid, agent)) for aid, agent in agents_to_run]
            await asyncio.gather(*tasks)
        else:
            for aid, agent in agents_to_run:
                await run_one(aid, agent)

    async def _phase_review(self, engine, proposals: dict, emit, max_rounds: int = 2) -> None:
        for review_round in range(1, max_rounds + 1):
            if review_round > 1:
                await emit("status", {"message": f"审阅第{review_round}轮：仍有未解决的问题..."})

            feedback_list = []
            for agent_id, agent in engine.agents.items():
                if agent_id not in proposals:
                    continue
                await emit("thinking", {"agent_id": agent_id, "agent_name": self._get_agent_name(agent_id), "content": f"{self._get_agent_name(agent_id)}正在审阅其他Agent的成果..."})
                try:
                    feedback = await agent.review(proposals, [])
                except Exception as e:
                    self.logger.error(f"Review failed for {agent_id}: {e}")
                    continue
                feedback_list.append(feedback)
                target_name = self._get_agent_name(feedback.target_agent) if feedback.target_agent else "其他Agent"
                await emit("discussion", {"agent_id": agent_id, "agent_name": self._get_agent_name(agent_id), "content": f"对{target_name}的审阅意见：{feedback.feedback}", "suggestions": feedback.suggestions, "target_agent": feedback.target_agent})

            critical = [iss for fb in feedback_list for iss in (fb.issues or []) if iss.severity in ("critical", "major")]
            if not critical:
                await emit("status", {"message": "审阅通过，无重大问题"})
                return

            await emit("status", {"message": f"发现 {len(critical)} 个需要修改的问题，正在进行修改..."})
            for agent_id, agent in engine.agents.items():
                agent_feedback = [f for f in feedback_list if f.target_agent == agent_id]
                if agent_feedback and agent_id in proposals:
                    await emit("thinking", {"agent_id": agent_id, "agent_name": self._get_agent_name(agent_id), "content": f"{self._get_agent_name(agent_id)}正在根据审阅意见进行修改..."})
                    try:
                        revised = await agent.revise(agent_feedback, proposals[agent_id])
                        proposals[agent_id] = revised
                        await emit("proposal", {"agent_id": agent_id, "agent_name": self._get_agent_name(agent_id), "summary": revised.summary, "confidence": revised.confidence, "content": revised.content})
                    except Exception as e:
                        self.logger.error(f"Revision failed for {agent_id}: {e}")

                    except Exception as e:
                        self.logger.error(f"Revision failed for {agent_id}: {e}")

    async def _phase_narrate(self, engine, story, emit) -> str:
        """调用 LLM 将故事组件合成完整叙事文本"""
        from app.agents.prompts import narrate
        from app.agents.base import BaseAgent

        # 构建故事组件 dict
        components = {
            "title": story.title,
            "genre": story.genre,
            "synopsis": story.synopsis,
            "acts": [
                {"name": a.name, "description": a.description, "key_events": a.key_events}
                for a in (story.outline.acts if story.outline else [])
            ],
            "characters": [
                {"name": c.name, "role": c.role, "personality": c.personality,
                 "background": c.background, "motivation": c.motivation}
                for c in story.characters
            ],
            "world_setting": {
                "era": story.world_setting.era if story.world_setting else "",
                "location": story.world_setting.location if story.world_setting else "",
                "rules": story.world_setting.rules if story.world_setting else [],
                "culture": story.world_setting.culture if story.world_setting else "",
            },
            "dialogues": [
                {"scene": d.scene, "content": [{"character": l.character, "line": l.line} for l in d.content]}
                for d in story.dialogues
            ],
        }

        prompt = narrate(components)

        # 用任意一个 agent 的 call_llm
        agent = next(iter(engine.agents.values()))

        await emit("thinking", {
            "agent_id": "narrator",
            "agent_name": "叙事引擎",
            "content": "正在将所有组件合成为完整故事...",
        })

        try:
            response = await agent.call_llm(
                [{"role": "user", "content": prompt}],
                max_tokens=8000,
            )
            # 清理 think 块
            import re
            narrative = re.sub(r'<think>.*?(?:</think>|$)', '', response, flags=re.DOTALL).strip()
            if not narrative:
                narrative = response.strip()
            return narrative
        except Exception as e:
            self.logger.error(f"Narrative generation failed: {e}")
            return ""

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

            # Use plot_agent's structured character list if available
            plot_chars = pc.get("characters", [])
            if plot_chars:
                for c in plot_chars:
                    if isinstance(c, dict) and c.get("name"):
                        blueprint["characters"].append({
                            "name": c["name"],
                            "role": c.get("role", "未知"),
                            "description": c.get("description", ""),
                        })

            # Fallback: extract character names from acts
            if not blueprint["characters"]:
                seen = set()
                for act in pc.get("acts", []):
                    for evt in act.get("key_events", []):
                        evt_str = str(evt)
                        names = re.findall(r'[「""\u2018\u2019\']([^「」""\u2018\u2019\']{1,8})[」""\u2018\u2019\']', evt_str)
                        for n in names:
                            n = n.strip()
                            if n and n not in seen:
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
            "narrative": story.narrative,
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

    def _build_story_from_result(self, session_id: str, proposals: Dict[str, Any]) -> Optional[Story]:
        try:
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

"""
Prompt Templates

所有Agent的提示词模板集中管理。每个函数返回完整 prompt 字符串。
"""

from typing import Any, Dict, List, Optional
import json


def plot_propose_brainstorm(task: str, context: Optional[Dict] = None) -> str:
    parts = [f"请为以下主题设计一个故事结构：\n\n{task}"]
    if context:
        parts.append(f"\n\n额外约束：{json.dumps(context, ensure_ascii=False)}")
    parts.append("""

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
}""")
    return "".join(parts)


def plot_propose_creation(task: str, blueprint: Dict) -> str:
    chars_desc = "\n".join(
        f"  - {c['name']}（{c.get('role','?')}）: {c.get('description','')}"
        for c in blueprint.get("characters", [])
    )
    return f"""请基于以下统一故事蓝图，进行详细的故事结构创作：

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


def plot_review(proposals_json: str, discussion_json: str) -> str:
    return f"""请从剧情角度review以下方案：

{proposals_json}
{discussion_json}
请从剧情角度给出结构化反馈，以JSON格式输出：
{{
    "feedback": "总体反馈内容",
    "suggestions": ["建议1", "建议2"],
    "agreement": true,
    "issues": [
        {{
            "target_agent": "存在问题的Agent ID",
            "severity": "critical/major/minor",
            "description": "问题描述",
            "suggestion": "改进建议"
        }}
    ]
}}"""


def plot_revise(current_json: str, feedback_text: str) -> str:
    return f"""当前的故事结构方案：
{current_json}

收到的反馈：
{feedback_text}

请根据反馈修改故事结构，保持JSON格式输出。
如果反馈合理，请做出相应调整；如果不合理，请保持原方案并说明理由。"""


# ── character agent ──

def char_propose_brainstorm(task: str, context: Optional[Dict] = None) -> str:
    parts = [f"请为以下故事设计角色：\n\n{task}"]
    if context:
        parts.append(f"\n\n故事结构：\n{json.dumps(context, ensure_ascii=False)}")
    parts.append("""

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
}""")
    return "".join(parts)


def char_propose_creation(task: str, blueprint: Dict) -> str:
    chars_list = "\n".join(
        f"  - {c['name']}（{c.get('role','?')}）: {c.get('description','')}"
        for c in blueprint.get("characters", [])
    )
    return f"""请基于以下统一故事蓝图，进行详细的角色设计：

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


def char_review(proposals_json: str, discussion_json: str) -> str:
    return f"""请从角色设计角度review以下方案：

{proposals_json}
{discussion_json}
请给出结构化反馈，以JSON格式输出：
{{
    "feedback": "总体反馈内容",
    "suggestions": ["建议1", "建议2"],
    "agreement": true,
    "issues": [
        {{
            "target_agent": "存在问题的Agent ID",
            "severity": "critical/major/minor",
            "description": "问题描述",
            "suggestion": "改进建议"
        }}
    ]
}}"""


def char_revise(current_json: str, feedback_text: str) -> str:
    return f"""当前的角色设计方案：
{current_json}

收到的反馈：
{feedback_text}

请根据反馈修改角色设计，保持JSON格式输出。
重点关注：
- 角色是否符合故事需要
- 角色关系是否合理
- 角色成长弧线是否清晰"""


# ── world agent ──

def world_propose_brainstorm(task: str, context: Optional[Dict] = None) -> str:
    parts = [f"请为以下故事设计世界观：\n\n{task}"]
    if context:
        parts.append(f"\n\n故事结构和角色：\n{json.dumps(context, ensure_ascii=False)}")
    parts.append("""

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
}""")
    return "".join(parts)


def world_propose_creation(task: str, blueprint: Dict) -> str:
    return f"""请基于以下统一故事蓝图，完善世界观设定：

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


def world_review(proposals_json: str, discussion_json: str) -> str:
    return f"""请从世界观角度review以下方案：

{proposals_json}
{discussion_json}
请给出结构化反馈，以JSON格式输出：
{{
    "feedback": "总体反馈内容",
    "suggestions": ["建议1", "建议2"],
    "agreement": true,
    "issues": [
        {{
            "target_agent": "存在问题的Agent ID",
            "severity": "critical/major/minor",
            "description": "问题描述",
            "suggestion": "改进建议"
        }}
    ]
}}"""


def world_revise(current_json: str, feedback_text: str) -> str:
    return f"""当前的世界观设定：
{current_json}

收到的反馈：
{feedback_text}

请根据反馈修改世界观设定，保持JSON格式输出。
重点关注：
- 设定是否服务于故事主题
- 规则是否自洽
- 是否与角色设定兼容"""


# ── dialogue agent ──

def dial_propose_brainstorm(task: str, context: Optional[Dict] = None) -> str:
    parts = [f"请为以下故事设计对话：\n\n{task}"]
    if context:
        parts.append(f"\n\n故事结构和角色信息：\n{json.dumps(context, ensure_ascii=False)}")
    parts.append("""

请设计2-3个关键对话场景，以JSON格式输出：
{
    "dialogues": [
        {
            "scene": "场景描述",
            "participants": ["角色1", "角色2"],
            "content": [
                {"character": "角色1", "line": "台词"},
                {"character": "角色2", "line": "台词"}
            ]
        }
    ]
}""")
    return "".join(parts)


def dial_propose_creation(task: str, blueprint: Dict) -> str:
    chars_desc = "\n".join(
        f"  - {c['name']}（{c.get('role','?')}）"
        for c in blueprint.get("characters", [])
    )
    return f"""请基于以下统一故事蓝图，设计关键对话场景：

【主题】
{task}

【故事蓝图】
标题：{blueprint.get('title','')}
类型：{blueprint.get('genre','')}
简介：{blueprint.get('synopsis','')}
核心冲突：{blueprint.get('core_conflict','')}
世界观：{blueprint.get('world_summary','')}

【角色列表】
{chars_desc or '  无'}

请设计2-4个关键对话场景，每个场景要贴合故事的核心冲突和角色关系。
以JSON格式输出：
{{
    "dialogues": [
        {{
            "scene": "场景描述（发生在剧情的哪个阶段）",
            "participants": ["角色1", "角色2"],
            "content": [
                {{"character": "角色1", "line": "台词"}},
                {{"character": "角色2", "line": "台词"}}
            ]
        }}
    ]
}}

要求：
- 对话要符合角色性格
- 通过对话展现角色关系和核心冲突
- 对话要有张力和感染力"""


def dial_review(proposals_json: str, discussion_json: str) -> str:
    return f"""请从对话设计角度review以下方案：

{proposals_json}
{discussion_json}
请给出结构化反馈，以JSON格式输出：
{{
    "feedback": "总体反馈内容",
    "suggestions": ["建议1", "建议2"],
    "agreement": true,
    "issues": [
        {{
            "target_agent": "存在问题的Agent ID",
            "severity": "critical/major/minor",
            "description": "问题描述",
            "suggestion": "改进建议"
        }}
    ]
}}"""


def dial_revise(current_json: str, feedback_text: str) -> str:
    return f"""当前的对话设计方案：
{current_json}

收到的反馈：
{feedback_text}

请根据反馈修改对话设计，保持JSON格式输出。
重点关注：
- 对话是否符合角色性格
- 对话是否推动剧情
- 对话是否有感染力"""


# ── lookups ──

PROMPTS = {
    "plot_agent": {
        "propose_brainstorm": plot_propose_brainstorm,
        "propose_creation": plot_propose_creation,
        "review": plot_review,
        "revise": plot_revise,
    },
    "character_agent": {
        "propose_brainstorm": char_propose_brainstorm,
        "propose_creation": char_propose_creation,
        "review": char_review,
        "revise": char_revise,
    },
    "world_agent": {
        "propose_brainstorm": world_propose_brainstorm,
        "propose_creation": world_propose_creation,
        "review": world_review,
        "revise": world_revise,
    },
    "dialogue_agent": {
        "propose_brainstorm": dial_propose_brainstorm,
        "propose_creation": dial_propose_creation,
        "review": dial_review,
        "revise": dial_revise,
    },
}


def get_prompt(agent_id: str, method: str, **kwargs) -> str:
    """获取指定Agent的提示词模板并填充参数"""
    fn = PROMPTS[agent_id][method]
    return fn(**kwargs)


def narrate(story_components: Dict[str, Any]) -> str:
    """根据故事组件生成完整故事正文的提示词"""
    title = story_components.get("title", "未命名故事")
    genre = story_components.get("genre", "")
    synopsis = story_components.get("synopsis", "")

    acts_text = ""
    for i, act in enumerate(story_components.get("acts", []), 1):
        acts_text += f"\n第{i}幕：{act.get('name', '')} — {act.get('description', '')}\n"
        for evt in act.get("key_events", []):
            acts_text += f"  · {evt}\n"

    chars_text = ""
    for c in story_components.get("characters", []):
        chars_text += f"\n- {c.get('name', '未知')}（{c.get('role', '未知')}）：{c.get('personality', '')}；背景：{c.get('background', '')}；动机：{c.get('motivation', '')}\n"

    world = story_components.get("world_setting", {})
    world_text = ""
    if world.get("era"):
        world_text += f"时代：{world['era']}\n"
    if world.get("location"):
        world_text += f"地点：{world['location']}\n"
    if world.get("rules"):
        world_text += "规则：" + "；".join(world["rules"][:5]) + "\n"
    if world.get("culture"):
        world_text += f"文化：{world['culture']}\n"

    dialogues_text = ""
    for d in story_components.get("dialogues", []):
        dialogues_text += f"\n场景：{d.get('scene', '')}\n"
        for line in d.get("content", []):
            dialogues_text += f"  {line.get('character', '')}：{line.get('line', '')}\n"

    return f"""请根据以下故事要素，创作一个完整的故事正文（不少于2000字）。

【故事标题】{title}
【类型】{genre}
【简介】{synopsis}

【故事大纲】{acts_text}

【角色设定】{chars_text}

【世界观】{world_text}

【关键对话场景】{dialogues_text}

要求：
1. 写一个完整的故事正文，从头到尾，不少于2000字
2. 按照大纲的幕结构顺序展开叙事
3. 角色性格要与设定一致，对话要符合角色说话风格
4. 世界观设定要自然融入故事叙述中
5. 关键对话场景要包含在故事中，用对话推动情节
6. 结局要与大纲一致，留有余韵
7. 直接输出故事正文，不要写概述或元评论"""

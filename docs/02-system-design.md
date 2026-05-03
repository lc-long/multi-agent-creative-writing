# 多Agent创意写作系统 - 系统设计文档

> 文档版本：v1.0  
> 创建日期：2024  
> 文档状态：已评审

---

## 1. 技术选型

### 1.1 技术栈总览

```
┌─────────────────────────────────────────────────────────────┐
│                        前端                                  │
├─────────────────────────────────────────────────────────────┤
│  框架: Next.js 14 (App Router)                              │
│  语言: TypeScript                                           │
│  UI库: Tailwind CSS + shadcn/ui                             │
│  状态管理: Zustand                                          │
│  HTTP客户端: Axios                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        后端                                  │
├─────────────────────────────────────────────────────────────┤
│  框架: FastAPI                                              │
│  语言: Python 3.11+                                         │
│  LLM框架: LangChain / 自定义Agent框架                       │
│  异步: asyncio                                              │
│  任务队列: Celery (可选，用于长任务)                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        存储层                                │
├─────────────────────────────────────────────────────────────┤
│  数据库: SQLite (开发) / PostgreSQL (生产)                   │
│  缓存: Redis (可选)                                         │
│  文件存储: 本地文件系统                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        LLM层                                 │
├─────────────────────────────────────────────────────────────┤
│  API: OpenAI兼容接口 (GPT-4, Claude, 本地模型等)            │
│  Embedding: text-embedding-3-small (可选)                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术选型理由

| 组件 | 选择 | 理由 |
|------|------|------|
| **前端框架** | Next.js 14 | React生态成熟，SSR支持，App Router现代化 |
| **UI库** | Tailwind + shadcn/ui | 开发效率高，组件质量好，易于定制 |
| **后端框架** | FastAPI | 异步支持好，自动API文档，Python生态 |
| **LLM框架** | LangChain | Agent抽象成熟，社区活跃，易于扩展 |
| **数据库** | SQLite/PostgreSQL | 开发简单，生产可靠 |
| **语言** | TypeScript + Python | 前后端分离，各自最优选择 |

### 1.3 备选方案对比

**后端框架对比：**

| 框架 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| FastAPI | 异步好，自动文档，性能高 | 相对较新 | ✅ 选用 |
| Flask | 简单，生态成熟 | 异步支持弱 | ❌ |
| Django | 功能全，ORM好 | 太重，不适合API服务 | ❌ |

**LLM框架对比：**

| 框架 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| LangChain | Agent抽象好，社区活跃 | 版本变化快，有时过度封装 | ✅ 选用 |
| LlamaIndex | RAG专精 | Agent支持弱 | ❌ |
| 自定义 | 完全控制 | 开发成本高 | 备选 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              用户界面层                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Next.js Frontend                            │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
│  │  │输入组件 │ │大纲展示 │ │角色卡片 │ │对话展示 │ │讨论过程 │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP/REST API
                                      ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              API网关层                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     FastAPI Application                         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
│  │  │/stories │ │/agents  │ │/sessions│ │/export  │ │/health  │  │   │
│  │  │Endpoint │ │Endpoint │ │Endpoint │ │Endpoint │ │Endpoint │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              业务逻辑层                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Orchestrator Service                        │   │
│  │                                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │              Agent Manager                               │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │   │
│  │  │  │剧情Agent │ │人物Agent │ │对话Agent │ │世界观Agent│  │   │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  │                              │                                  │   │
│  │                              ↓                                  │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │              Discussion Engine                           │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐               │   │   │
│  │  │  │讨论管理  │ │消息路由  │ │共识检测  │               │   │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘               │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              基础设施层                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   LLM层     │  │   数据库    │  │    缓存     │  │   文件存储  │  │
│  │  OpenAI API │  │  SQLite/PG  │  │   Redis     │  │   本地/云   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 分层架构说明

| 层次 | 职责 | 主要组件 |
|------|------|---------|
| **用户界面层** | 展示数据，接收用户输入 | Next.js页面、组件 |
| **API网关层** | 路由请求，参数校验，错误处理 | FastAPI路由 |
| **业务逻辑层** | 核心业务逻辑，Agent协作 | Orchestrator、Agent Manager |
| **基础设施层** | 数据存储，外部服务调用 | 数据库、LLM API |

### 2.3 部署架构

**开发环境：**
```
┌─────────────────────────────────────────┐
│              本地开发环境                 │
│  ┌─────────────┐    ┌─────────────┐    │
│  │  Next.js    │    │   FastAPI   │    │
│  │  :3000      │    │   :8000     │    │
│  └─────────────┘    └─────────────┘    │
│                            │            │
│                     ┌──────┴──────┐    │
│                     │   SQLite    │    │
│                     │  本地文件   │    │
│                     └─────────────┘    │
└─────────────────────────────────────────┘
```

**生产环境：**
```
┌─────────────────────────────────────────────────────────────────┐
│                        生产环境                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Nginx     │    │  Next.js    │    │   FastAPI   │        │
│  │  反向代理   │───→│  前端服务   │    │   后端服务  │        │
│  │  :80/443   │    │  :3000      │    │   :8000     │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                              │                  │
│                           ┌──────────────────┴──────────────┐  │
│                           │                                  │  │
│                    ┌──────┴──────┐    ┌─────────────┐       │  │
│                    │ PostgreSQL  │    │   Redis     │       │  │
│                    │   数据库    │    │    缓存     │       │  │
│                    └─────────────┘    └─────────────┘       │  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 模块划分

### 3.1 模块依赖图

```
┌─────────────────────────────────────────────────────────────┐
│                      前端模块                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   页面模块  │  │  组件模块   │  │  状态管理   │        │
│  │   (Pages)   │  │(Components)│  │   (Store)   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │                                  │
│                          ↓                                  │
│                   ┌─────────────┐                          │
│                   │   API层     │                          │
│                   │  (Axios)    │                          │
│                   └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      后端模块                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   API模块   │  │  服务模块   │  │  Agent模块  │        │
│  │  (Routes)   │──→ (Services) │──→ (Agents)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                          │                │                │
│                          ↓                ↓                │
│                   ┌─────────────┐  ┌─────────────┐        │
│                   │   数据模块  │  │   LLM模块   │        │
│                   │  (Models)   │  │  (LLM)     │        │
│                   └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 后端模块详细设计

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI应用入口
│   ├── config.py                  # 配置管理
│   │
│   ├── api/                       # API层
│   │   ├── __init__.py
│   │   ├── deps.py                # 依赖注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # 路由汇总
│   │       ├── stories.py         # 故事相关接口
│   │       ├── agents.py          # Agent相关接口
│   │       └── sessions.py        # 会话相关接口
│   │
│   ├── services/                  # 服务层
│   │   ├── __init__.py
│   │   ├── story_service.py       # 故事服务
│   │   ├── orchestrator.py        # 编排器
│   │   └── discussion_engine.py   # 讨论引擎
│   │
│   ├── agents/                    # Agent层
│   │   ├── __init__.py
│   │   ├── base.py                # Agent基类
│   │   ├── plot_agent.py          # 剧情Agent
│   │   ├── character_agent.py     # 人物Agent
│   │   ├── dialogue_agent.py      # 对话Agent
│   │   └── world_agent.py         # 世界观Agent
│   │
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── story.py               # 故事模型
│   │   ├── character.py           # 角色模型
│   │   └── session.py             # 会话模型
│   │
│   ├── schemas/                   # Pydantic Schema
│   │   ├── __init__.py
│   │   ├── story.py               # 故事Schema
│   │   ├── character.py           # 角色Schema
│   │   └── discussion.py          # 讨论Schema
│   │
│   ├── core/                      # 核心模块
│   │   ├── __init__.py
│   │   ├── llm.py                 # LLM客户端
│   │   ├── prompts.py             # Prompt模板
│   │   └── exceptions.py          # 自定义异常
│   │
│   └── db/                        # 数据库
│       ├── __init__.py
│       ├── database.py            # 数据库连接
│       └── repositories/          # 仓储层
│           ├── __init__.py
│           ├── story_repo.py
│           └── session_repo.py
│
├── tests/                         # 测试
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_agents.py
│   │   └── test_orchestrator.py
│   └── integration/
│       └── test_api.py
│
├── alembic/                       # 数据库迁移
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

### 3.3 前端模块详细设计

```
frontend/
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── layout.tsx             # 根布局
│   │   ├── page.tsx               # 首页
│   │   ├── create/                # 创建故事页
│   │   │   └── page.tsx
│   │   ├── story/[id]/            # 故事详情页
│   │   │   └── page.tsx
│   │   └── api/                   # API路由（可选）
│   │
│   ├── components/                # 组件
│   │   ├── ui/                    # 基础UI组件
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   └── ...
│   │   │
│   │   ├── story/                 # 故事相关组件
│   │   │   ├── StoryForm.tsx      # 故事输入表单
│   │   │   ├── StoryOutline.tsx   # 故事大纲展示
│   │   │   ├── CharacterCard.tsx  # 角色卡片
│   │   │   ├── DialogueView.tsx   # 对话展示
│   │   │   ├── WorldView.tsx      # 世界观展示
│   │   │   └── DiscussionView.tsx # 讨论过程展示
│   │   │
│   │   └── layout/                # 布局组件
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   │
│   ├── stores/                    # Zustand状态管理
│   │   ├── storyStore.ts          # 故事状态
│   │   └── uiStore.ts             # UI状态
│   │
│   ├── services/                  # API服务
│   │   ├── api.ts                 # Axios实例
│   │   ├── storyService.ts        # 故事API
│   │   └── agentService.ts        # Agent API
│   │
│   ├── types/                     # TypeScript类型
│   │   ├── story.ts
│   │   ├── character.ts
│   │   └── agent.ts
│   │
│   └── utils/                     # 工具函数
│       ├── format.ts
│       └── validation.ts
│
├── public/                        # 静态资源
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── next.config.js
└── Dockerfile
```

---

## 4. 接口设计

### 4.1 API设计原则

- 遵循RESTful设计规范
- 统一的响应格式
- 合理的错误处理
- 版本控制（/api/v1/）

### 4.2 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**错误响应：**
```json
{
  "code": 400,
  "message": "Invalid input",
  "errors": [
    {
      "field": "theme",
      "message": "Theme is required"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 4.3 API接口列表

#### 4.3.1 故事相关接口

**POST /api/v1/stories**

创建新故事（触发Agent协作生成）

```
请求：
{
  "theme": "未来世界的AI觉醒",
  "genre": "science_fiction",
  "constraints": {
    "target_audience": "青少年",
    "elements": ["哲学思考", "冒险"]
  }
}

响应：
{
  "code": 200,
  "message": "Story generation started",
  "data": {
    "session_id": "sess_abc123",
    "status": "processing",
    "estimated_time": 60
  }
}
```

**GET /api/v1/stories/{session_id}**

获取故事生成结果

```
响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "session_id": "sess_abc123",
    "status": "completed",
    "story": {
      "title": "觉醒之日",
      "outline": { ... },
      "characters": [ ... ],
      "dialogues": [ ... ],
      "world_setting": { ... }
    },
    "discussion": [ ... ]
  }
}
```

**GET /api/v1/stories/{session_id}/stream**

SSE流式获取生成过程

```
事件流：
event: status
data: {"phase": "proposal", "agent": "plot", "message": "正在生成故事结构..."}

event: discussion
data: {"round": 1, "agent": "character", "message": "我认为主角的性格应该..."}

event: result
data: {"story": { ... }}
```

#### 4.3.2 Agent相关接口

**GET /api/v1/agents**

获取所有Agent信息

```
响应：
{
  "code": 200,
  "data": {
    "agents": [
      {
        "id": "plot_agent",
        "name": "剧情Agent",
        "description": "负责设计故事结构和剧情",
        "status": "ready"
      },
      ...
    ]
  }
}
```

### 4.4 Agent间通信接口

```python
# Agent基类接口
class BaseAgent:
    async def propose(self, task: str, context: dict) -> AgentProposal:
        """提出方案"""
        pass
    
    async def review(self, proposals: dict, discussion: list) -> AgentFeedback:
        """Review其他Agent的方案"""
        pass
    
    async def revise(self, feedback: list, current_proposal: dict) -> AgentProposal:
        """根据反馈修改方案"""
        pass
    
    async def reach_consensus(self, proposals: dict, discussion: list) -> ConsensusResult:
        """达成共识"""
        pass
```

---

## 5. 数据模型

### 5.1 ER图

```
┌─────────────────────────────────────────────────────────────────┐
│                           数据模型                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐ │
│  │   Session    │       │    Story     │       │  Character   │ │
│  ├──────────────┤       ├──────────────┤       ├──────────────┤ │
│  │ id (PK)      │──1:N──│ id (PK)      │──1:N──│ id (PK)      │ │
│  │ user_id      │       │ session_id   │       │ story_id     │ │
│  │ status       │       │ title        │       │ name         │ │
│  │ theme        │       │ genre        │       │ role         │ │
│  │ genre        │       │ synopsis     │       │ personality  │ │
│  │ constraints  │       │ outline      │       │ background   │ │
│  │ created_at   │       │ world_setting│       │ motivation   │ │
│  │ updated_at   │       │ created_at   │       │ arc          │ │
│  └──────────────┘       └──────────────┘       │ relationships│ │
│         │                                       └──────────────┘ │
│         │                                                        │
│         │               ┌──────────────┐       ┌──────────────┐ │
│         │               │  Dialogue    │       │ Discussion   │ │
│         │               ├──────────────┤       ├──────────────┤ │
│         └───────1:N─────│ id (PK)      │       │ id (PK)      │ │
│                         │ story_id     │       │ session_id   │ │
│                         │ scene        │       │ round        │ │
│                         │ characters   │       │ agent_id     │ │
│                         │ content      │       │ content      │ │
│                         │ created_at   │       │ type         │ │
│                         └──────────────┘       │ created_at   │ │
│                                                └──────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 数据表设计

#### Session表

```sql
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending, processing, completed, failed
    theme TEXT NOT NULL,
    genre VARCHAR(50),
    constraints JSONB,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
```

#### Story表

```sql
CREATE TABLE stories (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id),
    title VARCHAR(200),
    genre VARCHAR(50),
    synopsis TEXT,
    outline JSONB,
    -- {"acts": [{"name": "...", "description": "...", "key_events": [...]}]}
    world_setting JSONB,
    -- {"era": "...", "location": "...", "rules": [...]}
    themes JSONB,
    -- ["theme1", "theme2"]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stories_session_id ON stories(session_id);
```

#### Character表

```sql
CREATE TABLE characters (
    id VARCHAR(36) PRIMARY KEY,
    story_id VARCHAR(36) NOT NULL REFERENCES stories(id),
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50),
    -- protagonist, antagonist, supporting
    age INTEGER,
    personality TEXT,
    background TEXT,
    motivation TEXT,
    arc TEXT,
    relationships JSONB,
    -- [{"character_id": "...", "relation": "..."}]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_characters_story_id ON characters(story_id);
```

#### Dialogue表

```sql
CREATE TABLE dialogues (
    id VARCHAR(36) PRIMARY KEY,
    story_id VARCHAR(36) NOT NULL REFERENCES stories(id),
    scene VARCHAR(200),
    participants JSONB,
    -- ["character_id_1", "character_id_2"]
    content JSONB,
    -- [{"character": "...", "line": "..."}, ...]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dialogues_story_id ON dialogues(story_id);
```

#### Discussion表

```sql
CREATE TABLE discussions (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id),
    round INTEGER NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    -- plot_agent, character_agent, dialogue_agent, world_agent
    content TEXT NOT NULL,
    type VARCHAR(20) NOT NULL,
    -- proposal, feedback, revision, consensus
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_discussions_session_id ON discussions(session_id);
CREATE INDEX idx_discussions_round ON discussions(round);
```

### 5.3 Pydantic Schema

```python
# schemas/story.py
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class Genre(str, Enum):
    SCIENCE_FICTION = "science_fiction"
    FANTASY = "fantasy"
    REALISM = "realism"
    MYSTERY = "mystery"
    ROMANCE = "romance"

class StoryCreateRequest(BaseModel):
    theme: str
    genre: Optional[Genre] = None
    constraints: Optional[dict] = None

class ActOutline(BaseModel):
    name: str
    description: str
    key_events: List[str]

class StoryOutline(BaseModel):
    acts: List[ActOutline]
    themes: List[str]

class CharacterBase(BaseModel):
    name: str
    role: str
    age: Optional[int] = None
    personality: str
    background: str
    motivation: str
    arc: Optional[str] = None

class StoryResponse(BaseModel):
    session_id: str
    status: str
    story: Optional[dict] = None
    discussion: Optional[list] = None
```

---

## 6. 错误处理设计

### 6.1 错误码定义

```python
# core/exceptions.py
class ErrorCode:
    # 通用错误
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
    
    # 业务错误 (1xxx)
    STORY_NOT_FOUND = 1001
    SESSION_NOT_FOUND = 1002
    GENERATION_FAILED = 1003
    
    # Agent错误 (2xxx)
    AGENT_TIMEOUT = 2001
    AGENT_RATE_LIMIT = 2002
    LLM_API_ERROR = 2003
    
    # 讨论错误 (3xxx)
    DISCUSSION_FAILED = 3001
    CONSENSUS_NOT_REACHED = 3002
```

### 6.2 异常处理流程

```
请求进入
    ↓
参数校验
    ↓ (失败)
返回400错误
    ↓ (成功)
业务逻辑执行
    ↓ (异常)
捕获异常
    ↓
├─ 业务异常 → 返回对应错误码
├─ LLM异常 → 重试或返回500
└─ 未知异常 → 记录日志，返回500
```

---

## 7. 安全设计

### 7.1 API安全

- API Key认证（可选）
- 请求频率限制
- 输入参数校验
- SQL注入防护（使用ORM）

### 7.2 数据安全

- 敏感数据加密存储
- 日志脱敏
- 定期数据备份

### 7.3 LLM安全

- Prompt注入防护
- 输出内容过滤
- Token使用限制

---

## 8. 监控和日志

### 8.1 日志设计

```python
# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 日志级别
# DEBUG: 开发调试
# INFO: 正常操作
# WARNING: 警告
# ERROR: 错误
# CRITICAL: 严重错误
```

### 8.2 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| API响应时间 | P95延迟 | > 3秒 |
| 错误率 | 5xx错误比例 | > 1% |
| LLM调用成功率 | 成功/总调用 | < 95% |
| 生成成功率 | 成功/总请求 | < 90% |

---

## 9. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2024 | 初始版本 | - |

---

**文档结束**

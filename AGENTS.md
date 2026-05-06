# AGENTS.md

## 环境配置

```bash
# 1. 复制环境变量文件
cp .env.example .env

# 2. 必须填入 OPENAI_API_KEY，否则 LLM 调用会失败
# 编辑 .env 文件

# 3. 安装依赖
uv sync --all-extras

# 4. 启动后端（从项目根目录）
uv run uvicorn app.main:app --reload --port 8000
```
- 后端入口：`backend/app/main.py`
- 数据库：开发环境用 SQLite（自动创建 `data/writing.db`），无需额外启动
- PostgreSQL 仅生产环境需要，通过 `docker compose up -d` 启动

## 开发命令

```bash
# 测试（项目根目录）
uv run pytest

# 单测试文件
uv run pytest backend/tests/unit/test_api.py

# 代码格式
uv run black .

# 代码检查
uv run ruff check .

# 类型检查
uv run mypy .
```

## 架构要点

- **4个Agent**：`plot_agent`、`character_agent`、`dialogue_agent`、`world_agent`，均继承 `backend/app/agents/base.py:BaseAgent`
- **编排器**：`backend/app/services/orchestrator.py:Orchestrator`，全局单例，管理会话状态
- **讨论引擎**：`backend/app/services/discussion_engine.py:DiscussionEngine`，控制多轮讨论流程，`DISCUSSION_ROUNDS` 环境变量控制轮数（默认3轮）
- **LLM调用**：Agent 直接调用 OpenAI API（`openai.AsyncOpenAI`），不经过 LangChain 封装层

## API路由

- `POST /api/v1/stories` - 创建故事会话
- `POST /api/v1/stories/{session_id}/generate` - 触发生成
- `GET /api/v1/stories/{session_id}` - 获取结果
- `GET /api/v1/stories/{session_id}/stream` - SSE 流式获取生成过程

## 配置优先级

配置从以下来源加载（优先级递减）：
1. 环境变量
2. `.env` 文件
3. `backend/app/config.py` 中的默认值

所有配置通过 `app.config.settings` 全局实例访问。

## Git 提交规范

遵循 Angular Commit Convention：
```
<type>(<scope>): <subject>
```
示例：`feat(agents): implement plot agent with story structure generation`

分支命名：`feature/<ticket>-<description>`，例如 `feature/AGT-001-plot-agent`

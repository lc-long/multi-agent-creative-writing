# 多Agent创意写作系统 - 开发规范文档

> 文档版本：v1.0  
> 创建日期：2024  
> 规范基础：Angular Commit Convention

---

## 1. Git提交规范

### 1.1 Commit Message格式

基于 [Angular Commit Convention](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit)，每次提交必须遵循以下格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**完整示例：**
```
feat(orchestrator): add multi-agent discussion engine

Implement the discussion engine that coordinates multiple agents
to collaboratively generate story content.

- Add DiscussionEngine class
- Implement round-based discussion mechanism
- Add consensus detection algorithm

Closes #123
```

### 1.2 Type类型定义

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(agent): add plot agent implementation` |
| `fix` | 修复bug | `fix(api): handle timeout error in story generation` |
| `docs` | 文档更新 | `docs(readme): update installation guide` |
| `style` | 代码格式（不影响功能） | `style(agents): fix indentation` |
| `refactor` | 重构（既不是新功能也不是修复） | `refactor(services): extract orchestrator logic` |
| `perf` | 性能优化 | `perf(llm): optimize token usage` |
| `test` | 测试相关 | `test(agents): add unit tests for plot agent` |
| `build` | 构建系统或外部依赖 | `build(docker): update Dockerfile` |
| `ci` | CI配置 | `ci(github): add workflow for testing` |
| `chore` | 其他杂项 | `chore(deps): update langchain to v0.1` |
| `revert` | 回滚 | `revert: revert changes to orchestrator` |

### 1.3 Scope范围定义

| Scope | 说明 | 示例 |
|-------|------|------|
| `agents` | Agent模块 | `feat(agents): add character agent` |
| `api` | API接口 | `feat(api): add story creation endpoint` |
| `services` | 服务层 | `fix(services): fix orchestrator race condition` |
| `models` | 数据模型 | `feat(models): add session model` |
| `schemas` | Pydantic Schema | `feat(schemas): add story response schema` |
| `db` | 数据库相关 | `fix(db): fix migration script` |
| `ui` | 前端UI | `feat(ui): add story form component` |
| `store` | 状态管理 | `feat(store): add story store` |
| `config` | 配置 | `chore(config): update env variables` |
| `deps` | 依赖 | `chore(deps): update dependencies` |
| `test` | 测试 | `test(api): add integration tests` |
| `docs` | 文档 | `docs(api): add API documentation` |
| `docker` | Docker相关 | `build(docker): optimize build process` |
| `ci` | CI/CD | `ci(github): add deploy workflow` |

### 1.4 Subject规范

- 使用英文
- 首字母小写
- 不超过50个字符
- 使用祈使语气（动词开头）
- 不加句号

**正确示例：**
```
feat(agents): add plot agent implementation
fix(api): handle timeout error
docs(readme): update installation guide
```

**错误示例：**
```
feat(agents): Added plot agent implementation  ❌ (过去式)
feat(agents): add plot agent implementation.  ❌ (加了句号)
feat(agents): Add plot agent implementation   ❌ (首字母大写)
```

### 1.5 Body规范

- 使用英文
- 解释**为什么**做这个改动，而不是**做了什么**
- 每行不超过72个字符
- 可以使用列表格式

```
feat(orchestrator): add multi-agent discussion engine

Implement the discussion engine that coordinates multiple agents
to collaboratively generate story content.

The engine uses a round-based mechanism where each agent can
review and provide feedback on other agents' proposals. This
ensures diverse perspectives are considered in the final output.

- Add DiscussionEngine class with round management
- Implement consensus detection algorithm
- Add support for agent-specific feedback collection
```

### 1.6 Footer规范

**关联Issue：**
```
Closes #123
Fixes #456
Resolves #789
```

**Breaking Change：**
```
BREAKING CHANGE: The orchestrator API has been updated to use
async/await pattern. Existing code using synchronous calls
will need to be updated.
```

### 1.7 提交示例库

```
# 功能相关
feat(agents): implement plot agent with story structure generation
feat(agents): add character agent for role design
feat(agents): add dialogue agent for conversation generation
feat(agents): add world-building agent for setting creation
feat(api): add POST /api/v1/stories endpoint
feat(api): add GET /api/v1/stories/{id} endpoint
feat(api): add SSE streaming endpoint for generation process
feat(ui): create story input form component
feat(ui): add character card display component
feat(ui): implement discussion process viewer

# 修复相关
fix(agents): fix agent timeout handling in orchestrator
fix(api): fix race condition in concurrent story generation
fix(db): fix migration script for character relationships
fix(ui): fix responsive layout on mobile devices

# 重构相关
refactor(agents): extract base agent class for reuse
refactor(services): split orchestrator into smaller modules
refactor(api): standardize error response format

# 测试相关
test(agents): add unit tests for plot agent
test(api): add integration tests for story endpoints
test(services): add tests for discussion engine

# 文档相关
docs(readme): add project overview and setup guide
docs(api): add OpenAPI documentation for all endpoints
docs(architecture): add system architecture diagram

# 杂项
chore(deps): update langchain to v0.1.0
chore(deps): add pytest-asyncio for async testing
build(docker): add multi-stage build for optimization
ci(github): add test and lint workflow
```

---

## 2. 分支管理规范

### 2.1 分支类型

| 分支类型 | 命名格式 | 说明 | 生命周期 |
|---------|---------|------|---------|
| `main` | `main` | 主分支，生产环境代码 | 永久 |
| `develop` | `develop` | 开发分支，最新功能 | 永久 |
| `feature` | `feature/<ticket-id>-<description>` | 功能开发分支 | 临时 |
| `bugfix` | `bugfix/<ticket-id>-<description>` | Bug修复分支 | 临时 |
| `hotfix` | `hotfix/<ticket-id>-<description>` | 紧急修复分支 | 临时 |
| `release` | `release/<version>` | 发布准备分支 | 临时 |

### 2.2 分支命名示例

```
# 功能分支
feature/AGT-001-plot-agent
feature/AGT-002-character-agent
feature/AGT-003-discussion-engine
feature/API-001-story-endpoints

# Bug修复分支
bugfix/AGT-004-fix-timeout-handling
bugfix/API-002-fix-validation-error

# 热修复分支
hotfix/AGT-005-fix-critical-crash

# 发布分支
release/1.0.0
release/1.1.0
```

### 2.3 分支工作流

```
main ──────────────────────────────────────────────────────────→
  │                                                          ↑
  │    ┌─ feature/AGT-001 ──────────────────────────────┐    │
  │    │         │                                      │    │
  │    │    commit  commit  commit                      │    │
  │    │         │                                      │    │
  │    │         └──────────────────────────────────→ PR/MR ──┘
  │    │
  │    └─ feature/AGT-002 ──────────────────────────────┐
  │              │                                      │
  │         commit  commit                              │
  │              │                                      │
  │              └──────────────────────────────────→ PR/MR ──→
  │
develop ──────────────────────────────────────────────────────→
```

### 2.4 分支操作规范

**创建功能分支：**
```bash
# 从develop分支创建
git checkout develop
git pull origin develop
git checkout -b feature/AGT-001-plot-agent
```

**提交代码：**
```bash
# 添加文件
git add <files>

# 提交（遵循Angular规范）
git commit -m "feat(agents): implement plot agent with story structure generation

- Add PlotAgent class
- Implement story structure generation
- Add unit tests for plot agent

Closes #1"
```

**同步远程分支：**
```bash
# 定期同步develop分支的更新
git fetch origin
git rebase origin/develop
```

**推送分支：**
```bash
git push origin feature/AGT-001-plot-agent
```

**合并分支（通过PR/MR）：**
```bash
# 在GitHub/GitLab上创建PR/MR
# 代码评审通过后，使用Squash and Merge
# 删除远程分支
git push origin --delete feature/AGT-001-plot-agent

# 删除本地分支
git checkout develop
git branch -d feature/AGT-001-plot-agent
```

### 2.5 版本号规范

遵循 [Semantic Versioning](https://semver.org/) (语义化版本)：

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的API变更
MINOR: 向后兼容的功能性新增
PATCH: 向后兼容的问题修复
```

**示例：**
```
1.0.0 → 1.0.1 (bug fix)
1.0.1 → 1.1.0 (new feature)
1.1.0 → 2.0.0 (breaking change)
```

---

## 3. 代码规范

### 3.1 Python代码规范

**工具链：**
```
代码格式化: black
代码检查: ruff / flake8
类型检查: mypy
导入排序: isort
```

**配置文件（pyproject.toml）：**
```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.ruff.isort]
known-first-party = ["app"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**代码风格示例：**
```python
# 正确示例
from typing import Optional, List
from pydantic import BaseModel


class Character(BaseModel):
    """Character model for story generation."""
    
    name: str
    role: str
    personality: str
    background: Optional[str] = None
    
    def introduce(self) -> str:
        """Generate character introduction."""
        return f"I am {self.name}, {self.role}"


def create_character(
    name: str,
    role: str,
    personality: str,
    background: Optional[str] = None,
) -> Character:
    """Create a new character instance."""
    return Character(
        name=name,
        role=role,
        personality=personality,
        background=background,
    )
```

### 3.2 TypeScript/React代码规范

**工具链：**
```
代码格式化: Prettier
代码检查: ESLint
类型检查: TypeScript
```

**配置文件（.prettierrc）：**
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

**配置文件（.eslintrc.json）：**
```json
{
  "extends": [
    "next/core-web-vitals",
    "prettier"
  ],
  "rules": {
    "no-unused-vars": "error",
    "no-console": "warn"
  }
}
```

**代码风格示例：**
```typescript
// 正确示例
interface Character {
  id: string;
  name: string;
  role: 'protagonist' | 'antagonist' | 'supporting';
  personality: string;
  background?: string;
}

interface CharacterCardProps {
  character: Character;
  onSelect?: (id: string) => void;
}

export function CharacterCard({ character, onSelect }: CharacterCardProps) {
  const handleClick = () => {
    onSelect?.(character.id);
  };

  return (
    <div className="rounded-lg border p-4" onClick={handleClick}>
      <h3 className="text-lg font-semibold">{character.name}</h3>
      <p className="text-sm text-gray-500">{character.role}</p>
      <p className="mt-2">{character.personality}</p>
    </div>
  );
}
```

### 3.3 命名规范

**Python命名：**
```python
# 模块名：小写 + 下划线
plot_agent.py
character_agent.py

# 类名：大驼峰
class PlotAgent:
class CharacterCard:

# 函数名：小写 + 下划线
def create_character():
def generate_story():

# 常量：大写 + 下划线
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 60

# 私有属性/方法：下划线开头
class Agent:
    def __init__(self):
        self._internal_state = {}
    
    def _validate_input(self):
        pass
```

**TypeScript/React命名：**
```typescript
// 组件名：大驼峰
function CharacterCard() {}
function StoryOutline() {}

// 文件名：大驼峰（组件）或 小驼峰（工具）
CharacterCard.tsx
useStoryStore.ts

// 接口名：大驼峰 + Props/Suffix
interface CharacterCardProps {}
interface StoryResponse {}

// 常量：大写 + 下划线
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = '/api/v1';

// 函数：小驼峰
function handleClick() {}
function formatCharacterName() {}
```

---

## 4. Pull Request / Merge Request 规范

### 4.1 PR模板

```markdown
## 描述

简要描述这个PR的目的和内容。

## 变更类型

- [ ] 新功能 (feat)
- [ ] Bug修复 (fix)
- [ ] 重构 (refactor)
- [ ] 文档更新 (docs)
- [ ] 测试 (test)
- [ ] 其他 (chore)

## 变更内容

- 变更1
- 变更2
- 变更3

## 关联Issue

Closes #123

## 测试

描述你如何测试这些变更：

- [ ] 单元测试
- [ ] 集成测试
- [ ] 手动测试

## 截图（如适用）

如果有UI变更，请提供截图。

## Checklist

- [ ] 代码遵循项目规范
- [ ] 已添加必要的测试
- [ ] 已更新相关文档
- [ ] 所有测试通过
- [ ] 代码已自我评审
```

### 4.2 代码评审要求

**必须满足的条件：**
- 至少1个Reviewer批准
- 所有CI检查通过
- 没有合并冲突
- 代码覆盖率不下降

**评审重点：**
```
✓ 代码逻辑是否正确
✓ 是否有潜在的bug
✓ 是否有安全隐患
✓ 是否有性能问题
✓ 代码是否可读
✓ 是否有必要的测试
✓ 是否有文档更新
```

### 4.3 合并策略

| 分支 | 合并策略 | 说明 |
|------|---------|------|
| feature → develop | Squash and Merge | 压缩为一个提交 |
| bugfix → develop | Squash and Merge | 压缩为一个提交 |
| develop → main | Merge Commit | 保留所有提交历史 |
| hotfix → main | Merge Commit | 保留紧急修复历史 |

---

## 5. Issue/Ticket规范

### 5.1 Issue模板

**功能需求模板：**
```markdown
## 功能描述

简要描述这个功能。

## 用户故事

作为 [用户角色]
我想要 [功能描述]
以便 [价值/目的]

## 验收标准

- [ ] 标准1
- [ ] 标准2
- [ ] 标准3

## 技术方案（可选）

描述实现方案。

## 优先级

- [ ] P0 - 必须
- [ ] P1 - 重要
- [ ] P2 - 一般
```

**Bug报告模板：**
```markdown
## Bug描述

简要描述这个Bug。

## 复现步骤

1. 步骤1
2. 步骤2
3. 步骤3

## 期望行为

描述你期望的行为。

## 实际行为

描述实际的行为。

## 环境信息

- OS: 
- Python版本: 
- Node版本: 

## 日志/截图

提供相关日志或截图。
```

### 5.2 Issue编号规范

```
项目前缀: AGT (Agent), API, UI, DB, DOC

示例:
AGT-001: 实现剧情Agent
AGT-002: 实现人物Agent
API-001: 实现故事创建接口
UI-001: 创建故事输入表单
```

---

## 6. 代码评审Checklist

### 6.1 通用检查项

```
□ 代码逻辑是否正确？
□ 是否有潜在的bug？
□ 是否有安全隐患？
□ 是否有性能问题？
□ 代码是否可读？
□ 命名是否清晰？
□ 是否有重复代码？
□ 是否有必要的注释？
□ 错误处理是否完善？
□ 日志记录是否充分？
```

### 6.2 Python检查项

```
□ 是否遵循PEP8规范？
□ 是否有类型注解？
□ 是否有docstring？
□ 是否正确使用异步？
□ 是否正确处理异常？
□ 是否正确关闭资源？
```

### 6.3 TypeScript/React检查项

```
□ 是否有TypeScript类型？
□ 是否正确使用hooks？
□ 组件是否有PropTypes/接口？
□ 是否有key属性？
□ 是否避免内联函数？
□ 是否正确处理副作用？
```

### 6.4 测试检查项

```
□ 是否有单元测试？
□ 测试覆盖是否足够？
□ 测试用例是否清晰？
□ 边界条件是否测试？
□ 异常情况是否测试？
```

---

## 7. 环境管理规范

### 7.1 Python环境管理（uv）

本项目使用 [uv](https://github.com/astral-sh/uv) 管理Python环境，替代传统的pip/venv。

**安装uv：**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**项目初始化：**
```bash
# 创建项目（如果还没有pyproject.toml）
uv init

# 创建虚拟环境
uv venv --python 3.11

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 安装依赖
uv pip install -r requirements.txt

# 添加新依赖
uv pip install langchain openai

# 同步依赖（从pyproject.toml）
uv sync
```

**pyproject.toml示例：**
```toml
[project]
name = "multi-agent-writing"
version = "0.1.0"
description = "Multi-Agent Creative Writing System"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "langchain>=0.1.0",
    "openai>=1.0.0",
    "pydantic>=2.0.0",
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.19.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
```

**常用命令：**
```bash
# 安装所有依赖（包括开发依赖）
uv sync --all-extras

# 只安装开发依赖
uv sync --extra dev

# 更新依赖
uv lock --upgrade

# 运行命令
uv run python main.py
uv run pytest

# 查看依赖树
uv tree
```

### 7.2 Docker使用规范

本项目使用Docker运行数据库等基础设施服务。

**docker-compose.yml示例：**
```yaml
version: '3.8'

services:
  # PostgreSQL数据库（生产环境）
  postgres:
    image: postgres:15-alpine
    container_name: writing-postgres
    environment:
      POSTGRES_USER: writing_user
      POSTGRES_PASSWORD: writing_pass
      POSTGRES_DB: writing_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U writing_user -d writing_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis缓存（可选）
  redis:
    image: redis:7-alpine
    container_name: writing-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**常用命令：**
```bash
# 启动所有服务
docker compose up -d

# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f postgres

# 停止所有服务
docker compose down

# 停止并删除数据
docker compose down -v

# 进入容器
docker exec -it writing-postgres psql -U writing_user -d writing_db
```

### 7.3 环境变量管理

**.env文件示例：**
```bash
# 应用配置
APP_ENV=development
APP_DEBUG=true
APP_PORT=8000

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./data/writing.db
# 生产环境使用PostgreSQL
# DATABASE_URL=postgresql+asyncpg://writing_user:writing_pass@localhost:5432/writing_db

# LLM配置
OPENAI_API_KEY=sk-your-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 其他配置
MAX_TOKENS=4000
TEMPERATURE=0.7
```

**.env.example文件：**
```bash
# 复制此文件为.env并填入实际值
APP_ENV=development
APP_DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./data/writing.db
OPENAI_API_KEY=sk-your-api-key
```

---

## 8. Commit频率规范

### 8.1 Commit原则

**核心原则：勤commit，按功能**

- 每完成一个**独立功能点**就commit
- 每修复一个**bug**就commit
- 每次commit应该是**可运行**的状态
- 避免"大爆炸"式提交（一次性提交大量代码）

### 8.2 Commit时机

**应该commit的时机：**
```
✓ 完成一个函数/方法的实现
✓ 完成一个类的定义
✓ 完成一个API接口
✓ 完成一个组件
✓ 修复一个bug
✓ 添加一个测试
✓ 更新文档
✓ 重构完成一个模块
```

**不应该commit的时机：**
```
✗ 代码还在调试中
✗ 测试还没通过
✗ 有编译错误
✗ 有未完成的TODO
```

### 8.3 Commit粒度示例

**正确的commit粒度：**
```bash
# 第1个commit：初始化项目结构
git commit -m "chore(init): initialize project structure with uv and FastAPI"

# 第2个commit：添加配置管理
git commit -m "feat(config): add configuration management with pydantic-settings"

# 第3个commit：添加数据库模型
git commit -m "feat(models): add SQLAlchemy models for story and characters"

# 第4个commit：添加Agent基类
git commit -m "feat(agents): add base agent class with LLM integration"

# 第5个commit：添加剧情Agent
git commit -m "feat(agents): implement plot agent with story structure generation"

# 第6个commit：添加API接口
git commit -m "feat(api): add POST /api/v1/stories endpoint"
```

**错误的commit粒度（太大）：**
```bash
# ❌ 一次性提交太多内容
git commit -m "feat: add all agents and API endpoints"
```

### 8.4 功能分支的Commit策略

```
feature/AGT-001-plot-agent分支：
├── commit 1: feat(agents): add plot agent class skeleton
├── commit 2: feat(agents): implement story structure generation
├── commit 3: test(agents): add unit tests for plot agent
├── commit 4: docs(agents): add plot agent documentation
└── commit 5: fix(agents): fix edge case in structure generation
```

---

## 9. 开发工作流

### 9.1 日常开发流程

```bash
# 1. 开始工作前
git checkout develop
git pull origin develop

# 2. 创建功能分支
git checkout -b feature/AGT-001-plot-agent

# 3. 开发过程中（勤commit）
# ... 编写代码 ...
git add <files>
git commit -m "feat(agents): add plot agent class skeleton"

# ... 继续开发 ...
git add <files>
git commit -m "feat(agents): implement story structure generation"

# 4. 定期同步develop分支
git fetch origin
git rebase origin/develop

# 5. 推送到远程
git push origin feature/AGT-001-plot-agent

# 6. 创建Pull Request
# 在GitHub/GitLab上创建PR

# 7. 代码评审通过后，合并PR
# 使用Squash and Merge

# 8. 清理
git checkout develop
git pull origin develop
git branch -d feature/AGT-001-plot-agent
```

### 9.2 提交前检查清单

```bash
# 运行测试
uv run pytest

# 运行代码检查
uv run ruff check .
uv run black --check .

# 运行类型检查
uv run mypy .

# 确保所有测试通过
uv run pytest -v
```

---

## 10. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2024 | 初始版本 | - |
| v1.1 | 2024 | 添加uv环境管理规范 | - |
| v1.2 | 2024 | 添加Docker使用规范 | - |
| v1.3 | 2024 | 添加Commit频率规范 | - |

---

**文档结束**

# Multi-Agent Creative Writing System

> 多Agent创意写作系统 - 多个AI Agent协作生成创意故事

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 项目简介

这是一个基于多Agent协作的创意写作系统，通过不同专业背景的AI Agent协作，生成比单一AI更有创意、更完整的故事内容。

### 核心特性

- 🤖 **多Agent协作**：剧情、人物、对话、世界观四个Agent协作
- 💬 **讨论机制**：Agent之间通过"讨论"碰撞产生更好的创意
- 📝 **完整输出**：故事大纲、角色设定、对话示例、世界观设定
- 🔄 **迭代优化**：支持用户反馈和迭代修改
- 📊 **过程透明**：可查看Agent的讨论过程

### Agent角色

| Agent | 职责 |
|-------|------|
| 剧情Agent | 设计故事结构、起承转合、冲突和高潮 |
| 人物Agent | 设计角色性格、背景、动机和成长弧线 |
| 对话Agent | 生成符合角色性格的对话示例 |
| 世界观Agent | 设定故事发生的世界和规则 |

## 快速开始

### 前置要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip
- Docker (可选，用于运行数据库)

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/multi-agent-writing.git
cd multi-agent-writing
```

### 2. 安装依赖

```bash
# 使用uv（推荐）
uv venv --python 3.11
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
uv pip install -r requirements.txt

# 或使用pip
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API Key
```

### 4. 启动服务

```bash
# 启动后端服务
cd backend
uvicorn app.main:app --reload --port 8000

# 或者使用uv运行
uv run uvicorn app.main:app --reload --port 8000
```

### 5. 访问API文档

打开浏览器访问：http://localhost:8000/docs

## 项目结构

```
multi-agent-writing/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API接口层
│   │   │   └── v1/           # API v1版本
│   │   ├── services/         # 业务逻辑层
│   │   ├── agents/           # Agent实现
│   │   ├── models/           # 数据模型
│   │   ├── schemas/          # Pydantic Schema
│   │   ├── core/             # 核心模块
│   │   └── db/               # 数据库
│   ├── tests/                # 测试
│   └── pyproject.toml        # 项目配置
├── frontend/                   # 前端应用（可选）
├── docs/                       # 项目文档
├── data/                       # 数据存储
├── docker-compose.yml          # Docker配置
├── .env.example               # 环境变量示例
└── README.md                  # 项目说明
```

## 开发指南

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest backend/tests/unit/test_agents.py

# 运行测试并生成覆盖率报告
uv run pytest --cov=app --cov-report=html
```

### 代码检查

```bash
# 运行代码格式化
uv run black .

# 运行代码检查
uv run ruff check .

# 运行类型检查
uv run mypy .
```

### Docker（数据库）

```bash
# 启动数据库服务
docker compose up -d

# 查看运行状态
docker compose ps

# 停止服务
docker compose down
```

## API接口

### 创建故事

```http
POST /api/v1/stories
Content-Type: application/json

{
  "theme": "未来世界的AI觉醒",
  "genre": "science_fiction",
  "constraints": {
    "target_audience": "青少年",
    "elements": ["哲学思考", "冒险"]
  }
}
```

### 获取故事结果

```http
GET /api/v1/stories/{session_id}
```

### 流式获取生成过程（SSE）

```http
GET /api/v1/stories/{session_id}/stream
```

## 文档

- [需求分析文档](docs/01-requirements-analysis.md)
- [系统设计文档](docs/02-system-design.md)
- [开发规范文档](docs/03-development-standards.md)

## 技术栈

- **后端**: FastAPI, Python 3.11+
- **LLM框架**: LangChain, OpenAI
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **环境管理**: uv
- **容器化**: Docker

## 许可证

MIT License

## 联系方式

- 项目主页: [GitHub](https://github.com/yourusername/multi-agent-writing)
- 问题反馈: [Issues](https://github.com/yourusername/multi-agent-writing/issues)

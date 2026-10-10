# Lacan-Agent

<div align="center">

**基于拉康话语理论的主体结构分析工具**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-176%20passed-green.svg)](./tests/)

[English](#english) | [中文](#中文)

</div>

---

Lacan-Agent 是一个本地研究工具，用于把聊天、访谈、写作样本和研究观察整理成可追溯的主体结构画像，为后续受控 PersonaAgent 和五人故事接龙提供输入。

项目关注的是证据化的经验分析，不是临床诊断，也不会把语言口癖直接等同于人格。每个结构候选都必须引用材料中的证据 span，默认状态为 `candidate`，只有人工审核通过后才能进入生成策略。

## 目录

- [功能特性](#功能特性)
- [安装](#安装)
- [快速开始](#快速开始)
- [API 服务](#api-服务)
- [隐私与授权](#隐私与授权)
- [测试](#测试)
- [技术栈](#技术栈)
- [当前边界](#当前边界)
- [License](#license)

## 功能特性

### 1.0 提供的功能

- **多源材料导入**：聊天、访谈、写作和观察材料的统一导入
- **多格式解析**：UTF-8、GB18030、普通逐行文本和微信聊天格式
- **证据追溯**：稳定的 `MaterialSource`、`EvidenceSpan` 和来源 checksum
- **观察层统计**：消息长度、语气词、括号、拟声词、emoji、媒体和互动对象等
- **结构候选抽取**：基于 Qwen 的证据约束结构候选
- **拉康结构维度**：话语位置、大他者、需求与欲望、重复能指、缝合点、幻想、症状重复、享乐、四种话语、RSI 和叙事冲突
- **跨来源互证**：跨聊天、访谈和写作材料的来源互证候选
- **人工审核**：CLI 和 JSON 审核文件驱动的人工审核流程
- **同意管理**：参与者同意、过期、撤回和派生数据清理
- **拓扑导出**：旧版分析流水线的证据校验、文化注释、模糊接地和拓扑导出

> **注意**：五人故事接龙调度器、共享故事记忆和五个 PersonaAgent 的运行时不属于 1.0，本版本提供的是它们所需的主体结构输入层。

## 安装

### 使用 uv（推荐）

```bash
uv venv
uv pip install -e ".[dev]"
```

### 使用 pip

```bash
pip install -e ".[dev]"
```

### 环境配置

Qwen 结构抽取需要设置 DashScope API Key：

```powershell
# PowerShell
$env:DASHSCOPE_API_KEY = "sk-your-key"

# Bash/Zsh
export DASHSCOPE_API_KEY="sk-your-key"
```

可选环境变量：
- `LACAN_MODEL`：模型名称（默认 `qwen-plus`）
- `LACAN_LLM_TIMEOUT`：API 超时秒数（默认 `60`）
- `LACAN_LLM_RETRIES`：重试次数（默认 `2`）
- `LACAN_TEMPERATURE`：生成温度（默认 `0.3`）
- `LACAN_MAX_UPLOAD_BYTES`：API 上传文件大小限制（默认 `10MB`）

## 快速开始

### 传统证据分析

```bash
# 初始化项目
lacan-agent init --project demo

# 添加参与者
lacan-agent add-participant --project demo --id A --consent consent.json

# 导入材料
lacan-agent add-source --project demo --participant A --file story.txt

# 运行分析（使用 mock provider）
lacan-agent analyze --project demo --participant A --source story.txt --mock

# 审核
lacan-agent review --run <run_id> --decision approve

# 导出
lacan-agent export --run <run_id> --pretty
```

### 多源主体结构画像

先创建来源清单 `sources.json`。路径相对于文件所在目录解析，也可以通过 `--root` 指定材料根目录：

```json
{
  "sources": [
    {
      "source_id": "chat_a",
      "participant_id": "A",
      "source_type": "chat",
      "path": "chat.txt",
      "context": "group_chat"
    },
    {
      "source_id": "interview_a",
      "participant_id": "A",
      "source_type": "interview",
      "path": "interview.json",
      "context": "research_interview"
    },
    {
      "source_id": "writing_a",
      "participant_id": "A",
      "source_type": "writing",
      "path": "continuation.txt",
      "context": "prompt_1"
    }
  ]
}
```

访谈 JSON 格式：

```json
{
  "interview_id": "interview_a",
  "participant_id": "A",
  "context": "research_interview",
  "turns": [
    {
      "question_id": "A2",
      "answer_text": "我通常先解释，再决定是否继续。",
      "tags": ["misrecognition", "other"]
    }
  ]
}
```

构建和查看画像：

```bash
# 构建主体结构画像
lacan-agent subject build \
  --participant A \
  --sources sources.json \
  --mode full \
  --batch-size 80 \
  --with-relations \
  --cards-dir data/subject-artifacts

# 查看画像摘要
lacan-agent subject show --participant A --cards-dir data/subject-artifacts

# 检查语言特征
lacan-agent subject inspect-motifs --participant A --cards-dir data/subject-artifacts

# 检查关系图谱
lacan-agent subject inspect-relations --participant A --cards-dir data/subject-artifacts
```

主体分析按重叠窗口覆盖全部消息。原文和规范化文本同时保留在本地处理中，戏仿、谐音、重复标点和模板变体只作为候选；单次表达不会自动进入稳定语言特征。关系层先生成有向互动事件，再由 Qwen 复核关系候选，所有候选都保留 span、时间和场景证据。

可用 `--aliases aliases.json` 提供人工确认的参与者别名表，未确认别名不会自动合并。

#### 审核结构候选

Qwen 失败时仍会生成观察层画像。结构候选必须人工审核：

创建 `review.json`：

```json
{
  "participant_id": "A",
  "decisions": [
    {
      "claim_id": "claim_1",
      "status": "approved",
      "reviewer_id": "researcher",
      "reason": "聊天和访谈材料均提供支持"
    }
  ]
}
```

应用审核并导出：

```bash
lacan-agent subject review --participant A --input review.json --cards-dir data/subject-artifacts
lacan-agent subject export --participant A --cards-dir data/subject-artifacts --output subject.json
```

### 快捷统计画像

```bash
# 构建所有参与者的统计画像
lacan-agent profile build --all --texts-dir data/participant_texts --cards-dir data/profile-cards

# 查看特定参与者
lacan-agent profile show --participant 灯 --cards-dir data/profile-cards
```

### 交互式界面

```powershell
.\start.ps1
```

交互菜单支持传统证据分析，以及主体结构画像的构建、摘要查看和结构候选审核。

## API 服务

### 启动服务

**本地开发**（仅本机访问）：

```bash
uvicorn lacan_agent.api:app --host 127.0.0.1 --port 8000
```

**允许外部访问**（局域网或公网部署）：

```bash
uvicorn lacan_agent.api:app --host 0.0.0.0 --port 8000
```

**Docker 部署**：

```bash
docker build -t lacan-agent .
docker run -p 8000:8000 -v $(pwd)/data:/data lacan-agent
```

API 支持 `.txt`、`.md` 和 `.pdf` 文件上传，单文件大小受 `LACAN_MAX_UPLOAD_BYTES` 限制。

### CORS 配置

API 默认启用 CORS（跨域资源共享），仅允许本地开发来源：

- `http://localhost:3000`
- `http://localhost:8000`

通过环境变量 `LACAN_CORS_ORIGINS` 配置允许的域名（逗号分隔）：

```bash
# 生产环境示例
export LACAN_CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
uvicorn lacan_agent.api:app --host 0.0.0.0 --port 8000
```

**安全警告**：不要在生产环境使用 `*` 通配符，这会允许任何网站访问 API。

### API 调用示例

**创建项目**：

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"id": "demo", "owner_id": "researcher"}'
```

**添加参与者**：

```bash
curl -X POST http://localhost:8000/api/v1/participants \
  -H "Content-Type: application/json" \
  -d '{
    "id": "A",
    "project_id": "demo",
    "pseudonym": "Participant A",
    "consent_scope": {
      "research_analysis": true,
      "generation": false
    }
  }'
```

**上传材料**：

```bash
curl -X POST "http://localhost:8000/api/v1/participants/A/sources" \
  -F "project_id=demo" \
  -F "file=@story.txt"
```

**运行分析**：

```bash
curl -X POST http://localhost:8000/api/v1/analysis-runs \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "demo",
    "participant_id": "A",
    "source_ids": ["source_1"],
    "mode": "evidence_first",
    "idempotency_key": "run_001"
  }'
```

**查询状态**：

```bash
curl http://localhost:8000/api/v1/analysis-runs/run_001
```

**提交审核**：

```bash
curl -X POST http://localhost:8000/api/v1/analysis-runs/run_001/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_id": "researcher",
    "decision": "approve",
    "reason": "Evidence supports all claims"
  }'
```

**导出结果**：

```bash
curl http://localhost:8000/api/v1/analysis-runs/run_001/packet > result.json
curl http://localhost:8000/api/v1/analysis-runs/run_001/graph > graph.json
```

### 主要端点

- `POST /api/v1/projects` - 创建项目
- `POST /api/v1/participants` - 添加参与者
- `POST /api/v1/participants/{pid}/sources` - 上传材料
- `POST /api/v1/analysis-runs` - 运行分析
- `GET /api/v1/analysis-runs/{rid}` - 查询运行状态
- `POST /api/v1/analysis-runs/{rid}/reviews` - 提交审核
- `GET /api/v1/analysis-runs/{rid}/packet` - 导出审核包
- `GET /api/v1/analysis-runs/{rid}/graph` - 导出图谱
- `POST /api/v1/participants/{pid}/withdraw` - 撤回参与者

## 隐私与授权

- **默认关闭**：所有画像和生成授权默认关闭，必须显式同意
- **细粒度控制**：`profile_analysis`、`agent_simulation`、`story_generation` 和 `public_export` 分开控制
- **原文保护**：原始文本不写入 ProfileArtifact 的观察层和生成提示
- **撤回清理**：撤回会清理原始材料、EvidenceSpan、结构候选、画像、审核文件和派生导出
- **审计日志**：审计记录只保留匿名 ID、时间、操作和清理结果
- **本地存储**：本地 `data/` 下的画像、报告、数据库和上传材料默认不提交到 GitHub

## 测试

```bash
# 运行所有测试
pytest tests/ -q

# 运行特定测试文件
pytest tests/test_workflow.py -v

# 带覆盖率
pytest tests/ --cov=lacan_agent
```

测试覆盖材料导入、访谈 span、证据引用、结构候选审核、撤回边界、SQLite 存储、Qwen Provider、拓扑计算和 CLI 工作流。

## 技术栈

- **Python 3.12+**
- **Pydantic v2** - 数据验证
- **SQLite + FTS5** - 本地存储和全文搜索
- **FastAPI** - API 服务
- **DashScope** - 通义千问 API（OpenAI 兼容）
- **pytest** - 测试框架

## 当前边界

1.0 只提供多源主体结构分析和审核后的画像输入层。五个独立 PersonaAgent、轮流调度、共享故事状态、故事接龙评测和长期记忆将在后续版本实现。

## License

MIT

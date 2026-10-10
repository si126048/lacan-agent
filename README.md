# Lacan-Agent

**基于拉康话语理论的主体结构分析工具**

---

<div align="left">

| | |
|---|---|
| **版本** | 1.0 |
| **Python** | 3.12+ |
| **测试** | 176 passed |
| **许可** | MIT |

</div>

---

## 概述

Lacan-Agent 是一个本地研究工具，用于把聊天、访谈、写作样本和研究观察整理成可追溯的主体结构画像。

项目关注的是证据化的经验分析，不是临床诊断，也不会把语言口癖直接等同于人格。每个结构候选都必须引用材料中的证据 span，默认状态为 `candidate`，只有人工审核通过后才能进入生成策略。

---

## 目录

```
01  功能特性
02  安装
03  快速开始
04  API 服务
05  隐私与授权
06  测试
07  技术栈
08  当前边界
09  License
```

---

## 01 功能特性

### 1.0 提供的功能

| 功能 | 描述 |
|------|------|
| **多源材料导入** | 聊天、访谈、写作和观察材料的统一导入 |
| **多格式解析** | UTF-8、GB18030、普通逐行文本和微信聊天格式 |
| **证据追溯** | 稳定的 `MaterialSource`、`EvidenceSpan` 和来源 checksum |
| **观察层统计** | 消息长度、语气词、括号、拟声词、emoji、媒体和互动对象等 |
| **结构候选抽取** | 基于 Qwen 的证据约束结构候选 |
| **拉康结构维度** | 话语位置、大他者、需求与欲望、重复能指、缝合点、幻想、症状重复、享乐、四种话语、RSI 和叙事冲突 |
| **跨来源互证** | 跨聊天、访谈和写作材料的来源互证候选 |
| **人工审核** | CLI 和 JSON 审核文件驱动的人工审核流程 |
| **同意管理** | 参与者同意、过期、撤回和派生数据清理 |
| **拓扑导出** | 旧版分析流水线的证据校验、文化注释、模糊接地和拓扑导出 |

---

## 02 安装

```bash
uv venv
uv pip install -e ".[dev]"
```

或：

```bash
pip install -e ".[dev]"
```

---

## 03 快速开始

### 传统证据分析

```bash
lacan-agent init --project demo
lacan-agent add-participant --project demo --id A --consent consent.json
lacan-agent add-source --project demo --participant A --file story.txt
lacan-agent analyze --project demo --participant A --source story.txt --mock
lacan-agent review --run <run_id> --decision approve
lacan-agent export --run <run_id> --pretty
```

### 多源主体结构画像

先创建来源清单。路径相对于 `sources.json` 所在目录解析，也可以通过 `--root` 指定材料根目录：

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

访谈 JSON 使用回答文本和问题 ID：

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

构建和查看：

```bash
lacan-agent subject build --participant A --sources sources.json --mode full --batch-size 80 --with-relations --cards-dir data/subject-artifacts
lacan-agent subject show --participant A --cards-dir data/subject-artifacts
lacan-agent subject inspect-motifs --participant A --cards-dir data/subject-artifacts
lacan-agent subject inspect-relations --participant A --cards-dir data/subject-artifacts
lacan-agent subject show-batch-failures --participant A --cards-dir data/subject-artifacts
```

主体分析按重叠窗口覆盖全部消息。原文和规范化文本同时保留在本地处理中，戏仿、谐音、重复标点和模板变体只作为候选；单次表达不会自动进入稳定语言特征。关系层先生成有向互动事件，再由 Qwen 复核关系候选，所有候选都保留 span、时间和场景证据。可用 `--aliases aliases.json` 提供人工确认的参与者别名表，未确认别名不会自动合并。

Qwen 结构抽取需要设置环境变量：

```powershell
$env:DASHSCOPE_API_KEY = "sk-your-key"
lacan-agent subject build --participant A --sources sources.json --cards-dir data/subject-artifacts
```

Qwen 失败时仍会生成观察层画像。结构候选必须人工审核：

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

```bash
lacan-agent subject review --participant A --input review.json --cards-dir data/subject-artifacts
lacan-agent subject export --participant A --cards-dir data/subject-artifacts --output subject.json
```

### 交互式界面

```powershell
.\start.ps1
```

交互菜单支持传统证据分析，以及主体结构画像的构建、摘要查看和结构候选审核。

---

## 04 API 服务

### 启动服务

```bash
uvicorn lacan_agent.api:app --host 127.0.0.1 --port 8000
```

API 仅绑定本机地址，支持 `.txt`、`.md` 和 `.pdf` 文件上传，单文件大小受 `LACAN_MAX_UPLOAD_BYTES` 限制。

**端口配置**：默认使用 8000 端口。如果端口被占用，可以指定其他端口：

```bash
# 使用 8001 端口
uvicorn lacan_agent.api:app --host 127.0.0.1 --port 8001

# 使用 5000 端口
uvicorn lacan_agent.api:app --host 127.0.0.1 --port 5000
```

后续 API 调用示例均使用 8000 端口，如果使用了其他端口，请相应替换 URL 中的端口号。

### API Key 认证

通过环境变量 `LACAN_API_KEY` 启用 API Key 认证：

```bash
# 启用认证
export LACAN_API_KEY=$(openssl rand -hex 32)
uvicorn lacan_agent.api:app --host 127.0.0.1 --port 8000
```

**本地开发**：不设置 `LACAN_API_KEY` 时，API 无需认证，方便快速调试。

**启用认证**：设置 API Key 后，所有 API 请求需要携带 Bearer Token：

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/v1/projects
```

**Vibe Coding 示例**（Python）：

```python
import requests

API_BASE = "http://localhost:8000"
API_KEY = "your-api-key-here"
headers = {"Authorization": f"Bearer {API_KEY}"}

# 创建项目
requests.post(f"{API_BASE}/api/v1/projects", 
              json={"id": "demo", "owner_id": "researcher"},
              headers=headers)

# 上传材料
with open("story.txt", "rb") as f:
    requests.post(f"{API_BASE}/api/v1/participants/A/sources",
                  files={"file": f},
                  data={"project_id": "demo"},
                  headers=headers)
```

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

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/v1/projects` | 创建项目 |
| `POST` | `/api/v1/participants` | 添加参与者 |
| `POST` | `/api/v1/participants/{pid}/sources` | 上传材料 |
| `POST` | `/api/v1/analysis-runs` | 运行分析 |
| `GET` | `/api/v1/analysis-runs/{rid}` | 查询运行状态 |
| `POST` | `/api/v1/analysis-runs/{rid}/reviews` | 提交审核 |
| `GET` | `/api/v1/analysis-runs/{rid}/packet` | 导出审核包 |
| `GET` | `/api/v1/analysis-runs/{rid}/graph` | 导出图谱 |
| `POST` | `/api/v1/participants/{pid}/withdraw` | 撤回参与者 |

---

## 05 隐私与授权

| 原则 | 说明 |
|------|------|
| **默认关闭** | 所有画像和生成授权默认关闭，必须显式同意 |
| **细粒度控制** | `profile_analysis`、`agent_simulation`、`story_generation` 和 `public_export` 分开控制 |
| **原文保护** | 原始文本不写入 ProfileArtifact 的观察层和生成提示 |
| **撤回清理** | 撤回会清理原始材料、EvidenceSpan、结构候选、画像、审核文件和派生导出 |
| **审计记录** | 只保留匿名 ID、时间、操作和清理结果 |
| **本地存储** | 本地 `data/` 下的画像、报告、数据库和上传材料默认不提交到 GitHub |

---

## 06 测试

```bash
pytest tests/ -q
```

测试覆盖材料导入、访谈 span、证据引用、结构候选审核、撤回边界、SQLite 存储、Qwen Provider、拓扑计算和 CLI 工作流。

---

## 07 技术栈

| 组件 | 技术 |
|------|------|
| **语言** | Python 3.12+ |
| **数据验证** | Pydantic v2 |
| **数据库** | SQLite + FTS5 |
| **Web 框架** | FastAPI |
| **LLM API** | DashScope OpenAI-compatible API |
| **测试框架** | pytest |

---

## 08 当前边界

1.0 提供多源主体结构分析和审核后的画像输入层，为后续生成策略提供基础。

---

## 09 License

MIT

---

<div align="center">

**Lacan-Agent** · 基于证据的主体结构分析

</div>

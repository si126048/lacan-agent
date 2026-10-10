# Lacan-Agent

**基于拉康话语理论的主体结构分析工具**

---

<div align="left">

| | |
|---|---|
| **版本** | 2.0 |
| **Python** | 3.12+ |
| **测试** | 230 passed |
| **许可** | MIT |

</div>

---

## 概述

Lacan-Agent 是一个本地研究工具，用于把聊天、访谈、写作样本和研究观察整理成可追溯的主体结构画像。v2.0 新增对抗性多视角分析（拉康 vs 德勒兹）和 PageIndex 文档系统，支持长篇精神分析文本的处理与引文验证。

项目关注的是证据化的经验分析，不是临床诊断，也不会把语言口癖直接等同于人格。每个结构候选都必须引用材料中的证据 span，默认状态为 `candidate`，只有人工审核通过后才能进入生成策略。

---

## 目录

```
01  功能特性
02  安装
03  快速开始
04  对抗性多视角分析
05  文档系统
06  API 服务
07  隐私与授权
08  测试
09  技术栈
10  当前边界
11  License
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

### 2.0 新增功能

| 功能 | 描述 |
|------|------|
| **对抗性多视角分析** | 多个理论视角独立分析同一文本后交叉批评，产出更稳健的结果 |
| **拉康 vs 德勒兹** | 内置两个对抗视角：拉康（能指/匮乏/结构）与德勒兹（装配/生成/机器） |
| **四阶段辩证管线** | 独立分析 → 交叉批评 → 综合 → 可选报告生成 |
| **可扩展视角注册** | 放置新 JSON 配置到 `perspectives/` 目录即可自动发现（福柯、德里达等） |
| **PageIndex 文档存储** | 内容寻址（SHA-256 doc_id）、SQLite + FTS5 全文检索 |
| **层级大纲检测** | 自动识别 BOOK/CHAPTER/SECTION 结构（英/法/德/西/意多语言） |
| **引文验证** | NFKC 归一化 + 空白折叠，跨版本/OCR 引文匹配 |
| **多格式文档提取** | txt/md、pdf（pypdf）、html、epub、office（可选） |

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

## 04 对抗性多视角分析

v2.0 引入 MISAKA-Agent 式的对抗结构：多个理论视角对同一文本进行独立分析，然后交叉批评，产出更稳健的分析结果。

### 哲学对抗轴

| 维度 | 拉康 | 德勒兹 |
|------|------|--------|
| 本体论 | 匮乏/缺失驱动主体 | 充盈/生产驱动机器 |
| 语言 | 能指链优先，无意识像语言一样结构 | 语用学优先，语言是欲望机器的装配 |
| 结构 | 三角结构（想象/象征/实在） | 多元体/根茎（去中心化网络） |
| 欲望 | 欲望 = 对他者的欲望 | 欲望 = 生产性机器 |
| 重复 | 强迫性重复，回返被压抑者 | 差异的重复，每次都是新的生产 |
| 方法 | 解读症状背后的能指逻辑 | 绘制装配的连接与断裂 |

### 四阶段流程

```
Phase 1 — 独立分析    每个视角独立跑 observe + interpret
Phase 2 — 交叉批评    N 个视角 round-robin 配对（i 批评 i+1）
Phase 3 — 综合        接收全部 Phase 1+2 结果，产出综合报告
Phase 4 — 报告        可选：生成自然语言综合报告
```

### CLI 使用

```bash
# 列出可用视角
lacan-agent perspectives

# 拉康-德勒兹对抗分析
lacan-agent dialectical-analyze \
  --perspectives lacan,deleuze \
  --participant A --project demo --source story.txt --mock

# 生成综合报告
lacan-agent dialectical-analyze \
  --perspectives lacan,deleuze \
  --participant A --project demo --source story.txt --mock --report
```

### 扩展新视角

在 `lacan_agent/perspectives/` 目录下放置新的 JSON 配置文件即可自动注册：

```json
{
  "id": "foucault",
  "name": "Foucauldian Power/Knowledge",
  "concept_inventory": ["power_knowledge", "disciplinary_power", "governmentality", "biopower"],
  "blind_spots": ["tends to reduce subjective experience to power effects"],
  "vocabulary": {
    "dispositif": "异质元素的异质集合——话语、制度、建筑、命题构成的网络"
  },
  "evidence_prompt_variant": null,
  "interpreter_prompt_variant": null,
  "critique_prompt_variant": null
}
```

---

## 05 文档系统

PageIndex 文档系统（移植自 MISAKA-Agent）支持长篇精神分析文本的处理。

### 文档导入

```bash
# 导入文档（自动检测格式、提取页面、检测大纲）
lacan-agent doc-ingest --path book.pdf --project demo
lacan-agent doc-ingest --path seminar.txt --project demo --title "研讨班 XI"

# 支持格式：txt, md, pdf, html, epub, docx, xlsx, pptx
```

### 文档查询

```bash
# 查看文档大纲
lacan-agent doc-outline --doc-id abc123def456

# 全文检索
lacan-agent doc-search --query "objet petit a" --project demo
lacan-agent doc-search --query "能指链" --doc-id abc123def456

# 验证引文
lacan-agent doc-verify --doc-id abc123def456 --quote "欲望是他者的欲望" --page 47
```

### 存储架构

| 组件 | 说明 |
|------|------|
| **内容寻址** | SHA-256 前 12 位作为 doc_id，相同文档自动去重 |
| **页级存储** | 每页文本独立存储，支持页级导航和检索 |
| **FTS5 全文索引** | SQLite FTS5 虚拟表，支持中文分词检索 |
| **大纲检测** | 自动识别 CHAPTER/BOOK/SECTION 等层级结构 |
| **引文归一化** | NFKC  Unicode 归一化 + 连字符/软连字符/空白折叠 |

---

## 06 API 服务

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

**多视角辩证分析**：

```bash
curl -X POST http://localhost:8000/api/v1/dialectical/run \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "demo",
    "participant_id": "A",
    "source_ids": ["source_1"],
    "perspective_ids": ["lacan", "deleuze"],
    "idempotency_key": "dial_001",
    "generate_report": true
  }'
```

**列出可用视角**：

```bash
curl http://localhost:8000/api/v1/perspectives
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
| `POST` | `/api/v1/dialectical/run` | 运行多视角辩证分析 |
| `GET` | `/api/v1/perspectives` | 列出可用理论视角 |

---

## 07 隐私与授权

| 原则 | 说明 |
|------|------|
| **默认关闭** | 所有画像和生成授权默认关闭，必须显式同意 |
| **细粒度控制** | `profile_analysis`、`agent_simulation`、`story_generation` 和 `public_export` 分开控制 |
| **原文保护** | 原始文本不写入 ProfileArtifact 的观察层和生成提示 |
| **撤回清理** | 撤回会清理原始材料、EvidenceSpan、结构候选、画像、审核文件和派生导出 |
| **审计记录** | 只保留匿名 ID、时间、操作和清理结果 |
| **本地存储** | 本地 `data/` 下的画像、报告、数据库和上传材料默认不提交到 GitHub |

---

## 08 测试

```bash
pytest tests/ -q
```

测试覆盖材料导入、访谈 span、证据引用、结构候选审核、撤回边界、SQLite 存储、Qwen Provider、拓扑计算、CLI 工作流、对抗性多视角辩证分析、视角注册、文档大纲检测、引文验证和文档存储。

---

## 09 技术栈

| 组件 | 技术 |
|------|------|
| **语言** | Python 3.12+ |
| **数据验证** | Pydantic v2 |
| **数据库** | SQLite + FTS5 |
| **Web 框架** | FastAPI |
| **LLM API** | DashScope OpenAI-compatible API |
| **文档提取** | pypdf (PDF), HTMLParser (HTML), zipfile (EPUB) |
| **测试框架** | pytest |

---

## 10 当前边界

v2.0 提供多源主体结构分析、对抗性多视角辩证分析和 PageIndex 文档系统，为后续生成策略和更多理论视角（福柯、德里达等）的扩展提供基础。

---

## 11 License

MIT

---

<div align="center">

**Lacan-Agent** · 基于证据的主体结构分析

</div>

# Hermeneut-Agent

**对抗性多视角话语分析工具** — 形式化记号驱动的多理论视角辩证分析，产出可追溯的证据化主体结构画像。

> v2.2 · Python 3.12+ · 267 tests · MIT

---

## 这是什么

Hermeneut 把聊天、访谈、写作样本等研究材料转化为**有证据追溯的主体结构分析**。每个结构候选都必须引用原文证据 span，默认状态为 `candidate`，只有人工审核通过后才进入后续流程。

核心架构是**形式化记号驱动的对抗性多视角分析**：拉康与德勒兹各有独立的形式化记号体系（mathemes / 装配代数），用紧凑的符号表示替代自然语言概念解释，在压缩 token 消耗的同时减少语义漂移。同时内置 PageIndex 文档系统，支持长篇精神分析文本的导入、检索和引文验证。

这不是临床诊断工具，也不把语言口癖直接等同于人格。

---

## 核心能力

| | |
|---|---|
| **形式化记号系统** | 拉康 mathemes ($, a, S₁, D_m) + 德勒兹装配代数 (Ag, Dt, BwO)，全阶段 token 压缩 38-69% |
| **对抗性辩证分析** | 多视角独立分析 → 交叉批评 → 综合，内置拉康 vs 德勒兹 |
| **多源材料导入** | 聊天、访谈、写作样本统一导入，支持 UTF-8 / GB18030 / 微信格式 |
| **证据追溯** | `MaterialSource` → `EvidenceSpan` → `StructuralCandidate`，全链路来源 checksum |
| **可扩展视角** | 放置 JSON 配置到 `perspectives/` 即可自动注册（福柯、德里达等） |
| **PageIndex 文档系统** | 内容寻址存储 (SHA-256)、FTS5 全文检索、层级大纲检测、引文验证 |
| **多格式提取** | txt / md / pdf / html / epub / docx / xlsx / pptx |
| **人工审核门禁** | CLI + JSON 审核文件驱动，所有结构候选必须人工批准 |
| **同意管理** | 细粒度同意 scope、过期、撤回与派生数据清理 |

---

## 形式化记号系统

v2.1 的核心创新。Agent 内部交流使用数学/拓扑形式表示替代自然语言概念解释，压缩 context 长度、减少语义漂移。

### 拉康记号

```
主体:  $ = 分裂主体    a = objet petit a    A = 大他者
能指:  S₁ = 主人能指   S₂ = 知识            S = 能指
运算:  ◇ = 幻想($◇a)  / = 压抑             → = 转喻    ∩ = 隐喻
享乐:  J = 享乐        JΦ = 阳具享乐        j = 剩余享乐

四话语代数:
  Dm [S₁→S₂/$→a]   主人话语 — 权威/命令
  Du [S₂→a/S₁→$]   大学话语 — 中立/知识
  Dh [$→S₁/a→S₂]   歇斯底里话语 — 质疑/症状
  Da [a→$/S₂→S₁]   分析者话语 — 沉默/脱落

注册: S=象征界  I=想象界  R=实在界
```

### 德勒兹记号

```
核心:  Ag = 装配    Rz = 根茎    Dm = 欲望机器    BwO = 无器官身体
运动:  Dt = 去领土化  Rt = 再领土化  Lf = 逃逸线  Bec = 生成
本体:  Mul = 多元体   Aff = 情动    Int = 强度     V↔A = 虚拟↔实际
尺度:  Mol = 大尺度(刚性)    mo = 分子(流动)

运算:  × = 异质连接   ↗ = 去领土化方向   ↘ = 再领土化方向   ∅ = 解体化   ≡ = 编码
注册:  M = 机器连接   D = 去领土化运动   B = 生成过程   I = 强度/情动
```

### Token 压缩效果

| 阶段 | 原版 | 形式化 | 压缩 |
|------|-----:|-------:|-----:|
| evidence (Lacan) | 667t | 211t | **↓68%** |
| interpreter (Lacan) | 746t | 312t | **↓58%** |
| critic (Lacan) | 477t | 238t | **↓50%** |
| cross-critique | 291t | 150t | **↓49%** |
| synthesis | 407t | 191t | **↓53%** |
| profile inference | 258t | 140t | **↓46%** |
| structural | 282t | 172t | **↓39%** |

---

## 安装

```bash
# uv（推荐）
uv venv && uv pip install -e ".[dev]"

# pip
pip install -e ".[dev]"
```

---

## 快速开始

### 证据分析流程

```bash
hermeneut init --project demo
hermeneut add-participant --project demo --id A --consent consent.json
hermeneut add-source --project demo --participant A --file story.txt
hermeneut analyze --project demo --participant A --source story.txt --mock
hermeneut review --run <run_id> --decision approve
hermeneut export --run <run_id> --pretty
```

### 对抗性多视角分析

```bash
# 列出可用视角
hermeneut perspectives

# 拉康 vs 德勒兹对抗分析
hermeneut dialectical-analyze \
  --perspectives lacan,deleuze \
  --participant A --project demo --source story.txt --mock

# 含综合报告
hermeneut dialectical-analyze \
  --perspectives lacan,deleuze \
  --participant A --project demo --source story.txt --mock --report
```

### 文档系统

```bash
hermeneut doc-ingest --path book.pdf --project demo
hermeneut doc-search --query "objet petit a" --project demo
hermeneut doc-outline --doc-id <doc_id>
hermeneut doc-verify --doc-id <doc_id> --quote "欲望是他者的欲望" --page 47
```

### 交互式界面

```powershell
.\start.ps1
```

---

## 对抗性多视角分析

多个理论视角对同一文本独立分析后交叉批评，暴露各自盲区，产出比单一视角更稳健的结果。

### 哲学对抗轴

| 维度 | 拉康 | 德勒兹 |
|------|------|--------|
| **本体论** | 匮乏/缺失驱动主体 | 充盈/生产驱动机器 |
| **语言** | 能指链优先，无意识像语言一样结构 | 语用学优先，语言是欲望机器的装配 |
| **结构** | 三角结构（想象/象征/实在） | 多元体/根茎（去中心化网络） |
| **欲望** | 欲望 = 对他者的欲望 | 欲望 = 生产性机器 |
| **重复** | 强迫性重复，回返被压抑者 | 差异的重复，每次都是新的生产 |
| **方法** | 解读症状背后的能指逻辑 | 绘制装配的连接与断裂 |

### 四阶段辩证管线

```
Phase 1  独立分析    每个视角用形式化记号独立跑 observe + interpret
Phase 2  交叉批评    N 个视角 round-robin 配对（i 批评 i+1）
Phase 3  综合        接收全部 Phase 1+2 结果，产出综合报告
Phase 4  报告        可选：生成自然语言综合报告
```

### 扩展新视角

在 `hermeneut/perspectives/` 放置 JSON 配置文件即可自动发现：

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

## 文档系统

移植自 MISAKA-Agent 的 PageIndex 文档系统，支持长篇精神分析文本的处理与引文验证。

| 组件 | 说明 |
|------|------|
| **内容寻址** | SHA-256 前 12 位作为 doc_id，相同文档自动去重 |
| **页级存储** | 每页文本独立存储，支持页级导航和检索 |
| **FTS5 全文索引** | SQLite FTS5 虚拟表，支持中文分词检索 |
| **大纲检测** | 自动识别 CHAPTER / BOOK / SECTION 层级（英/法/德/西/意多语言） |
| **引文归一化** | NFKC Unicode 归一化 + 连字符/软连字符/空白折叠，跨版本 OCR 匹配 |

---

## API

### 启动

```bash
uvicorn hermeneut.api:app --host 127.0.0.1 --port 8000
```

默认仅绑定本机地址。设置 `LACAN_API_KEY` 环境变量启用 Bearer Token 认证；不设置时无需认证。

### 端点

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

### 示例

```bash
# 创建项目
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"id": "demo", "owner_id": "researcher"}'

# 上传材料
curl -X POST "http://localhost:8000/api/v1/participants/A/sources" \
  -F "project_id=demo" -F "file=@story.txt"

# 运行辩证分析
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

---

## ACP（Agent Client Protocol）

Hermeneut 支持通过 ACP 协议在 Zed 等编辑器中直接调用，选中文字即可分析。

### 启动

```bash
hermeneut-acp --mock          # 无需 API key（mock 模式）
hermeneut-acp                 # 需要 DASHSCOPE_API_KEY
python -m hermeneut.acp --mock
```

### Zed 配置

在 Zed `settings.json` 中添加：

```json
{
  "agent_servers": {
    "hermeneut": {
      "type": "custom",
      "command": "python",
      "args": ["-m", "hermeneut.acp", "--mock"]
    }
  }
}
```

### 支持的操作

| 输入示例 | 操作 |
|----------|------|
| "列出可用视角" / "perspectives" | 列出已注册的理论视角 |
| "分析以下文本：..." | 单视角证据分析 |
| "辩证分析：..." | 拉康 vs 德勒兹对抗性分析 |
| "搜索：能指" | 文档全文检索 |

---

## 隐私与伦理

| 原则 | 说明 |
|------|------|
| **默认关闭** | 画像和生成授权默认关闭，必须显式同意 |
| **细粒度控制** | `profile_analysis` / `agent_simulation` / `story_generation` / `public_export` 分开控制 |
| **原文保护** | 原始文本不写入 ProfileArtifact 的观察层和生成提示 |
| **撤回清理** | 撤回时清理原始材料、EvidenceSpan、结构候选、画像、审核文件和派生导出 |
| **本地存储** | 数据库和上传材料默认不提交到 GitHub |

---

## 开发

```bash
pytest tests/ -q          # 运行全部测试 (267)
ruff check hermeneut/     # 代码检查
```

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.12+ |
| 数据验证 | Pydantic v2 |
| 数据库 | SQLite + FTS5 |
| Web 框架 | FastAPI + Uvicorn |
| LLM | DashScope (通义千问) OpenAI-compatible API |
| 形式化记号 | `hermeneut/formal/` — mathemes + discourse algebra + register taxonomy |
| 文档提取 | pypdf / HTMLParser / zipfile |
| 测试 | pytest + pytest-asyncio |

---

## 多源主体结构画像

除单源证据分析外，Hermeneut 支持跨来源互证的主体结构画像构建：

```json
{
  "sources": [
    { "source_id": "chat_a", "participant_id": "A", "source_type": "chat", "path": "chat.txt" },
    { "source_id": "interview_a", "participant_id": "A", "source_type": "interview", "path": "interview.json" },
    { "source_id": "writing_a", "participant_id": "A", "source_type": "writing", "path": "continuation.txt" }
  ]
}
```

```bash
hermeneut subject build --participant A --sources sources.json --mode full \
  --batch-size 80 --with-relations --cards-dir data/subject-artifacts
hermeneut subject show --participant A --cards-dir data/subject-artifacts
hermeneut subject review --participant A --input review.json --cards-dir data/subject-artifacts
hermeneut subject export --participant A --cards-dir data/subject-artifacts --output subject.json
```

主体分析按重叠窗口覆盖全部消息。关系层先生成有向互动事件，再由 Qwen 复核关系候选。所有候选保留 span、时间和场景证据。可用 `--aliases aliases.json` 提供人工确认的参与者别名表。

Qwen 结构抽取需要设置 `DASHSCOPE_API_KEY` 环境变量。Qwen 失败时仍会生成观察层画像。

---

## 致谢

Hermeneut-Agent 的文档系统（`hermeneut/documents/`）移植自 [MISAKA-Agent](https://github.com/Luciole-Studio/Misaka-Agent)（Copyright 2026 Luciole Studio, [Apache License 2.0](LICENSE-MISAKA)），包括内容寻址存储、层级大纲检测、引文归一化验证和多格式文本提取器。对抗性多视角辩证分析的架构设计亦受 MISAKA 多智能体编排的启发。详见 [NOTICE](NOTICE)。

---

MIT License

# Lacan-Agent

基于拉康精神分析理论的话语分析工具。通过 evidence-constrained 流水线处理群聊文本数据，生成结构化的话语分析结果。

## 核心流程

```
Ingest → Evidence → Observation → Annotation → Interpretation → Critique → Fuzzy Grounding → Human Review → Compile → Export
```

- **Evidence**: 从参与者文本中提取可验证的证据片段（EvidenceSpan）
- **Observation**: 识别话语模式（能指链、重复、言说主体等），标注 RSI 注册归属
- **Annotation**: 文化语境注释（游戏/著作/梗自动识别）
- **Interpretation**: 基于拉康理论概念构建假设（四种话语、数学式、缝合点、欲望剩余）
- **Critique**: 独立反例审查 + 模糊否定强度评估 + 幻觉风险检测
- **Fuzzy Grounding**: 连续隶属度评分替代二值证据链接，抑制 LLM 幻觉
- **Human Review**: 人工审核批准/退回/拒绝
- **Export**: 生成类型化图谱（含数学式节点、话语轨迹、缝合点）和叙事操作符

## v0.2 变更 (2026-10-09)

### Phase A: 数学核心
- **Matheme 代数**: `S`, `s`, `S(A)`, `a`, `◇`, `$` 作为一等数据结构，带 valence 值 [-1, +1]
- **Borromean RSI 拓扑**: 三界（Real/Symbolic/Imaginary）连贯性监控，滑动窗口检测"解结"事件
- **四话语代数**: Master→Hysteric→Analyst→University 作为 Z/4Z 循环群，`quarter_turn_cw()` 实现话语旋转

### Phase B: 模糊证据框架
- **MembershipFunction**: 加权隶属度计算（lexical 0.5 + proximity 0.3 + temporal 0.2）
- **模糊运算**: t-norm (min), t-conorm (概率和), 补集 (1-μ), α-截集
- **HallucinationGuard**: 低/中/高风险分级，自动标记 `grounding_score < 0.3` 的假设

### Phase C: 背景审查
- **CJK-aware 文化注释**: 正则匹配 + CJK 边界处理（中文无需 `\b`，Latin 用 `(?<![a-zA-Z])`）
- **30 条初始词典**: 游戏（原神/明日方舟）、理论家（拉康/弗洛伊德/齐泽克）、网络梗（内卷/躺平/yyds）

### Phase D: 并发基础设施
- **ConcurrentAnalyzer**: `asyncio.Semaphore` + `ThreadPoolExecutor`，每线程独立 SQLite 连接
- **批量 API**: `POST /api/v1/analysis-runs/batch` 支持多参与者并行分析

### Phase E: 集成与导出增强
- **LLM Prompt 升级**: RSI 注册标注、话语类型判定、模糊否定强度、幻觉论断检测
- **Export 增强**: 新增 `topology`（话语轨迹、缝合点）、`annotations`、`hallucination_reports`
- **图节点扩展**: `matheme`、`capiton_point` 类型；`discourse_rotation`、`metaphor`、`metonymy` 边类型

## 安装

```bash
# 使用 uv（推荐）
uv venv
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

## 快速开始

### CLI 命令行

```bash
# 初始化项目
lacan-agent init --project demo

# 导入理论文献
lacan-agent ingest-theory --project demo --path fixtures/synthetic/theory.md

# 注册参与者（需要授权文件）
lacan-agent add-participant --project demo --id A --consent fixtures/synthetic/consent.json

# 导入参与者文本
lacan-agent add-source --project demo --participant A --file fixtures/synthetic/story.txt

# 运行分析（Mock 模式）
lacan-agent analyze --project demo --participant A --source story.txt --mock

# 审核并导出
lacan-agent review --run <run_id> --decision approve
lacan-agent export --run <run_id> --pretty
```

### 交互式界面

```powershell
# Windows PowerShell
.\start.ps1

# 或绕过执行策略
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

### API 服务

```bash
uvicorn lacan_agent.api:app --reload
```

API 默认面向本机使用。理论文献和参与者文本通过 `multipart/form-data` 上传，支持 `.txt`、`.md`、`.pdf`，默认单文件上限为 10 MiB（可用 `LACAN_MAX_UPLOAD_BYTES` 调整）；不会接受服务器任意路径。

默认数据库路径 `./data/lacan.db`，可通过 `--db` 或 `LACAN_DB_PATH` 环境变量覆盖。

参与者撤回后，系统会删除其原始文档、证据片段、全文索引和分析运行，仅保留最小化的撤回审计记录；撤回后的参与者不能继续分析、审核或导出。

**批量分析端点:**

```bash
POST /api/v1/analysis-runs/batch
{
  "tasks": [
    {"project_id": "demo", "participant_id": "A", "source_ids": ["s1"], "idempotency_key": "k1"},
    {"project_id": "demo", "participant_id": "B", "source_ids": ["s2"], "idempotency_key": "k2"}
  ],
  "max_concurrent": 4
}
```

### 使用通义千问（Qwen）

设置环境变量后，分析命令会自动使用真实 LLM：

```bash
export DASHSCOPE_API_KEY=sk-your-key
lacan-agent analyze --project demo --participant A --source story.txt
```

## 项目结构

```
lacan_agent/
├── cli.py              # 命令行入口
├── api.py              # FastAPI 服务（含批量分析端点）
├── interactive.py      # 交互式终端 UI
├── workflow.py         # 分析流水线（含模糊接地、文化注释）
├── models.py           # Pydantic v2 数据模型（含拓扑扩展）
├── db.py               # SQLite + FTS5 存储层
├── rag.py              # 文本摄入、分块、搜索
├── llm.py              # LLM Provider（FakeProvider / QwenProvider，v0.2 prompt）
├── fuzzy.py            # 模糊集合运算 + HallucinationGuard
├── annotation.py       # CJK-aware 文化注释器
├── concurrent.py       # 并发分析器（Semaphore + per-thread Store）
├── config.py           # 配置管理
└── topology/           # 数学化/拓扑结构
    ├── __init__.py
    ├── mathemes.py     # Matheme 代数类型
    ├── borromean.py    # Borromean RSI 拓扑监控
    └── discourses.py   # 四话语代数（Z/4Z 循环群）

fixtures/
└── cultural_gazetteer.json  # 文化实体词典（30 条）
```

## 伦理与同意

本工具遵循严格的伦理框架：

- **Opt-in 同意**: 所有同意项默认为 `false`，必须显式授权
- **可撤回**: 参与者可随时撤回同意，系统将阻止后续分析
- **数据隔离**: 参与者数据按项目和授权范围严格隔离
- **审计追踪**: 所有状态变更记录在案，不可篡改
- **幻觉守卫**: 低接地分数的假设自动标记，防止 LLM 编造

> 这是一个研究工具。它不诊断个人、推断私密的无意识内容、或提供治疗。

## 测试

```bash
pytest tests/ -v
```

当前 **163 个测试**覆盖全部核心模块：

- `test_db.py` / `test_models.py` / `test_rag.py` / `test_llm.py` / `test_workflow.py` / `test_cli.py` — 基础模块 (74)
- `test_topology.py` — Matheme + Borromean + 四话语 (34)
- `test_fuzzy.py` — 模糊运算 + HallucinationGuard (21)
- `test_annotation.py` — 文化注释器 (15)
- `test_concurrent.py` — 并发分析 (7)
- `test_integration_v02.py` — v0.2 端到端集成 (12)

## 技术栈

- Python 3.12+
- Pydantic v2（数据验证）
- SQLite + FTS5（存储与全文搜索）
- FastAPI（HTTP API）
- DashScope OpenAI-compatible API（通义千问接入）
- aiosqlite（异步 SQLite，并发场景）

## License

MIT

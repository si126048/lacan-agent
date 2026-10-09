# Lacan-Agent

基于拉康精神分析理论的话语分析工具。通过 evidence-constrained 流水线处理群聊文本数据，生成结构化的话语分析结果。

## 核心流程

```
Ingest → Evidence → Observation → Interpretation → Critique → Human Review → Compile → Export
```

- **Evidence**: 从参与者文本中提取可验证的证据片段（EvidenceSpan）
- **Observation**: 识别话语模式（能指链、重复、言说主体等）
- **Interpretation**: 基于拉康理论概念构建假设（四种话语、对象a、RSI三界等）
- **Critique**: 独立反例审查，按假设分组分配反例
- **Human Review**: 人工审核批准/退回/拒绝
- **Export**: 生成类型化图谱和叙事操作符

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

默认数据库路径 `./data/lacan.db`，可通过 `--db` 或 `LACAN_DB_PATH` 环境变量覆盖。

### 使用通义千问（Qwen）

设置环境变量后，分析命令会自动使用真实 LLM：

```bash
export DASHSCOPE_API_KEY=sk-your-key
lacan-agent analyze --project demo --participant A --source story.txt
```

## 项目结构

```
lacan_agent/
├── cli.py          # 命令行入口
├── api.py          # FastAPI 服务
├── interactive.py  # 交互式终端 UI
├── workflow.py     # 分析流水线（evidence → observe → interpret → critique）
├── models.py       # Pydantic v2 数据模型
├── db.py           # SQLite + FTS5 存储层
├── rag.py          # 文本摄入、分块、搜索
├── llm.py          # LLM Provider（FakeProvider / QwenProvider）
└── config.py       # 配置管理
```

## 伦理与同意

本工具遵循严格的伦理框架：

- **Opt-in 同意**: 所有同意项默认为 `false`，必须显式授权
- **可撤回**: 参与者可随时撤回同意，系统将阻止后续分析
- **数据隔离**: 参与者数据按项目和授权范围严格隔离
- **审计追踪**: 所有状态变更记录在案，不可篡改

> 这是一个研究工具。它不诊断个人、推断私密的无意识内容、或提供治疗。

## 测试

```bash
pytest tests/ -v
```

当前 74 个测试覆盖全部核心模块（db / models / rag / llm / workflow / cli）。

## 技术栈

- Python 3.12+
- Pydantic v2（数据验证）
- SQLite + FTS5（存储与全文搜索）
- FastAPI（HTTP API）
- DashScope OpenAI-compatible API（通义千问接入）

## License

MIT

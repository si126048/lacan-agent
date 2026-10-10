# Lacan-Agent 1.0

Lacan-Agent 是一个本地研究工具，用于把聊天、访谈、写作样本和研究观察整理成可追溯的主体结构画像，为后续受控 PersonaAgent 和五人故事接龙提供输入。

项目关注的是证据化的经验分析，不是临床诊断，也不会把语言口癖直接等同于人格。每个结构候选都必须引用材料中的证据 span，默认状态为 `candidate`，只有人工审核通过后才能进入生成策略。

## 1.0 提供的功能

- 聊天、访谈、写作和观察材料的统一导入。
- UTF-8、GB18030、普通逐行文本和微信聊天格式解析。
- 稳定的 `MaterialSource`、`EvidenceSpan` 和来源 checksum。
- 消息长度、语气词、括号、拟声词、emoji、媒体和互动对象等观察层统计。
- 基于 Qwen 的证据约束结构候选抽取。
- 拉康结构维度候选：话语位置、大他者、需求与欲望、重复能指、缝合点、幻想、症状重复、享乐、四种话语、RSI 和叙事冲突。
- 跨聊天、访谈和写作材料的来源互证候选。
- CLI 和 JSON 审核文件驱动的人工审核。
- 参与者同意、过期、撤回和派生数据清理。
- 旧版分析流水线的证据校验、文化注释、模糊接地和拓扑导出。

五人故事接龙调度器、共享故事记忆和五个 PersonaAgent 的运行时不属于 1.0，本版本提供的是它们所需的主体结构输入层。

## 安装

```bash
uv venv
uv pip install -e ".[dev]"
```

或：

```bash
pip install -e ".[dev]"
```

## 快速开始

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

### 五人快捷统计画像

```bash
lacan-agent profile build --all --texts-dir data/participant_texts --cards-dir data/profile-cards
lacan-agent profile show --participant 灯 --cards-dir data/profile-cards
```

### 交互式界面

```powershell
.\start.ps1
```

交互菜单支持传统证据分析，以及主体结构画像的构建、摘要查看和结构候选审核。

## API

API 默认绑定本机，使用上传文件而不是服务器路径。支持 `.txt`、`.md` 和 `.pdf`，单文件大小受 `LACAN_MAX_UPLOAD_BYTES` 限制。

```bash
uvicorn lacan_agent.api:app --host 127.0.0.1 --port 8000
```

## 隐私与授权

- 所有画像和生成授权默认关闭，必须显式同意。
- `profile_analysis`、`agent_simulation`、`story_generation` 和 `public_export` 分开控制。
- 原始文本不写入 ProfileArtifact 的观察层和生成提示。
- 撤回会清理原始材料、EvidenceSpan、结构候选、画像、审核文件和派生导出。
- 审计记录只保留匿名 ID、时间、操作和清理结果。
- 本地 `data/` 下的画像、报告、数据库和上传材料默认不提交到 GitHub。

## 当前边界

1.0 只提供多源主体结构分析和审核后的画像输入层。五个独立 PersonaAgent、轮流调度、共享故事状态、故事接龙评测和长期记忆将在后续版本实现。

## 测试

```bash
pytest tests/ -q
```

测试覆盖材料导入、访谈 span、证据引用、结构候选审核、撤回边界、SQLite 存储、Qwen Provider、拓扑计算和 CLI 工作流。

## 技术栈

Python 3.12+、Pydantic v2、SQLite + FTS5、FastAPI、DashScope OpenAI-compatible API、pytest。

## License

MIT

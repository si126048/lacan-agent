from __future__ import annotations
import json, logging, os, textwrap
from typing import Protocol, Type
from .models import *

logger = logging.getLogger(__name__)

class LLMProvider(Protocol):
    def generate_structured(self, system_prompt: str, user_payload: dict, output_schema: Type[BaseModel], run_context: dict) -> dict: ...

class EmbeddingProvider(Protocol):
    async def embed(self,texts:list[str])->list[list[float]]: ...

class FakeProvider:
    def generate_structured(self, system_prompt, user_payload, output_schema, run_context):
        stage=run_context.get('stage')
        if stage=='evidence': return {'observations':[{'id':'obs_1','label':'文本中出现可复核的重复措辞或意象','evidence_span_ids':user_payload['span_ids'][:1]}]}
        if stage=='interpreter': return {'hypotheses':[{'id':'hyp_1','concept_ids':['repetition'],'support_ids':user_payload['observation_ids'],'alternatives':['体裁惯例或主题回环'],'counterexamples':['当前样本过短，无法排除偶然性'],'status':'provisional','theory_reference_ids':user_payload.get('theory_reference_ids',[])}]}
        if stage=='critic': return {'counterexamples_by_hypothesis':{h_id: [f'反例: 样本规模有限，假设 {h_id} 需更多跨情境材料'] for h_id in user_payload.get('hypothesis_ids', [])},'gaps':['理论引用与文本跨度需由审核者复核']}
        raise ValueError(f"UNKNOWN_STAGE: {stage}")

EVIDENCE_SYSTEM = textwrap.dedent("""\
    你是一位拉康派话语分析研究者。你的任务是从参与者的聊天文本中识别可观察的话语模式。
    请基于以下理论框架进行分析：
    - 能指链（Signifier Chain）：重复出现的措辞、意象、隐喻
    - 重复（Repetition）：跨语境的重复模式，可能揭示无意识结构
    - 言说主体（Subject of Enunciation）：说话者如何定位自己
    - 欲望与缺失（Desire and Lack）：未说出的内容、沉默、回避
    - 大他者（The Other）：消息指向谁？想象中的受众
    - 享乐（Jouissance）：过度的表达、表情符号泛滥、内部笑话
    - RSI三界：象征界（规则/规范）、想象界（认同/竞争）、实在界（创伤/不可能性）

    请从文本中找出 1-5 个具体的、可被证据支持的话语观察。
    每个观察必须引用具体的文本片段（通过 span_id 标注）。
    只描述可观察的现象，不做过度推断。
    返回 JSON 格式：{"observations": [{"id": "obs_N", "label": "观察描述", "evidence_span_ids": ["span_xxx"]}]}""")

INTERPRETER_SYSTEM = textwrap.dedent("""\
    你是一位拉康派话语分析研究者。基于前一阶段的观察结果，构建理论假设。
    请将观察到的话语模式与拉康理论概念关联：
    - 能指/所指（Signifier/Signified）
    - 重复（Repetition）与回返（Return）
    - 言说主体分裂（Split Subject）
    - 欲望图式（Graph of Desire）
    - 四种话语（Four Discourses）：主人、大学、歇斯底里、分析者
    - 对象a（objet petit a）
    - 镜像阶段（Mirror Stage）
    - RSI三界拓扑

    每个假设必须：
    1. 关联到具体的拉康概念（concept_ids）
    2. 由观察结果支持（support_ids）
    3. 提供至少一个替代解释（alternatives）
    4. 提供至少一个反例或限制条件（counterexamples）
    5. 引用理论文献（theory_reference_ids）
    返回 JSON：{"hypotheses": [{"id": "hyp_N", "concept_ids": [...], "support_ids": [...], "alternatives": [...], "counterexamples": [...], "status": "provisional", "theory_reference_ids": [...]}]}""")

CRITIC_SYSTEM = textwrap.dedent("""\
    你是一位严格的学术审稿人，专门审查拉康派话语分析的假设。
    你的任务是寻找反例、替代解释和方法论缺陷。
    请针对每个假设（按 hypothesis_id 分组）：
    1. 提出至少一个反例（counterexample）：什么情况下这个假设不成立？
    2. 指出方法论缺口（gap）：分析中可能存在的偏差或盲点
    3. 考虑文化语境：中文群聊的特殊性是否被充分考虑？
    返回 JSON：{"counterexamples_by_hypothesis": {"hyp_1": ["反例1", ...], "hyp_2": [...]}, "gaps": ["缺口1", ...]}""")


class QwenProvider:
    """通义千问 LLM Provider via DashScope OpenAI-compatible API."""

    def __init__(self, api_key: str | None = None, model: str = "qwen-plus", base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
        from openai import OpenAI
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is required for QwenProvider")
        self.model = model
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)

    def _call(self, system: str, user_content: str) -> dict:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            logger.warning("LLM API call failed: %s", exc)
            raise RuntimeError(f"LLM_API_ERROR: {exc}") from exc
        text = resp.choices[0].message.content
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("LLM returned invalid JSON: %s", exc)
            raise RuntimeError(f"LLM_INVALID_JSON: {exc}") from exc

    def generate_structured(self, system_prompt, user_payload, output_schema, run_context):
        stage = run_context.get('stage')
        if stage == 'evidence':
            spans_text = user_payload.get('spans_text', '')
            span_ids = user_payload.get('span_ids', [])
            user_content = f"以下是参与者的聊天文本片段（span_id 标注在每段开头）：\n\n{spans_text}\n\n请分析这些文本，返回 JSON。可用的 span_ids: {json.dumps(span_ids)}"
            return self._call(EVIDENCE_SYSTEM, user_content)
        elif stage == 'interpreter':
            obs_labels = user_payload.get('observation_labels', [])
            theory_text = user_payload.get('theory_text', '')
            user_content = f"观察结果：\n{json.dumps(obs_labels, ensure_ascii=False, indent=2)}\n\n理论框架文献：\n{theory_text[:3000]}\n\n请构建拉康式假设，返回 JSON。"
            return self._call(INTERPRETER_SYSTEM, user_content)
        elif stage == 'critic':
            obs_labels = user_payload.get('observation_labels', [])
            hypotheses_summary = user_payload.get('hypotheses_summary', [])
            user_content = f"观察结果：\n{json.dumps(obs_labels, ensure_ascii=False, indent=2)}\n\n假设：\n{json.dumps(hypotheses_summary, ensure_ascii=False, indent=2)}\n\n请提出反例和方法论缺口，返回 JSON。"
            return self._call(CRITIC_SYSTEM, user_content)
        raise ValueError(f"UNKNOWN_STAGE: {stage}")

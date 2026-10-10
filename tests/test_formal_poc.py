"""PoC tests: formal (matheme) notation vs natural language prompts."""

import re
from hermeneut.formal import (
    FORMAL_EVIDENCE_SYSTEM,
    FORMAL_INTERPRETER_SYSTEM,
    MATHEME_ALPHABET,
    DISCOURSE_ALGEBRA,
    REGISTER_TAXONOMY,
    CONCEPT_TO_MATHEME,
    DELEUZE_ALPHABET,
    DELEUZE_OPERATIONS,
    format_formal_schema,
    get_formal_prompt,
)
from hermeneut.llm import EVIDENCE_SYSTEM, INTERPRETER_SYSTEM


def _estimate_tokens(text: str) -> float:
    cjk = len(re.findall(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", text))
    other = len(text) - cjk
    return cjk * 1.5 + other * 0.25


def test_formal_prompts_exist():
    assert len(FORMAL_EVIDENCE_SYSTEM) > 50
    assert len(FORMAL_INTERPRETER_SYSTEM) > 50
    assert "Notation:" in FORMAL_EVIDENCE_SYSTEM
    assert "Disc:" in FORMAL_INTERPRETER_SYSTEM


def test_token_comparison():
    orig_ev_tokens = _estimate_tokens(EVIDENCE_SYSTEM)
    form_ev_tokens = _estimate_tokens(FORMAL_EVIDENCE_SYSTEM)
    orig_int_tokens = _estimate_tokens(INTERPRETER_SYSTEM)
    form_int_tokens = _estimate_tokens(FORMAL_INTERPRETER_SYSTEM)

    ev_ratio = form_ev_tokens / orig_ev_tokens
    int_ratio = form_int_tokens / orig_int_tokens

    print(f"\n{'='*60}")
    print(f"EVIDENCE prompt:")
    print(f"  original:  {len(EVIDENCE_SYSTEM):5d} chars  ~ {orig_ev_tokens:6.0f} tokens")
    print(f"  formal:    {len(FORMAL_EVIDENCE_SYSTEM):5d} chars  ~ {form_ev_tokens:6.0f} tokens")
    print(f"  ratio:     {ev_ratio:.1%}")
    print(f"INTERPRETER prompt:")
    print(f"  original:  {len(INTERPRETER_SYSTEM):5d} chars  ~ {orig_int_tokens:6.0f} tokens")
    print(f"  formal:    {len(FORMAL_INTERPRETER_SYSTEM):5d} chars  ~ {form_int_tokens:6.0f} tokens")
    print(f"  ratio:     {int_ratio:.1%}")
    print(f"{'='*60}")

    assert ev_ratio < 0.85, f"Evidence formal prompt not smaller: {ev_ratio:.1%}"
    assert int_ratio < 0.85, f"Interpreter formal prompt not smaller: {int_ratio:.1%}"


def test_output_schema_compatible():
    assert '"observations"' in FORMAL_EVIDENCE_SYSTEM
    assert '"id"' in FORMAL_EVIDENCE_SYSTEM
    assert '"label"' in FORMAL_EVIDENCE_SYSTEM
    assert '"evidence_span_ids"' in FORMAL_EVIDENCE_SYSTEM
    assert '"register"' in FORMAL_EVIDENCE_SYSTEM
    assert '"register_markers"' in FORMAL_EVIDENCE_SYSTEM

    assert '"hypotheses"' in FORMAL_INTERPRETER_SYSTEM
    assert '"concept_ids"' in FORMAL_INTERPRETER_SYSTEM
    assert '"support_ids"' in FORMAL_INTERPRETER_SYSTEM
    assert '"alternatives"' in FORMAL_INTERPRETER_SYSTEM
    assert '"counterexamples"' in FORMAL_INTERPRETER_SYSTEM
    assert '"discourse_type"' in FORMAL_INTERPRETER_SYSTEM
    assert '"matheme_ids"' in FORMAL_INTERPRETER_SYSTEM
    assert '"points_de_capiton"' in FORMAL_INTERPRETER_SYSTEM
    assert '"desire_residual"' in FORMAL_INTERPRETER_SYSTEM


def test_matheme_alphabet_complete():
    all_symbols = set()
    for entries in MATHEME_ALPHABET.values():
        all_symbols.update(entries.keys())
    for info in DISCOURSE_ALGEBRA.values():
        all_symbols.add(info["symbol"])
    for entries in DELEUZE_ALPHABET.values():
        all_symbols.update(entries.keys())
    all_symbols.update(DELEUZE_OPERATIONS.keys())

    for concept, mathemes in CONCEPT_TO_MATHEME.items():
        for m in mathemes:
            clean = re.sub(r"[→∩◇/(),]+", "", m)
            if clean:
                found = any(clean in s or s in clean for s in all_symbols)
                assert found, f"Concept '{concept}' references unknown matheme '{m}'"


def test_discourse_algebra_structure():
    expected_types = {"master", "university", "hysteric", "analyst"}
    assert set(DISCOURSE_ALGEBRA.keys()) == expected_types

    for dtype, info in DISCOURSE_ALGEBRA.items():
        assert "symbol" in info
        assert "structure" in info
        for pos in ("agent", "other", "truth", "product"):
            assert pos in info, f"{dtype} missing position {pos}"
        positions = {info["agent"], info["other"], info["truth"], info["product"]}
        assert len(positions) == 4, f"{dtype} has duplicate positions"


def test_register_taxonomy_complete():
    assert set(REGISTER_TAXONOMY.keys()) == {"S", "I", "R"}
    for reg, info in REGISTER_TAXONOMY.items():
        assert "name" in info
        assert "domain" in info
        assert "markers" in info
        assert len(info["markers"]) >= 3
        assert "topology" in info


def test_get_formal_prompt_dispatch():
    assert get_formal_prompt("evidence") is FORMAL_EVIDENCE_SYSTEM
    assert get_formal_prompt("interpreter") is FORMAL_INTERPRETER_SYSTEM
    assert get_formal_prompt("critic") is not None
    assert get_formal_prompt("deleuze_evidence") is not None
    assert get_formal_prompt("synthesis") is not None
    assert get_formal_prompt("profile_inference") is not None
    assert get_formal_prompt("structural") is not None
    try:
        get_formal_prompt("nonexistent_stage")
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_formal_schema_generation():
    ev_schema = format_formal_schema("evidence")
    assert "MATHEME ALPHABET" in ev_schema
    assert "RSI REGISTERS" in ev_schema
    assert "EVIDENCE SCHEMA" in ev_schema

    int_schema = format_formal_schema("interpreter")
    assert "FOUR DISCOURSES" in int_schema
    assert "INTERPRETER SCHEMA" in int_schema


def test_discourse_type_mapping():
    orig_types = {"master", "university", "hysteric", "analyst"}
    formal_symbols = {DISCOURSE_ALGEBRA[d]["symbol"] for d in orig_types}
    assert formal_symbols == {"D_m", "D_u", "D_h", "D_a"}

    for dtype, info in DISCOURSE_ALGEBRA.items():
        sym = info["symbol"].replace("_", "")
        assert sym in FORMAL_INTERPRETER_SYSTEM or dtype in FORMAL_INTERPRETER_SYSTEM


def test_lacan_perspective_uses_formal_prompts():
    from hermeneut.models import PerspectiveConfig
    from hermeneut.perspectives.prompts import build_perspective_prompts
    from hermeneut.formal.prompts import FORMAL_EVIDENCE_SYSTEM, FORMAL_INTERPRETER_SYSTEM

    lacan_config = PerspectiveConfig(
        id="lacan", name="Lacanian Psychoanalytic",
        concept_inventory=["signifier"], blind_spots=[],
        vocabulary={}, evidence_prompt_variant=None,
        interpreter_prompt_variant=None, critique_prompt_variant=None,
    )

    ev_prompt = build_perspective_prompts(lacan_config, "evidence")
    assert FORMAL_EVIDENCE_SYSTEM in ev_prompt
    assert "Notation:" in ev_prompt

    int_prompt = build_perspective_prompts(lacan_config, "interpreter")
    assert FORMAL_INTERPRETER_SYSTEM in int_prompt
    assert "Disc:" in int_prompt


def test_deleuze_perspective_uses_formal():
    from hermeneut.models import PerspectiveConfig
    from hermeneut.perspectives.prompts import build_perspective_prompts
    from hermeneut.formal.prompts import FORMAL_DELEUZE_EVIDENCE

    deleuze_config = PerspectiveConfig(
        id="deleuze", name="Deleuzian Schizoanalysis",
        concept_inventory=["assemblage"], blind_spots=[],
        vocabulary={},
        evidence_prompt_variant="CUSTOM_DELEUZE_EVIDENCE",
        interpreter_prompt_variant="CUSTOM_DELEUZE_INTERPRETER",
        critique_prompt_variant=None,
    )

    ev_prompt = build_perspective_prompts(deleuze_config, "evidence")
    assert FORMAL_DELEUZE_EVIDENCE in ev_prompt
    assert "Notation:" in ev_prompt


def test_lacan_critic_uses_formal():
    from hermeneut.models import PerspectiveConfig
    from hermeneut.perspectives.prompts import build_perspective_prompts
    from hermeneut.formal.prompts import FORMAL_CRITIC_SYSTEM

    lacan_config = PerspectiveConfig(
        id="lacan", name="Lacanian Psychoanalytic",
        concept_inventory=["signifier"], blind_spots=[],
        vocabulary={}, evidence_prompt_variant=None,
        interpreter_prompt_variant=None, critique_prompt_variant=None,
    )

    critic_prompt = build_perspective_prompts(lacan_config, "critic")
    assert FORMAL_CRITIC_SYSTEM in critic_prompt
    assert "Strict reviewer" in critic_prompt


def test_all_stages_token_comparison():
    from hermeneut.llm import (
        EVIDENCE_SYSTEM, INTERPRETER_SYSTEM, CRITIC_SYSTEM,
        CROSS_CRITIQUE_SYSTEM, SYNTHESIS_SYSTEM,
    )
    from hermeneut.behavioral.inference import PROFILE_INFERENCE_SYSTEM, STRUCTURAL_SYSTEM
    from hermeneut.formal import (
        FORMAL_CRITIC_SYSTEM as FC,
        FORMAL_CROSS_CRITIQUE_SYSTEM as FCC,
        FORMAL_SYNTHESIS_SYSTEM as FS,
        FORMAL_PROFILE_INFERENCE as FPI,
        FORMAL_STRUCTURAL as FST,
    )

    pairs = [
        ("evidence (Lacan)", EVIDENCE_SYSTEM, FORMAL_EVIDENCE_SYSTEM),
        ("interpreter (Lacan)", INTERPRETER_SYSTEM, FORMAL_INTERPRETER_SYSTEM),
        ("critic (Lacan)", CRITIC_SYSTEM, FC),
        ("cross_critique", CROSS_CRITIQUE_SYSTEM, FCC),
        ("synthesis", SYNTHESIS_SYSTEM, FS),
        ("profile_inference", PROFILE_INFERENCE_SYSTEM, FPI),
        ("structural", STRUCTURAL_SYSTEM, FST),
    ]

    print(f"\n{'='*70}")
    print(f"{'Stage':<25} {'Original':>10} {'Formal':>10} {'Ratio':>8}")
    print(f"{'-'*70}")
    for name, orig, formal in pairs:
        orig_t = _estimate_tokens(orig)
        form_t = _estimate_tokens(formal)
        ratio = form_t / orig_t if orig_t > 0 else 0
        print(f"{name:<25} {orig_t:>8.0f}t {form_t:>8.0f}t {ratio:>7.1%}")
    print(f"{'='*70}")

    for name, orig, formal in pairs:
        orig_t = _estimate_tokens(orig)
        form_t = _estimate_tokens(formal)
        ratio = form_t / orig_t if orig_t > 0 else 0
        assert ratio < 0.85, f"{name}: formal not smaller ({ratio:.1%})"

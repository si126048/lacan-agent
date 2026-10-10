"""Formal notation module — matheme-based internal representation."""

from .mathemes import (
    MATHEME_ALPHABET,
    DISCOURSE_ALGEBRA,
    REGISTER_TAXONOMY,
    CONCEPT_TO_MATHEME,
    DELEUZE_ALPHABET,
    DELEUZE_REGISTER_TAXONOMY,
    DELEUZE_OPERATIONS,
    format_alphabet,
    format_discourse_table,
    format_register_table,
    format_formal_schema,
    format_deleuze_alphabet,
    format_deleuze_register,
)
from .prompts import (
    FORMAL_EVIDENCE_SYSTEM,
    FORMAL_INTERPRETER_SYSTEM,
    FORMAL_CRITIC_SYSTEM,
    FORMAL_CROSS_CRITIQUE_SYSTEM,
    FORMAL_SYNTHESIS_SYSTEM,
    FORMAL_DELEUZE_EVIDENCE,
    FORMAL_DELEUZE_INTERPRETER,
    FORMAL_DELEUZE_CRITIQUE,
    FORMAL_PROFILE_INFERENCE,
    FORMAL_STRUCTURAL,
    get_formal_prompt,
)

__all__ = [
    "MATHEME_ALPHABET", "DISCOURSE_ALGEBRA", "REGISTER_TAXONOMY", "CONCEPT_TO_MATHEME",
    "DELEUZE_ALPHABET", "DELEUZE_REGISTER_TAXONOMY", "DELEUZE_OPERATIONS",
    "format_alphabet", "format_discourse_table", "format_register_table",
    "format_formal_schema", "format_deleuze_alphabet", "format_deleuze_register",
    "FORMAL_EVIDENCE_SYSTEM", "FORMAL_INTERPRETER_SYSTEM", "FORMAL_CRITIC_SYSTEM",
    "FORMAL_CROSS_CRITIQUE_SYSTEM", "FORMAL_SYNTHESIS_SYSTEM",
    "FORMAL_DELEUZE_EVIDENCE", "FORMAL_DELEUZE_INTERPRETER", "FORMAL_DELEUZE_CRITIQUE",
    "FORMAL_PROFILE_INFERENCE", "FORMAL_STRUCTURAL",
    "get_formal_prompt",
]

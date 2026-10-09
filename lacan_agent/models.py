from __future__ import annotations
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

class RunState(StrEnum):
    CREATED='CREATED'; INGESTED='INGESTED'; OBSERVED='OBSERVED'; INTERPRETED='INTERPRETED'; CRITIQUED='CRITIQUED'; NEEDS_HUMAN_REVIEW='NEEDS_HUMAN_REVIEW'; APPROVED='APPROVED'; COMPILED='COMPILED'; FAILED='FAILED'; CANCELLED='CANCELLED'; REVISION_REQUIRED='REVISION_REQUIRED'
class ReviewStatus(StrEnum):
    PROVISIONAL='provisional'; APPROVED='approved'; REJECTED='rejected'; NEEDS_REVISION='needs_revision'
class ReviewDecision(StrEnum):
    APPROVE='approve'; REJECT='reject'; REVISE='revise'
class ConsentScope(BaseModel):
    research_analysis: bool = False
    human_review: bool = False
    generation: bool = False
    training: bool = False
    public_display: bool = False
    expires_at: str | None = None
    withdrawn_at: str | None = None
class Project(BaseModel):
    id: str
    policy_version: str = '1.0'
    owner_id: str = 'local-user'
class Participant(BaseModel):
    id: str
    project_id: str
    pseudonym: str
    consent_scope: ConsentScope
    withdrawn_at: str | None = None
class SourceDocument(BaseModel):
    id: str
    project_id: str
    participant_id: str | None = None
    origin: str
    type: str
    checksum: str
    text: str
    consent_scope: ConsentScope = Field(default_factory=ConsentScope)
    metadata: dict[str, Any] = Field(default_factory=dict)
class EvidenceSpan(BaseModel):
    id: str; document_id: str; char_start: int; char_end: int; excerpt: str; excerpt_hash: str

    @model_validator(mode='after')
    def _validate_offsets(self):
        if self.char_start < 0 or self.char_end <= self.char_start:
            raise ValueError('invalid char offsets')
        if not self.excerpt.strip():
            raise ValueError('empty excerpt')
        return self
class ConceptCard(BaseModel):
    id: str; canonical_name: str; definition: str; theoretical_period: str = 'unspecified'; source_span_ids: list[str] = []; review_status: str = 'draft'
class Observation(BaseModel):
    id: str; label: str; evidence_span_ids: list[str]
class Hypothesis(BaseModel):
    id: str; concept_ids: list[str]; support_ids: list[str]; alternatives: list[str]; counterexamples: list[str] = []; status: ReviewStatus = ReviewStatus.PROVISIONAL; theory_reference_ids: list[str] = []
class GraphNode(BaseModel):
    id: str; type: str; label: str; source_ids: list[str] = []; status: str = 'provisional'
class GraphEdge(BaseModel):
    id: str; source: str; target: str; type: str; evidence_span_ids: list[str]; weight: float | None = None
class NarrativeOperator(BaseModel):
    id: str; operator: str; source_finding_ids: list[str]; allowed: bool = False; use_cases: list[str] = []; counterexamples: list[str] = []; approval_state: str = 'provisional'
class AnalysisPacket(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    run_id: str; participant_id: str; state: RunState; observations: list[Observation] = []; hypotheses: list[Hypothesis] = []; narrative_operators: list[NarrativeOperator] = []; errors: list[str] = []
class AnalysisRun(BaseModel):
    id: str; project_id: str; participant_id: str; source_ids: list[str]; state: RunState; idempotency_key: str; packet: AnalysisPacket | None = None; audit: list[dict[str, Any]] = []
class ReviewRequest(BaseModel):
    reviewer_id: str; decision: ReviewDecision; reason: str = ''
class ErrorBody(BaseModel):
    code: str; message: str; request_id: str
class ErrorResponse(BaseModel):
    error: ErrorBody

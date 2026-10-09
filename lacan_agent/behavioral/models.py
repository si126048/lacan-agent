"""Output models for behavioral profiling."""

from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


SOURCE_TYPES = {'chat', 'interview', 'writing', 'observation'}
STRUCTURAL_DIMENSIONS = {
    'discourse_position', 'big_other', 'demand_desire', 'repeated_signifier',
    'capiton_point', 'fantasy_structure', 'symptom_repetition', 'jouissance',
    'four_discourse', 'rsi_relation', 'narrative_conflict',
}
CLAIM_STATUSES = {'candidate', 'approved', 'rejected', 'needs_revision'}


class BehavioralProfile(BaseModel):
    """Behavioral style profile for one participant."""

    pseudonym: str

    total_messages: int = 0
    avg_msg_length: float = 0.0
    median_msg_length: float = 0.0
    short_msg_ratio: float = 0.0
    media_ratio: float = 0.0
    emoji_density: float = 0.0

    top_bigrams: list[tuple[str, int]] = Field(default_factory=list)
    signature_phrases: list[str] = Field(default_factory=list)
    unique_expressions: list[str] = Field(default_factory=list)

    top_punctuation: dict[str, float] = Field(default_factory=dict)
    question_ratio: float = 0.0
    exclamation_ratio: float = 0.0
    repeated_punct_ratio: float = 0.0

    opening_patterns: list[str] = Field(default_factory=list)
    closing_patterns: list[str] = Field(default_factory=list)
    bracket_insertions: list[str] = Field(default_factory=list)
    modal_particles: dict[str, int] = Field(default_factory=dict)
    onomatopoeia: list[str] = Field(default_factory=list)

    mention_targets: dict[str, int] = Field(default_factory=dict)
    quote_reply_ratio: float = 0.0
    pure_media_ratio: float = 0.0

    peak_hours: list[int] = Field(default_factory=list)
    burst_ratio: float = 0.0

    style_tags: list[str] = Field(default_factory=list)


class StructuralSummary(BaseModel):
    """Summary from lacan-agent structural analysis."""

    discourse_trajectory: list[str] = Field(default_factory=list)
    dominant_discourse: str = ""
    capiton_signifiers: list[str] = Field(default_factory=list)
    desire_direction: str = ""
    hallucination_risk: str = ""


class DistillationCard(BaseModel):
    """Full distillation card combining behavioral + structural layers."""

    pseudonym: str
    behavioral: dict = Field(default_factory=dict)
    structural: StructuralSummary | None = None


class ConsentPolicy(BaseModel):
    profile_analysis: bool = False
    agent_simulation: bool = False
    story_generation: bool = False
    public_export: bool = False
    expires_at: str | None = None
    withdrawn_at: str | None = None

    def is_active(self) -> bool:
        if self.withdrawn_at or not self.profile_analysis:
            return False
        if not self.expires_at:
            return True
        try:
            value = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value > datetime.now(timezone.utc)
        except ValueError:
            return False


class SourceManifest(BaseModel):
    source_id: str
    path: str
    checksum: str
    message_count: int
    time_range: tuple[str, str] | None = None
    format: str = 'plain'


class MaterialSource(BaseModel):
    """A consented input source used for multi-source subject analysis."""

    source_id: str
    participant_id: str
    source_type: str
    path: str
    checksum: str
    context: str | None = None
    collected_at: str | None = None
    consent_scope: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)

    @field_validator('source_type')
    @classmethod
    def valid_source_type(cls, value: str) -> str:
        if value not in SOURCE_TYPES:
            raise ValueError(f'INVALID_SOURCE_TYPE:{value}')
        return value


class EvidenceSpan(BaseModel):
    span_id: str
    source_id: str
    participant_id: str
    text: str
    start_offset: int = 0
    end_offset: int = 0
    speaker: str | None = None
    scene: str | None = None
    timestamp: str | None = None
    message_id: str | None = None
    question_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class StructuralClaim(BaseModel):
    claim_id: str
    dimension: str
    text: str
    evidence_span_ids: list[str] = Field(default_factory=list)
    source_types: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    alternatives: list[str] = Field(default_factory=list)
    status: str = 'candidate'
    source: str = 'qwen'
    reviewer_id: str | None = None
    review_reason: str | None = None
    created_at: str | None = None

    @field_validator('source_types')
    @classmethod
    def valid_source_types(cls, values: list[str]) -> list[str]:
        invalid = set(values) - SOURCE_TYPES
        if invalid:
            raise ValueError(f'INVALID_SOURCE_TYPE:{sorted(invalid)[0]}')
        return values

    @field_validator('dimension')
    @classmethod
    def valid_dimension(cls, value: str) -> str:
        if value not in STRUCTURAL_DIMENSIONS:
            raise ValueError(f'INVALID_STRUCTURAL_DIMENSION:{value}')
        return value

    @field_validator('status')
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in CLAIM_STATUSES:
            raise ValueError(f'INVALID_CLAIM_STATUS:{value}')
        return value

    @field_validator('confidence')
    @classmethod
    def valid_structural_confidence(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError('confidence must be in [0, 1]')
        return value


class CrossSourceFinding(BaseModel):
    finding_id: str
    type: str
    claim_ids: list[str] = Field(default_factory=list)
    evidence_span_ids: list[str] = Field(default_factory=list)
    text: str
    confidence: float = 0.0
    status: str = 'candidate'

    @field_validator('type')
    @classmethod
    def valid_finding_type(cls, value: str) -> str:
        if value not in {'consistent', 'context_shift', 'contradiction', 'insufficient_evidence'}:
            raise ValueError(f'INVALID_CROSS_SOURCE_TYPE:{value}')
        return value

    @field_validator('confidence')
    @classmethod
    def valid_finding_confidence(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError('confidence must be in [0, 1]')
        return value


class EvidenceClaim(BaseModel):
    id: str
    text: str
    evidence_span_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    alternatives: list[str] = Field(default_factory=list)
    status: str = 'candidate'
    source: str = 'qwen'

    @field_validator('confidence')
    @classmethod
    def valid_confidence(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError('confidence must be in [0, 1]')
        return value


class ProfileArtifact(BaseModel):
    profile_id: str
    participant_id: str
    pseudonym: str
    schema_version: str = '1.0'
    created_at: str
    source_manifest: list[SourceManifest] = Field(default_factory=list)
    consent: ConsentPolicy
    observed_style: dict = Field(default_factory=dict)
    source_profiles: dict[str, dict] = Field(default_factory=dict)
    structural_claims: list[StructuralClaim] = Field(default_factory=list)
    cross_source_findings: list[CrossSourceFinding] = Field(default_factory=list)
    topics: list[EvidenceClaim] = Field(default_factory=list)
    episodes: list[EvidenceClaim] = Field(default_factory=list)
    relationships: list[EvidenceClaim] = Field(default_factory=list)
    inferred_traits: list[EvidenceClaim] = Field(default_factory=list)
    generation_policy: dict = Field(default_factory=dict)
    quality: dict = Field(default_factory=dict)
    review_state: str = 'candidate'

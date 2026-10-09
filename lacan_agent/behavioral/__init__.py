"""Behavioral profiling module for agent distillation."""

from .profiler import BehavioralProfiler
from .models import (
    ProfileArtifact, EvidenceClaim, ConsentPolicy, MaterialSource, EvidenceSpan,
    StructuralClaim, CrossSourceFinding,
)
from .subject import SubjectProfiler

__all__ = [
    "BehavioralProfiler", "SubjectProfiler", "ProfileArtifact", "EvidenceClaim",
    "ConsentPolicy", "MaterialSource", "EvidenceSpan", "StructuralClaim",
    "CrossSourceFinding",
]

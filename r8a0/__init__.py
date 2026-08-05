"""R8A0 bounded vertical slice."""

from .memory import AdmissionRequest, GovernedMemoryStore, MemoryClass
from .recovery import CheckpointState, recover, terminate, write_checkpoint
from .temporal import (
    CURRENT_TIME,
    REQUIRED_DIMENSIONS,
    OrientationGate,
    OrientationState,
    TimeEvidence,
    current_evidence,
    evidence_from_mapping,
)

__all__ = [
    "AdmissionRequest",
    "CheckpointState",
    "CURRENT_TIME",
    "GovernedMemoryStore",
    "MemoryClass",
    "OrientationGate",
    "OrientationState",
    "REQUIRED_DIMENSIONS",
    "TimeEvidence",
    "current_evidence",
    "evidence_from_mapping",
    "recover",
    "terminate",
    "write_checkpoint",
]

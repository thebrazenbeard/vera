"""Canonical V.E.R.A. temporal enforcement API.

The single-precision implementation remains available as
``protocol.temporal_enforcement`` for compatibility. Package-level imports use
the strict role-specific prior-anchor gate.
"""

from .temporal_enforcement import (
    AnchorStatus,
    CoordinationEvent,
    ElapsedResult,
    ElapsedStatus,
    EvidenceSystem,
    EvidenceVerifier,
    ExternalEvidence,
    HandoffEvidence,
    PostflightRequest,
    PreflightDecision,
    PreflightRequest,
    RequiredHandoff,
    ResolvedScope,
    ScopeStability,
    TemporalAnchor,
    TemporalPrecision,
    TurnTemporalResult,
    Workstream,
    anchor_subject_hash,
    canonical_subject_hash,
    coordination_inbox_subject_hash,
    current_time_subject_hash,
    resolve_scope,
    scope_subject_hash,
)
from .temporal_role_precision import (
    RoleTemporalPoint,
    elapsed_between,
    role_temporal_point_subject_hash,
    run_postflight,
    run_preflight,
)

__all__ = [name for name in globals() if not name.startswith("_")]

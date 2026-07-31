"""V.E.R.A. coordination bus v1 public interface."""

from .contracts import (
    ACTOR_WORKSTREAM_ALIASES, ALL_PERMISSIONS, CANONICAL_MEMORY_ELIGIBLE,
    EVENT_STATUS_PAIRS, EVENT_TYPES, INSTRUCTION_TRUST,
    LEGACY_STORED_ADDRESSES, OBSOLETE_WORKSTREAMS, RECORD_CLASS, STATUSES,
    WORKSTREAMS, CoordinationEvent, CoordinationEventDraft,
    CoordinationReceipt, CoordinationResult, PERMISSION_ACKNOWLEDGE,
    PERMISSION_DECIDE, PERMISSION_POST, PERMISSION_READ_ANY,
    PERMISSION_READ_SELF, PERMISSION_RESOLVE, PERMISSION_REVIEW,
    PERMISSION_STATUS, RepositoryConflict, canonical_hash, canonicalize,
    classify_stored_address,
)
from .in_memory import InMemoryCoordinationRepository
from .supabase_sql import (
    GET_EVENT_SQL, INSERT_EVENT_SQL, LIST_THREAD_SQL, LIVE_SCHEMA_SNAPSHOT_V1,
    READ_INBOX_SQL, SqlExecutor, SupabaseSqlRepository,
)
from . import temporal as _temporal_module
from .temporal import (
    TemporalCoordinationReceipt,
    TemporalCoordinationResult,
    TemporalEvidence,
)

# The temporal mechanics class is internal. Preserve its historical import name
# only long enough for the verifier-bound facade to subclass it. The package
# still exports exactly one public CoordinationBus below.
_temporal_module.CoordinationBus = _temporal_module._TemporalCoordinationCore

from .verified_temporal import (
    EVIDENCE_ENVELOPE_SCHEMA,
    HmacTemporalEvidenceAuthority,
    ReceiptTimeProvider,
    TemporalEvidenceEnvelope,
    TemporalEvidenceInput,
    TemporalEvidenceVerifier,
    acknowledgement_subject,
    entry_checkpoint_subject,
    exit_checkpoint_subject,
    receipt_subject,
)
from .strict_authority import (
    ActorContext,
    CoordinationBus,
    DECISION_AUTHORITY_ENVELOPE_SCHEMA,
    DecisionAuthorityEnvelope,
    DecisionAuthorityVerifier,
    HmacDecisionAuthority,
    decision_subject,
)

__all__ = [name for name in globals() if not name.startswith("_")]

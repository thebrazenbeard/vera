"""Fail-closed temporal enforcement for V.E.R.A.

The kernel treats the language model as an intelligent but untrusted component.
A turn is ANCHORED only when exposed external evidence proves the required
preflight and postflight operations. Model claims never certify time, retrieval,
storage, delivery, continuity, or elapsed duration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from hashlib import sha256
import json
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5


class AnchorStatus(str, Enum):
    ANCHORED = "ANCHORED"
    UNANCHORED = "UNANCHORED"


class TemporalPrecision(str, Enum):
    EXACT = "EXACT"
    BOUNDED = "BOUNDED"
    APPROXIMATE = "APPROXIMATE"
    UNKNOWN = "UNKNOWN"


class ElapsedStatus(str, Enum):
    EXACT = "EXACT"
    BOUNDED = "BOUNDED"
    APPROXIMATE = "APPROXIMATE"
    UNAVAILABLE = "UNAVAILABLE"
    CONFLICTED = "CONFLICTED"


class ScopeStability(str, Enum):
    STABLE = "STABLE"
    EPHEMERAL = "EPHEMERAL"


class EvidenceSystem(str, Enum):
    HOST = "HOST"
    SUPABASE = "SUPABASE"
    BASIC_MEMORY = "BASIC_MEMORY"
    GITHUB = "GITHUB"
    MODEL = "MODEL"
    OTHER = "OTHER"


class Workstream(str, Enum):
    TIME = "workstream/time"
    MEMORY = "workstream/memory"
    INITIATIVES = "workstream/initiatives"
    INTEGRATION = "workstream/integration"


TRUSTED_NOW_SYSTEMS = frozenset({EvidenceSystem.HOST, EvidenceSystem.SUPABASE})
IMMUTABLE_EVIDENCE_SYSTEMS = frozenset({EvidenceSystem.SUPABASE, EvidenceSystem.GITHUB})


def _new_uuid() -> UUID:
    """Private UUID source so callers cannot select ephemeral identities."""

    return uuid4()


def _as_aware_datetime(value: datetime | str | None, field_name: str) -> datetime:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            value = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO-8601 datetime") from exc
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime or ISO-8601 string")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone offset")
    return value.astimezone(timezone.utc)


def _nonblank(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} may not have surrounding whitespace")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} may not contain control characters")
    return value


@dataclass(frozen=True)
class ExternalEvidence:
    system: EvidenceSystem
    operation: str
    confirmed: bool
    reference_id: str | None
    observed_at: datetime | str | None
    immutable: bool = False
    payload_hash: str | None = None

    def validate(self) -> None:
        _nonblank(self.operation, "operation")
        if self.system is EvidenceSystem.MODEL and self.confirmed:
            raise ValueError("model output cannot be confirmed external evidence")
        if self.confirmed:
            _nonblank(self.reference_id or "", "reference_id")
            _as_aware_datetime(self.observed_at, "observed_at")
        elif self.reference_id is not None and not self.reference_id.strip():
            raise ValueError("reference_id may not be blank")
        if self.immutable and self.system not in IMMUTABLE_EVIDENCE_SYSTEMS:
            raise ValueError("immutable evidence must come from an immutable-capable system")
        if self.payload_hash is not None:
            if len(self.payload_hash) != 64 or any(c not in "0123456789abcdef" for c in self.payload_hash):
                raise ValueError("payload_hash must be a lowercase SHA-256 digest")


@dataclass(frozen=True)
class ResolvedScope:
    project_id: str
    conversation_id: str
    branch_id: str
    session_id: str
    scope_instance_id: str
    checkpoint_id: str | None
    stability: ScopeStability
    provider_conversation_id: str | None
    provider_branch_id: str | None
    generated_at: datetime
    limitations: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in (
            "project_id",
            "conversation_id",
            "branch_id",
            "session_id",
            "scope_instance_id",
        ):
            _nonblank(getattr(self, name), name)
        _as_aware_datetime(self.generated_at, "generated_at")
        identities = [
            self.conversation_id,
            self.branch_id,
            self.session_id,
            self.scope_instance_id,
        ]
        if self.checkpoint_id is not None:
            _nonblank(self.checkpoint_id, "checkpoint_id")
            identities.append(self.checkpoint_id)
        if len(set(identities)) != len(identities):
            raise ValueError("conversation, branch, session, scope, and checkpoint identities must be distinct")
        if self.stability is ScopeStability.STABLE:
            _nonblank(self.provider_conversation_id or "", "provider_conversation_id")
            _nonblank(self.provider_branch_id or "", "provider_branch_id")
        else:
            if self.provider_conversation_id is not None or self.provider_branch_id is not None:
                raise ValueError("ephemeral scope may not claim provider identifiers")


def resolve_scope(
    *,
    project_id: str,
    observed_at: datetime | str,
    provider_conversation_id: str | None = None,
    provider_branch_id: str | None = None,
    checkpoint_id: str | None = None,
) -> ResolvedScope:
    """Resolve stable host scope or issue fresh ephemeral scope internally."""

    project_id = _nonblank(project_id, "project_id")
    generated_at = _as_aware_datetime(observed_at, "observed_at")
    session_id = f"session:{_new_uuid()}"

    if provider_conversation_id is not None and provider_branch_id is not None:
        provider_conversation_id = _nonblank(provider_conversation_id, "provider_conversation_id")
        provider_branch_id = _nonblank(provider_branch_id, "provider_branch_id")
        conversation_id = f"conversation:{provider_conversation_id}"
        branch_id = f"branch:{provider_branch_id}"
        stable_key = f"{project_id}|{provider_conversation_id}|{provider_branch_id}"
        scope_instance_id = f"scope:{uuid5(NAMESPACE_URL, stable_key)}"
        stability = ScopeStability.STABLE
        limitations: tuple[str, ...] = ()
    elif provider_conversation_id is None and provider_branch_id is None:
        conversation_id = f"conversation:ephemeral:{_new_uuid()}"
        branch_id = f"branch:ephemeral:{_new_uuid()}"
        scope_instance_id = f"scope:ephemeral:{_new_uuid()}"
        stability = ScopeStability.EPHEMERAL
        limitations = (
            "Host did not expose stable conversation or branch identifiers.",
            "This scope supports only the current execution and proves no durable recognition.",
        )
    else:
        raise ValueError("provider conversation and branch identifiers must be supplied together")

    scope = ResolvedScope(
        project_id=project_id,
        conversation_id=conversation_id,
        branch_id=branch_id,
        session_id=session_id,
        scope_instance_id=scope_instance_id,
        checkpoint_id=checkpoint_id,
        stability=stability,
        provider_conversation_id=provider_conversation_id,
        provider_branch_id=provider_branch_id,
        generated_at=generated_at,
        limitations=limitations,
    )
    scope.validate()
    return scope


@dataclass(frozen=True)
class TemporalPoint:
    precision: TemporalPrecision
    source: ExternalEvidence
    scope_instance_id: str
    event_time: datetime | str | None = None
    state_time: datetime | str | None = None
    record_time: datetime | str | None = None
    retrieval_time: datetime | str | None = None
    lower_bound: datetime | str | None = None
    upper_bound: datetime | str | None = None

    def validate(self) -> None:
        self.source.validate()
        if not self.source.confirmed:
            raise ValueError("temporal point requires confirmed external evidence")
        _nonblank(self.scope_instance_id, "scope_instance_id")

        event = _as_aware_datetime(self.event_time, "event_time") if self.event_time is not None else None
        lower = _as_aware_datetime(self.lower_bound, "lower_bound") if self.lower_bound is not None else None
        upper = _as_aware_datetime(self.upper_bound, "upper_bound") if self.upper_bound is not None else None
        for name, value in (
            ("state_time", self.state_time),
            ("record_time", self.record_time),
            ("retrieval_time", self.retrieval_time),
        ):
            if value is not None:
                _as_aware_datetime(value, name)

        if self.precision is TemporalPrecision.EXACT:
            if event is None or lower is not None or upper is not None:
                raise ValueError("EXACT requires event_time and forbids bounds")
        elif self.precision is TemporalPrecision.BOUNDED:
            if event is None or lower is None or upper is None:
                raise ValueError("BOUNDED requires event_time and both inclusive bounds")
            if lower > upper:
                raise ValueError("lower_bound may not exceed upper_bound")
            if not lower <= event <= upper:
                raise ValueError("event_time must fall inside inclusive bounds")
        elif self.precision is TemporalPrecision.APPROXIMATE:
            if event is None or lower is not None or upper is not None:
                raise ValueError("APPROXIMATE requires event_time and forbids hard bounds")
        elif self.precision is TemporalPrecision.UNKNOWN:
            if event is not None or lower is not None or upper is not None:
                raise ValueError("UNKNOWN forbids event_time and bounds")

    @property
    def best_time(self) -> datetime | None:
        if self.event_time is None:
            return None
        return _as_aware_datetime(self.event_time, "event_time")

    def interval(self) -> tuple[datetime, datetime] | None:
        self.validate()
        if self.precision is TemporalPrecision.UNKNOWN:
            return None
        if self.precision is TemporalPrecision.BOUNDED:
            return (
                _as_aware_datetime(self.lower_bound, "lower_bound"),
                _as_aware_datetime(self.upper_bound, "upper_bound"),
            )
        if self.precision is TemporalPrecision.EXACT:
            best = self.best_time
            assert best is not None
            return best, best
        return None


@dataclass(frozen=True)
class TemporalAnchor:
    anchor_id: str
    scope_instance_id: str
    status: AnchorStatus
    point: TemporalPoint
    workstream: Workstream = Workstream.TIME

    def validate(self) -> None:
        _nonblank(self.anchor_id, "anchor_id")
        _nonblank(self.scope_instance_id, "scope_instance_id")
        self.point.validate()
        if self.scope_instance_id != self.point.scope_instance_id:
            raise ValueError("anchor and temporal point scope must match")
        if self.status is not AnchorStatus.ANCHORED:
            raise ValueError("prior anchors must be ANCHORED")


@dataclass(frozen=True)
class CoordinationEvent:
    event_id: str
    event_sequence: int
    thread_key: str
    source_workstream: Workstream
    target_workstream: Workstream | None
    event_type: str
    status: str
    record_time: datetime | str
    acknowledges_event_id: str | None = None

    def validate(self) -> None:
        _nonblank(self.event_id, "event_id")
        if self.event_sequence <= 0:
            raise ValueError("event_sequence must be positive")
        _nonblank(self.thread_key, "thread_key")
        _nonblank(self.event_type, "event_type")
        _nonblank(self.status, "status")
        _as_aware_datetime(self.record_time, "record_time")
        if self.acknowledges_event_id is not None:
            _nonblank(self.acknowledges_event_id, "acknowledges_event_id")


@dataclass(frozen=True)
class PreflightRequest:
    workstream: Workstream
    now: datetime | str | None
    now_evidence: ExternalEvidence | None
    scope: ResolvedScope | None
    coordination_inbox_checked: bool
    coordination_read_evidence: ExternalEvidence | None
    coordination_events: tuple[CoordinationEvent, ...] = ()
    retrieval_required: bool = False
    retrieval_evidence: ExternalEvidence | None = None
    prior_anchor_required: bool = False
    prior_anchor: TemporalAnchor | None = None
    maximum_anchor_age: timedelta = timedelta(days=30)
    immutable_proof_required: bool = False
    model_claims: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreflightDecision:
    status: AnchorStatus
    reasons: tuple[str, ...]
    trusted_now: datetime | None
    scope: ResolvedScope | None
    addressed_events: tuple[CoordinationEvent, ...]
    prior_anchor: TemporalAnchor | None
    limitations: tuple[str, ...]

    @property
    def may_reason_temporally(self) -> bool:
        return self.status is AnchorStatus.ANCHORED


@dataclass(frozen=True)
class HandoffEvidence:
    target_workstream: Workstream
    write_evidence: ExternalEvidence


@dataclass(frozen=True)
class PostflightRequest:
    preflight: PreflightDecision
    material_transition: bool
    temporal_write_evidence: ExternalEvidence | None = None
    required_handoff_targets: tuple[Workstream, ...] = ()
    handoff_evidence: tuple[HandoffEvidence, ...] = ()
    model_claims: tuple[str, ...] = ()


@dataclass(frozen=True)
class TurnTemporalResult:
    status: AnchorStatus
    reasons: tuple[str, ...]
    temporal_reference_id: str | None
    handoff_reference_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class ElapsedResult:
    status: ElapsedStatus
    best_seconds: float | None
    lower_seconds: float | None
    upper_seconds: float | None
    reasons: tuple[str, ...] = ()


def _validated_evidence(
    evidence: ExternalEvidence | None,
    *,
    allowed_systems: frozenset[EvidenceSystem] | None = None,
    operation: str | None = None,
) -> bool:
    if evidence is None:
        return False
    try:
        evidence.validate()
    except ValueError:
        return False
    if not evidence.confirmed:
        return False
    if allowed_systems is not None and evidence.system not in allowed_systems:
        return False
    if operation is not None and evidence.operation != operation:
        return False
    return True


def run_preflight(request: PreflightRequest) -> PreflightDecision:
    """Evaluate the mandatory temporal gate before temporal reasoning."""

    reasons: list[str] = []
    limitations: list[str] = []
    trusted_now: datetime | None = None

    if not _validated_evidence(request.now_evidence, allowed_systems=TRUSTED_NOW_SYSTEMS, operation="current_time"):
        reasons.append("TRUSTED_NOW_UNVERIFIED")
    else:
        try:
            trusted_now = _as_aware_datetime(request.now, "now")
        except ValueError:
            reasons.append("TRUSTED_NOW_INVALID")

    if request.scope is None:
        reasons.append("SCOPE_UNRESOLVED")
    else:
        try:
            request.scope.validate()
        except ValueError:
            reasons.append("SCOPE_INVALID")
        else:
            limitations.extend(request.scope.limitations)

    if not request.coordination_inbox_checked:
        reasons.append("COORDINATION_INBOX_NOT_CHECKED")
    elif not _validated_evidence(
        request.coordination_read_evidence,
        allowed_systems=frozenset({EvidenceSystem.SUPABASE}),
        operation="coordination_read_inbox",
    ):
        reasons.append("COORDINATION_INBOX_UNVERIFIED")

    addressed: list[CoordinationEvent] = []
    seen_sequences: set[int] = set()
    for event in request.coordination_events:
        try:
            event.validate()
        except ValueError:
            reasons.append("COORDINATION_EVENT_INVALID")
            continue
        if event.event_sequence in seen_sequences:
            reasons.append("COORDINATION_SEQUENCE_CONFLICT")
        seen_sequences.add(event.event_sequence)
        if event.target_workstream in (None, request.workstream):
            addressed.append(event)

    if request.retrieval_required and not _validated_evidence(
        request.retrieval_evidence,
        allowed_systems=frozenset({EvidenceSystem.SUPABASE, EvidenceSystem.BASIC_MEMORY}),
    ):
        reasons.append("TEMPORAL_RETRIEVAL_UNVERIFIED")

    if request.prior_anchor_required and request.prior_anchor is None:
        reasons.append("PRIOR_ANCHOR_MISSING")

    if request.prior_anchor is not None:
        try:
            request.prior_anchor.validate()
        except ValueError:
            reasons.append("PRIOR_ANCHOR_INVALID")
        else:
            if request.scope is not None and request.prior_anchor.scope_instance_id != request.scope.scope_instance_id:
                reasons.append("PRIOR_ANCHOR_SCOPE_MISMATCH")
            if trusted_now is not None:
                anchor_time = request.prior_anchor.point.best_time
                if anchor_time is None:
                    reasons.append("PRIOR_ANCHOR_TIME_UNAVAILABLE")
                elif trusted_now < anchor_time:
                    reasons.append("PRIOR_ANCHOR_FROM_FUTURE")
                elif trusted_now - anchor_time > request.maximum_anchor_age:
                    reasons.append("PRIOR_ANCHOR_STALE")
            if (
                request.immutable_proof_required
                and request.prior_anchor.point.source.system not in IMMUTABLE_EVIDENCE_SYSTEMS
            ):
                reasons.append("PRIOR_ANCHOR_NOT_IMMUTABLE")

    if request.model_claims:
        limitations.append("Model claims were ignored as temporal evidence.")

    status = AnchorStatus.ANCHORED if not reasons else AnchorStatus.UNANCHORED
    return PreflightDecision(
        status=status,
        reasons=tuple(dict.fromkeys(reasons)),
        trusted_now=trusted_now,
        scope=request.scope,
        addressed_events=tuple(sorted(addressed, key=lambda event: event.event_sequence)),
        prior_anchor=request.prior_anchor,
        limitations=tuple(dict.fromkeys(limitations)),
    )


def run_postflight(request: PostflightRequest) -> TurnTemporalResult:
    """Evaluate persistence and handoff evidence after reasoning."""

    reasons: list[str] = []
    limitations = list(request.preflight.limitations)
    temporal_reference: str | None = None
    handoff_references: list[str] = []

    if request.preflight.status is not AnchorStatus.ANCHORED:
        reasons.append("PREFLIGHT_UNANCHORED")

    if request.material_transition:
        if not _validated_evidence(
            request.temporal_write_evidence,
            allowed_systems=frozenset({EvidenceSystem.SUPABASE}),
            operation="append_temporal_event",
        ):
            reasons.append("MATERIAL_TRANSITION_NOT_PERSISTED")
        else:
            temporal_reference = request.temporal_write_evidence.reference_id

    evidence_by_target: dict[Workstream, ExternalEvidence] = {}
    for handoff in request.handoff_evidence:
        if handoff.target_workstream in evidence_by_target:
            reasons.append(f"DUPLICATE_HANDOFF_EVIDENCE:{handoff.target_workstream.value}")
            continue
        evidence_by_target[handoff.target_workstream] = handoff.write_evidence

    for target in request.required_handoff_targets:
        evidence = evidence_by_target.get(target)
        if not _validated_evidence(
            evidence,
            allowed_systems=frozenset({EvidenceSystem.SUPABASE}),
            operation="coordination_post",
        ):
            reasons.append(f"REQUIRED_HANDOFF_UNCONFIRMED:{target.value}")
        else:
            assert evidence is not None and evidence.reference_id is not None
            handoff_references.append(evidence.reference_id)

    if request.model_claims:
        limitations.append("Model claims of saving or delivery were ignored.")

    status = AnchorStatus.ANCHORED if not reasons else AnchorStatus.UNANCHORED
    return TurnTemporalResult(
        status=status,
        reasons=tuple(dict.fromkeys(reasons)),
        temporal_reference_id=temporal_reference,
        handoff_reference_ids=tuple(handoff_references),
        limitations=tuple(dict.fromkeys(limitations)),
    )


def elapsed_between(start: TemporalPoint, end: TemporalPoint) -> ElapsedResult:
    """Calculate elapsed time without inventing precision."""

    try:
        start.validate()
        end.validate()
    except ValueError as exc:
        return ElapsedResult(ElapsedStatus.CONFLICTED, None, None, None, (str(exc),))

    if start.precision is TemporalPrecision.UNKNOWN or end.precision is TemporalPrecision.UNKNOWN:
        return ElapsedResult(
            ElapsedStatus.UNAVAILABLE,
            None,
            None,
            None,
            ("At least one endpoint has UNKNOWN temporal precision.",),
        )

    start_best = start.best_time
    end_best = end.best_time
    assert start_best is not None and end_best is not None
    best = (end_best - start_best).total_seconds()
    if best < 0:
        return ElapsedResult(
            ElapsedStatus.CONFLICTED,
            None,
            None,
            None,
            ("Best-supported end time precedes start time.",),
        )

    if TemporalPrecision.APPROXIMATE in (start.precision, end.precision):
        return ElapsedResult(ElapsedStatus.APPROXIMATE, best, None, None)

    start_interval = start.interval()
    end_interval = end.interval()
    assert start_interval is not None and end_interval is not None
    lower = (end_interval[0] - start_interval[1]).total_seconds()
    upper = (end_interval[1] - start_interval[0]).total_seconds()
    if upper < 0 or lower < 0:
        return ElapsedResult(
            ElapsedStatus.CONFLICTED,
            None,
            None,
            None,
            ("Supported endpoint intervals do not establish non-negative ordering.",),
        )
    if start.precision is TemporalPrecision.EXACT and end.precision is TemporalPrecision.EXACT:
        return ElapsedResult(ElapsedStatus.EXACT, best, best, best)
    return ElapsedResult(ElapsedStatus.BOUNDED, best, lower, upper)


def canonical_turn_hash(payload: dict[str, object]) -> str:
    """Hash externally supplied turn evidence for idempotency and comparison."""

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()

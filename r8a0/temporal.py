"""Fail-closed temporal orientation for the R8A0 vertical slice."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterable, Mapping

from .canonical import canonical_sha256


class OrientationState(str, Enum):
    COMPLETE = "COMPLETE"
    COMPLETE_FROM_FRESH_SNAPSHOT = "COMPLETE_FROM_FRESH_SNAPSHOT"
    DEGRADED_BOUNDED = "DEGRADED_BOUNDED"
    STALE = "STALE"
    CONFLICTED = "CONFLICTED"
    UNKNOWN = "UNKNOWN"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


CURRENT_TIME = "current_time"
SEMANTIC_TIME_DIMENSIONS = (
    "current_chat_time",
    "project_interaction_time",
    "durable_state_time",
    "event_time",
    "record_time",
    "retrieval_time",
)
REQUIRED_DIMENSIONS = (CURRENT_TIME, *SEMANTIC_TIME_DIMENSIONS)
SOURCE_MODES = {"CURRENT_SOURCE", "FRESH_BOUND_SNAPSHOT"}


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class TimeEvidence:
    dimension: str
    value: str
    source: str
    source_kind: str
    observed_at: str
    source_digest: str
    lower_bound: str | None = None
    upper_bound: str | None = None

    def validate(self) -> None:
        if self.dimension not in REQUIRED_DIMENSIONS:
            raise ValueError(f"unknown time dimension: {self.dimension}")
        if not self.source or not self.source_digest:
            raise ValueError("source and source digest are required")
        if self.source_kind != self.dimension:
            raise ValueError("time evidence source kind does not match its semantic dimension")
        if len(self.source_digest) != 64 or any(c not in "0123456789abcdef" for c in self.source_digest.lower()):
            raise ValueError("source digest must be lowercase hexadecimal SHA-256")
        value = parse_time(self.value)
        observed = parse_time(self.observed_at)
        lower = parse_time(self.lower_bound) if self.lower_bound else None
        upper = parse_time(self.upper_bound) if self.upper_bound else None
        if (lower is None) != (upper is None):
            raise ValueError("bounded evidence requires both lower and upper bounds")
        if lower and upper and lower > upper:
            raise ValueError("lower bound exceeds upper bound")
        if lower and value < lower:
            raise ValueError("value precedes lower bound")
        if upper and value > upper:
            raise ValueError("value exceeds upper bound")
        if observed < value - timedelta(minutes=5):
            raise ValueError("observation materially predates the claimed value")

    def as_dict(self) -> dict[str, str | None]:
        return {
            "dimension": self.dimension,
            "value": self.value,
            "source": self.source,
            "source_kind": self.source_kind,
            "observed_at": self.observed_at,
            "source_digest": self.source_digest,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
        }


@dataclass(frozen=True)
class OrientationReceipt:
    state: OrientationState
    evaluated_at: str
    evidence_digest: str
    missing_dimensions: tuple[str, ...]
    stale_dimensions: tuple[str, ...]
    conflicted_dimensions: tuple[str, ...]
    invalid_dimensions: tuple[str, ...]
    claims_allowed: bool
    source_mode: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": "VERA_R8A0_TEMPORAL_ORIENTATION_RECEIPT_V1",
            "state": self.state.value,
            "evaluated_at": self.evaluated_at,
            "evidence_digest": self.evidence_digest,
            "missing_dimensions": list(self.missing_dimensions),
            "stale_dimensions": list(self.stale_dimensions),
            "conflicted_dimensions": list(self.conflicted_dimensions),
            "invalid_dimensions": list(self.invalid_dimensions),
            "claims_allowed": self.claims_allowed,
            "source_mode": self.source_mode,
        }


class OrientationGate:
    def __init__(self, max_age: timedelta = timedelta(minutes=10)) -> None:
        if max_age <= timedelta(0):
            raise ValueError("max_age must be positive")
        self.max_age = max_age

    def evaluate(
        self,
        evidence: Iterable[TimeEvidence],
        *,
        now: datetime,
        required_dimensions: Iterable[str] = REQUIRED_DIMENSIONS,
        source_mode: str = "CURRENT_SOURCE",
        degraded_allowed: bool = False,
    ) -> OrientationReceipt:
        if now.tzinfo is None:
            raise ValueError("now must include a timezone")
        if source_mode not in SOURCE_MODES:
            raise ValueError("unsupported source mode")
        now = now.astimezone(timezone.utc)
        required = tuple(required_dimensions)
        if any(dimension not in REQUIRED_DIMENSIONS for dimension in required):
            raise ValueError("required dimensions contain an unknown semantic time")

        grouped: dict[str, list[TimeEvidence]] = {}
        invalid: set[str] = set()
        materialized: list[dict[str, str | None]] = []
        for item in evidence:
            grouped.setdefault(item.dimension, []).append(item)
            materialized.append(item.as_dict())
            try:
                item.validate()
            except ValueError:
                invalid.add(item.dimension)

        missing = tuple(sorted(set(required) - set(grouped)))
        stale: set[str] = set()
        conflicted: set[str] = set()
        for dimension, rows in grouped.items():
            valid_rows = [row for row in rows if dimension not in invalid]
            values = {parse_time(row.value) for row in valid_rows}
            source_digests = {row.source_digest for row in valid_rows}
            if len(values) > 1 or len(source_digests) > 1:
                conflicted.add(dimension)
            for row in valid_rows:
                observed = parse_time(row.observed_at)
                if now - observed > self.max_age or observed - now > timedelta(minutes=5):
                    stale.add(dimension)
                if source_mode == "FRESH_BOUND_SNAPSHOT" and not (row.lower_bound and row.upper_bound):
                    invalid.add(dimension)

        if conflicted:
            state = OrientationState.CONFLICTED
        elif invalid:
            state = OrientationState.UNKNOWN
        elif missing:
            state = OrientationState.DEGRADED_BOUNDED if degraded_allowed else OrientationState.UNKNOWN
        elif stale:
            state = OrientationState.STALE
        elif source_mode == "FRESH_BOUND_SNAPSHOT":
            state = OrientationState.COMPLETE_FROM_FRESH_SNAPSHOT
        else:
            state = OrientationState.COMPLETE
        claims_allowed = state in {
            OrientationState.COMPLETE,
            OrientationState.COMPLETE_FROM_FRESH_SNAPSHOT,
        }
        return OrientationReceipt(
            state=state,
            evaluated_at=now.isoformat(),
            evidence_digest=canonical_sha256(materialized),
            missing_dimensions=missing,
            stale_dimensions=tuple(sorted(stale)),
            conflicted_dimensions=tuple(sorted(conflicted)),
            invalid_dimensions=tuple(sorted(invalid)),
            claims_allowed=claims_allowed,
            source_mode=source_mode,
        )


def current_evidence(
    now: datetime,
    *,
    source: str = "VERIFIED_CURRENT_TIME_SOURCE",
    source_digest: str,
) -> list[TimeEvidence]:
    """Return only current wall-clock evidence.

    Semantic event, record, retrieval, project, durable-state, and chat times must be
    supplied from their own provenance-bearing sources. They are deliberately not
    inferred from the wall clock merely because humans enjoy convenient lies.
    """
    if now.tzinfo is None:
        raise ValueError("now must include a timezone")
    value = now.astimezone(timezone.utc).isoformat()
    return [
        TimeEvidence(
            dimension=CURRENT_TIME,
            value=value,
            source=source,
            source_kind=CURRENT_TIME,
            observed_at=value,
            source_digest=source_digest,
        )
    ]


def evidence_from_mapping(rows: Mapping[str, Mapping[str, str | None]]) -> list[TimeEvidence]:
    """Build evidence from explicit, separately sourced semantic-time records."""
    return [
        TimeEvidence(
            dimension=dimension,
            value=str(row["value"]),
            source=str(row["source"]),
            source_kind=str(row["source_kind"]),
            observed_at=str(row["observed_at"]),
            source_digest=str(row["source_digest"]),
            lower_bound=str(row["lower_bound"]) if row.get("lower_bound") else None,
            upper_bound=str(row["upper_bound"]) if row.get("upper_bound") else None,
        )
        for dimension, row in rows.items()
    ]

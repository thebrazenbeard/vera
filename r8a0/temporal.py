"""Fail-closed temporal orientation for the R8A0 vertical slice."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterable

from .canonical import canonical_sha256


class OrientationState(str, Enum):
    COMPLETE = "COMPLETE"
    COMPLETE_FROM_FRESH_SNAPSHOT = "COMPLETE_FROM_FRESH_SNAPSHOT"
    DEGRADED_BOUNDED = "DEGRADED_BOUNDED"
    STALE = "STALE"
    CONFLICTED = "CONFLICTED"
    UNKNOWN = "UNKNOWN"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


REQUIRED_DIMENSIONS = (
    "current_chat_time",
    "project_interaction_time",
    "durable_state_time",
    "event_time",
    "record_time",
    "retrieval_time",
)


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
    observed_at: str
    lower_bound: str | None = None
    upper_bound: str | None = None

    def validate(self) -> None:
        if not self.dimension or not self.source:
            raise ValueError("dimension and source are required")
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
            "observed_at": self.observed_at,
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
        now = now.astimezone(timezone.utc)
        required = tuple(required_dimensions)
        grouped: dict[str, list[TimeEvidence]] = {}
        invalid_dimensions: set[str] = set()
        materialized: list[dict[str, str | None]] = []
        for item in evidence:
            try:
                item.validate()
            except ValueError:
                invalid_dimensions.add(item.dimension)
            grouped.setdefault(item.dimension, []).append(item)
            materialized.append(item.as_dict())

        missing = tuple(sorted(set(required) - set(grouped)))
        stale: set[str] = set(invalid_dimensions)
        conflicted: set[str] = set()
        for dimension, rows in grouped.items():
            values = {parse_time(row.value) for row in rows if row.dimension not in invalid_dimensions}
            if len(values) > 1:
                conflicted.add(dimension)
            for row in rows:
                try:
                    observed = parse_time(row.observed_at)
                except ValueError:
                    stale.add(dimension)
                    continue
                if now - observed > self.max_age or observed - now > timedelta(minutes=5):
                    stale.add(dimension)

        if conflicted:
            state = OrientationState.CONFLICTED
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
            claims_allowed=claims_allowed,
            source_mode=source_mode,
        )


def current_evidence(now: datetime, *, source: str = "VERIFIED_CLOCK") -> list[TimeEvidence]:
    if now.tzinfo is None:
        raise ValueError("now must include a timezone")
    value = now.astimezone(timezone.utc).isoformat()
    return [TimeEvidence(dimension, value, source, value) for dimension in REQUIRED_DIMENSIONS]

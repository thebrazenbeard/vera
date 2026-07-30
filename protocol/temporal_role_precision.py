"""Role-specific temporal precision for the V.E.R.A. enforcement kernel.

The original bounded kernel attached one precision value to ``event_time`` while
also carrying state, record, and retrieval timestamps. This strict layer makes
precision explicit for every temporal role and binds the complete shape to the
external evidence verifier.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Any

from . import temporal_enforcement as legacy


@dataclass(frozen=True)
class RoleTemporalPoint:
    """A temporal point with independent uncertainty for every time role."""

    source: legacy.ExternalEvidence
    scope_instance_id: str
    event_time: datetime | str | None = None
    event_time_precision: legacy.TemporalPrecision = legacy.TemporalPrecision.UNKNOWN
    event_time_lower_bound: datetime | str | None = None
    event_time_upper_bound: datetime | str | None = None
    state_time: datetime | str | None = None
    state_time_precision: legacy.TemporalPrecision = legacy.TemporalPrecision.UNKNOWN
    state_time_lower_bound: datetime | str | None = None
    state_time_upper_bound: datetime | str | None = None
    record_time: datetime | str | None = None
    record_time_precision: legacy.TemporalPrecision = legacy.TemporalPrecision.UNKNOWN
    record_time_lower_bound: datetime | str | None = None
    record_time_upper_bound: datetime | str | None = None
    retrieval_time: datetime | str | None = None
    retrieval_time_precision: legacy.TemporalPrecision = legacy.TemporalPrecision.UNKNOWN
    retrieval_time_lower_bound: datetime | str | None = None
    retrieval_time_upper_bound: datetime | str | None = None

    def _validate_role(
        self,
        *,
        role: str,
        value: datetime | str | None,
        precision: legacy.TemporalPrecision,
        lower_bound: datetime | str | None,
        upper_bound: datetime | str | None,
    ) -> None:
        if not isinstance(precision, legacy.TemporalPrecision):
            raise ValueError(f"{role}_precision must be a TemporalPrecision")

        normalized = (
            legacy._as_aware_datetime(value, role) if value is not None else None
        )
        lower = (
            legacy._as_aware_datetime(lower_bound, f"{role}_lower_bound")
            if lower_bound is not None else None
        )
        upper = (
            legacy._as_aware_datetime(upper_bound, f"{role}_upper_bound")
            if upper_bound is not None else None
        )

        if precision is legacy.TemporalPrecision.EXACT:
            if normalized is None or lower is not None or upper is not None:
                raise ValueError(f"EXACT {role} requires a value and forbids bounds")
        elif precision is legacy.TemporalPrecision.BOUNDED:
            if normalized is None or lower is None or upper is None:
                raise ValueError(
                    f"BOUNDED {role} requires a value and both inclusive bounds"
                )
            if lower > upper or not lower <= normalized <= upper:
                raise ValueError(f"BOUNDED {role} has inconsistent bounds")
        elif precision is legacy.TemporalPrecision.APPROXIMATE:
            if normalized is None or lower is not None or upper is not None:
                raise ValueError(
                    f"APPROXIMATE {role} requires a value and forbids hard bounds"
                )
        elif precision is legacy.TemporalPrecision.UNKNOWN:
            if normalized is not None or lower is not None or upper is not None:
                raise ValueError(f"UNKNOWN {role} forbids values and bounds")

    def validate_shape(self) -> None:
        self.source.validate_shape()
        if not self.source.confirmed:
            raise ValueError("role temporal point requires confirmed evidence claim")
        legacy._nonblank(self.scope_instance_id, "scope_instance_id")

        self._validate_role(
            role="event_time",
            value=self.event_time,
            precision=self.event_time_precision,
            lower_bound=self.event_time_lower_bound,
            upper_bound=self.event_time_upper_bound,
        )
        self._validate_role(
            role="state_time",
            value=self.state_time,
            precision=self.state_time_precision,
            lower_bound=self.state_time_lower_bound,
            upper_bound=self.state_time_upper_bound,
        )
        self._validate_role(
            role="record_time",
            value=self.record_time,
            precision=self.record_time_precision,
            lower_bound=self.record_time_lower_bound,
            upper_bound=self.record_time_upper_bound,
        )
        self._validate_role(
            role="retrieval_time",
            value=self.retrieval_time,
            precision=self.retrieval_time_precision,
            lower_bound=self.retrieval_time_lower_bound,
            upper_bound=self.retrieval_time_upper_bound,
        )

    @property
    def best_time(self) -> datetime | None:
        if self.event_time_precision is legacy.TemporalPrecision.UNKNOWN:
            return None
        assert self.event_time is not None
        return legacy._as_aware_datetime(self.event_time, "event_time")

    @property
    def freshness_time(self) -> datetime | None:
        """Materialization/state freshness, never retrieval recency."""

        for role, value, precision in (
            ("record_time", self.record_time, self.record_time_precision),
            ("state_time", self.state_time, self.state_time_precision),
            ("event_time", self.event_time, self.event_time_precision),
        ):
            if precision is not legacy.TemporalPrecision.UNKNOWN:
                assert value is not None
                return legacy._as_aware_datetime(value, role)
        return None

    def interval(self) -> tuple[datetime, datetime] | None:
        self.validate_shape()
        if self.event_time_precision is legacy.TemporalPrecision.UNKNOWN:
            return None
        if self.event_time_precision is legacy.TemporalPrecision.BOUNDED:
            assert self.event_time_lower_bound is not None
            assert self.event_time_upper_bound is not None
            return (
                legacy._as_aware_datetime(
                    self.event_time_lower_bound, "event_time_lower_bound"
                ),
                legacy._as_aware_datetime(
                    self.event_time_upper_bound, "event_time_upper_bound"
                ),
            )
        if self.event_time_precision is legacy.TemporalPrecision.EXACT:
            best = self.best_time
            assert best is not None
            return best, best
        return None


def role_temporal_point_subject_hash(point: RoleTemporalPoint) -> str:
    """Bind evidence to all values, precisions, bounds, scope, and provenance."""

    point.validate_shape()
    payload: dict[str, Any] = {
        "scope_instance_id": point.scope_instance_id,
        "event_time": legacy._iso(point.event_time, "event_time"),
        "event_time_precision": point.event_time_precision,
        "event_time_lower_bound": legacy._iso(
            point.event_time_lower_bound, "event_time_lower_bound"
        ),
        "event_time_upper_bound": legacy._iso(
            point.event_time_upper_bound, "event_time_upper_bound"
        ),
        "state_time": legacy._iso(point.state_time, "state_time"),
        "state_time_precision": point.state_time_precision,
        "state_time_lower_bound": legacy._iso(
            point.state_time_lower_bound, "state_time_lower_bound"
        ),
        "state_time_upper_bound": legacy._iso(
            point.state_time_upper_bound, "state_time_upper_bound"
        ),
        "record_time": legacy._iso(point.record_time, "record_time"),
        "record_time_precision": point.record_time_precision,
        "record_time_lower_bound": legacy._iso(
            point.record_time_lower_bound, "record_time_lower_bound"
        ),
        "record_time_upper_bound": legacy._iso(
            point.record_time_upper_bound, "record_time_upper_bound"
        ),
        "retrieval_time": legacy._iso(point.retrieval_time, "retrieval_time"),
        "retrieval_time_precision": point.retrieval_time_precision,
        "retrieval_time_lower_bound": legacy._iso(
            point.retrieval_time_lower_bound, "retrieval_time_lower_bound"
        ),
        "retrieval_time_upper_bound": legacy._iso(
            point.retrieval_time_upper_bound, "retrieval_time_upper_bound"
        ),
        "source_system": point.source.system,
        "source_operation": point.source.operation,
        "source_reference_id": point.source.reference_id,
    }
    return legacy.canonical_subject_hash("role_temporal_point", payload)


def run_preflight(
    request: legacy.PreflightRequest,
    verifier: legacy.EvidenceVerifier | None,
) -> legacy.PreflightDecision:
    """Run the base gate plus strict role-precision prior-anchor validation."""

    original_anchor = request.prior_anchor
    base_request = replace(
        request,
        prior_anchor=None,
        prior_anchor_required=False,
    )
    base_decision = legacy.run_preflight(base_request, verifier)
    reasons = list(base_decision.reasons)
    limitations = list(base_decision.limitations)

    if request.prior_anchor_required and original_anchor is None:
        reasons.append("PRIOR_ANCHOR_MISSING")

    if original_anchor is not None:
        point = original_anchor.point
        if not isinstance(point, RoleTemporalPoint):
            reasons.append("PRIOR_ANCHOR_ROLE_PRECISION_MISSING")
        else:
            try:
                original_anchor.validate_shape()
                subject_hash = role_temporal_point_subject_hash(point)
            except ValueError:
                reasons.append("PRIOR_ANCHOR_INVALID")
            else:
                if not legacy._verified_evidence(
                    verifier,
                    point.source,
                    allowed_systems=legacy.TEMPORAL_READ_SYSTEMS,
                    operation="temporal_read",
                    subject_hash=subject_hash,
                    require_immutable=request.immutable_proof_required,
                ):
                    reasons.append("PRIOR_ANCHOR_EVIDENCE_UNVERIFIED")
                if (
                    request.scope is not None
                    and original_anchor.scope_instance_id
                    != request.scope.scope_instance_id
                ):
                    reasons.append("PRIOR_ANCHOR_SCOPE_MISMATCH")

                trusted_now = base_decision.trusted_now
                if trusted_now is not None:
                    event_time = point.best_time
                    if event_time is not None and event_time > trusted_now:
                        reasons.append("PRIOR_ANCHOR_FROM_FUTURE")
                    freshness_time = point.freshness_time
                    if freshness_time is None:
                        reasons.append("PRIOR_ANCHOR_FRESHNESS_UNAVAILABLE")
                    elif trusted_now < freshness_time:
                        reasons.append("PRIOR_ANCHOR_RECORDED_IN_FUTURE")
                    elif (
                        request.maximum_anchor_age >= timedelta(0)
                        and trusted_now - freshness_time
                        > request.maximum_anchor_age
                    ):
                        reasons.append("PRIOR_ANCHOR_STALE")

    status = (
        legacy.AnchorStatus.ANCHORED
        if not reasons
        else legacy.AnchorStatus.UNANCHORED
    )
    return legacy.PreflightDecision(
        status=status,
        reasons=tuple(dict.fromkeys(reasons)),
        trusted_now=base_decision.trusted_now,
        scope=base_decision.scope,
        addressed_events=base_decision.addressed_events,
        prior_anchor=original_anchor,
        limitations=tuple(dict.fromkeys(limitations)),
    )


# Re-export unchanged postflight and elapsed logic. Their evidence subjects are
# independent of the prior-anchor role-precision representation.
run_postflight = legacy.run_postflight
elapsed_between = legacy.elapsed_between

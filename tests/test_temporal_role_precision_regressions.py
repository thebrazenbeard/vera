from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from protocol import temporal_enforcement as legacy
from protocol.temporal_role_precision import (
    RoleTemporalPoint,
    TemporalRole,
    adapt_memory_state_time,
    elapsed_between,
    role_temporal_point_subject_hash,
    run_preflight,
)


NOW = datetime(2026, 7, 30, 23, 40, tzinfo=timezone.utc)


def evidence(reference_id: str = "temporal-role-test") -> legacy.ExternalEvidence:
    return legacy.ExternalEvidence(
        system=legacy.EvidenceSystem.SUPABASE,
        operation="temporal_read",
        confirmed=True,
        reference_id=reference_id,
        observed_at=NOW,
        subject_hash="0" * 64,
        immutable=True,
    )


def point(
    *,
    scope: str = "scope-one",
    event_time=NOW,
    event_precision=legacy.TemporalPrecision.EXACT,
    event_lower=None,
    event_upper=None,
    state_time=None,
    state_precision=legacy.TemporalPrecision.UNKNOWN,
    record_time=None,
    record_precision=legacy.TemporalPrecision.UNKNOWN,
    retrieval_time=None,
    retrieval_precision=legacy.TemporalPrecision.UNKNOWN,
) -> RoleTemporalPoint:
    return RoleTemporalPoint(
        source=evidence(),
        scope_instance_id=scope,
        event_time=event_time,
        event_time_precision=event_precision,
        event_time_lower_bound=event_lower,
        event_time_upper_bound=event_upper,
        state_time=state_time,
        state_time_precision=state_precision,
        record_time=record_time,
        record_time_precision=record_precision,
        retrieval_time=retrieval_time,
        retrieval_time_precision=retrieval_precision,
    )


class RegistryVerifier:
    def __init__(self) -> None:
        self.records: dict[str, tuple[legacy.EvidenceSystem, str, str, bool]] = {}
        self.counter = 0

    def issue(
        self,
        system: legacy.EvidenceSystem,
        operation: str,
        subject_hash: str,
        *,
        immutable: bool = False,
    ) -> legacy.ExternalEvidence:
        self.counter += 1
        reference_id = f"verified-{self.counter}"
        self.records[reference_id] = (system, operation, subject_hash, immutable)
        return legacy.ExternalEvidence(
            system=system,
            operation=operation,
            confirmed=True,
            reference_id=reference_id,
            observed_at=NOW,
            subject_hash=subject_hash,
            immutable=immutable,
        )

    def verify(
        self,
        evidence,
        *,
        allowed_systems,
        operation,
        subject_hash,
        require_immutable=False,
    ):
        registered = self.records.get(evidence.reference_id)
        if registered is None:
            return False
        system, expected_operation, expected_hash, immutable = registered
        return (
            evidence.system is system
            and system in allowed_systems
            and evidence.operation == operation == expected_operation
            and evidence.subject_hash == subject_hash == expected_hash
            and (not require_immutable or (immutable and evidence.immutable))
        )


class RoleAwareElapsedRegressionTests(unittest.TestCase):
    def test_exact_elapsed_uses_event_role(self):
        result = elapsed_between(
            point(event_time=NOW),
            point(event_time=NOW + timedelta(seconds=90)),
        )
        self.assertIs(result.status, legacy.ElapsedStatus.EXACT)
        self.assertEqual(
            (result.best_seconds, result.lower_seconds, result.upper_seconds),
            (90, 90, 90),
        )

    def test_bounded_elapsed_preserves_interval(self):
        start = point(
            event_time=NOW,
            event_precision=legacy.TemporalPrecision.BOUNDED,
            event_lower=NOW - timedelta(seconds=5),
            event_upper=NOW + timedelta(seconds=5),
        )
        end = point(
            event_time=NOW + timedelta(seconds=60),
            event_precision=legacy.TemporalPrecision.BOUNDED,
            event_lower=NOW + timedelta(seconds=55),
            event_upper=NOW + timedelta(seconds=65),
        )
        result = elapsed_between(start, end)
        self.assertIs(result.status, legacy.ElapsedStatus.BOUNDED)
        self.assertEqual(
            (result.best_seconds, result.lower_seconds, result.upper_seconds),
            (60, 50, 70),
        )

    def test_approximate_elapsed_does_not_invent_bounds(self):
        result = elapsed_between(
            point(event_precision=legacy.TemporalPrecision.APPROXIMATE),
            point(event_time=NOW + timedelta(seconds=30)),
        )
        self.assertIs(result.status, legacy.ElapsedStatus.APPROXIMATE)
        self.assertEqual(result.best_seconds, 30)
        self.assertIsNone(result.lower_seconds)
        self.assertIsNone(result.upper_seconds)

    def test_unknown_elapsed_is_unavailable(self):
        result = elapsed_between(
            point(event_time=None, event_precision=legacy.TemporalPrecision.UNKNOWN),
            point(),
        )
        self.assertIs(result.status, legacy.ElapsedStatus.UNAVAILABLE)

    def test_reversed_elapsed_is_conflicted(self):
        result = elapsed_between(
            point(),
            point(event_time=NOW - timedelta(seconds=1)),
        )
        self.assertIs(result.status, legacy.ElapsedStatus.CONFLICTED)

    def test_cross_scope_elapsed_is_conflicted(self):
        result = elapsed_between(
            point(scope="scope-a"),
            point(scope="scope-b", event_time=NOW + timedelta(seconds=1)),
        )
        self.assertIs(result.status, legacy.ElapsedStatus.CONFLICTED)

    def test_explicit_state_role_is_supported(self):
        start = point(
            event_time=None,
            event_precision=legacy.TemporalPrecision.UNKNOWN,
            state_time=NOW,
            state_precision=legacy.TemporalPrecision.EXACT,
        )
        end = point(
            event_time=None,
            event_precision=legacy.TemporalPrecision.UNKNOWN,
            state_time=NOW + timedelta(seconds=15),
            state_precision=legacy.TemporalPrecision.EXACT,
        )
        result = elapsed_between(start, end, TemporalRole.STATE_TIME)
        self.assertIs(result.status, legacy.ElapsedStatus.EXACT)
        self.assertEqual(result.best_seconds, 15)


class FreshnessRegressionTests(unittest.TestCase):
    def test_recent_record_and_retrieval_times_do_not_refresh_old_state(self):
        old = NOW - timedelta(days=45)
        temporal_point = point(
            event_time=old,
            state_time=old,
            state_precision=legacy.TemporalPrecision.EXACT,
            record_time=NOW,
            record_precision=legacy.TemporalPrecision.EXACT,
            retrieval_time=NOW,
            retrieval_precision=legacy.TemporalPrecision.EXACT,
        )
        self.assertEqual(temporal_point.freshness_time, old)
        self.assertEqual(temporal_point.persistence_time, NOW)

    def test_preflight_marks_old_state_stale_despite_recent_record_time(self):
        verifier = RegistryVerifier()
        scope = legacy.resolve_scope(
            project_id="vera-reciprocal-agency-environment",
            observed_at=NOW,
            provider_conversation_id="conversation-one",
            provider_branch_id="branch-one",
        )
        old = NOW - timedelta(days=45)
        draft = point(
            scope=scope.scope_instance_id,
            event_time=old,
            state_time=old,
            state_precision=legacy.TemporalPrecision.EXACT,
            record_time=NOW,
            record_precision=legacy.TemporalPrecision.EXACT,
            retrieval_time=NOW,
            retrieval_precision=legacy.TemporalPrecision.EXACT,
        )
        bound = replace(
            draft,
            source=verifier.issue(
                legacy.EvidenceSystem.SUPABASE,
                "temporal_read",
                role_temporal_point_subject_hash(draft),
                immutable=True,
            ),
        )
        anchor = legacy.TemporalAnchor(
            anchor_id="old-state-new-record",
            anchor_key="project/current-time",
            scope_instance_id=scope.scope_instance_id,
            status=legacy.AnchorStatus.ANCHORED,
            point=bound,
        )
        request = legacy.PreflightRequest(
            workstream=legacy.Workstream.TIME,
            now=NOW,
            now_evidence=verifier.issue(
                legacy.EvidenceSystem.HOST,
                "current_time",
                legacy.current_time_subject_hash(NOW),
            ),
            scope=scope,
            scope_evidence=verifier.issue(
                legacy.EvidenceSystem.HOST,
                "resolve_scope",
                legacy.scope_subject_hash(scope),
            ),
            coordination_inbox_checked=True,
            coordination_read_evidence=verifier.issue(
                legacy.EvidenceSystem.SUPABASE,
                "coordination_read_inbox",
                legacy.coordination_inbox_subject_hash(legacy.Workstream.TIME, ()),
            ),
            prior_anchor_required=True,
            prior_anchor=anchor,
            maximum_anchor_age=timedelta(days=30),
        )
        result = run_preflight(request, verifier)
        self.assertIn("PRIOR_ANCHOR_STALE", result.reasons)
        self.assertNotIn("PRIOR_ANCHOR_RECORDED_IN_FUTURE", result.reasons)
        self.assertIs(result.status, legacy.AnchorStatus.UNANCHORED)


class MemorySentinelBoundaryTests(unittest.TestCase):
    def test_unknown_sentinel_normalizes_before_point_construction(self):
        value, precision, lower, upper = adapt_memory_state_time(
            "-infinity",
            legacy.TemporalPrecision.UNKNOWN,
            temporal_claim=False,
        )
        self.assertIsNone(value)
        self.assertIs(precision, legacy.TemporalPrecision.UNKNOWN)
        self.assertIsNone(lower)
        self.assertIsNone(upper)

    def test_unknown_sentinel_rejects_exact_precision(self):
        with self.assertRaisesRegex(
            ValueError,
            "MEMORY_UNKNOWN_STATE_SENTINEL_PRECISION_MISMATCH",
        ):
            adapt_memory_state_time(
                "-infinity",
                legacy.TemporalPrecision.EXACT,
                temporal_claim=False,
            )

    def test_unknown_sentinel_rejects_temporal_claim(self):
        with self.assertRaisesRegex(
            ValueError,
            "MEMORY_UNKNOWN_STATE_SENTINEL_TEMPORAL_CLAIM_INVALID",
        ):
            adapt_memory_state_time(
                "-infinity",
                legacy.TemporalPrecision.UNKNOWN,
                temporal_claim=True,
            )

    def test_unknown_sentinel_rejects_bounds(self):
        with self.assertRaisesRegex(
            ValueError,
            "MEMORY_UNKNOWN_STATE_SENTINEL_BOUNDS_FORBIDDEN",
        ):
            adapt_memory_state_time(
                "-infinity",
                legacy.TemporalPrecision.UNKNOWN,
                lower_bound=NOW,
                temporal_claim=False,
            )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from protocol import temporal_enforcement as legacy
from protocol.temporal_role_precision import (
    MEMORY_UNKNOWN_STATE_TIME_SENTINEL,
    RoleTemporalPoint,
    TemporalRole,
    adapt_memory_state_time,
    elapsed_between,
    role_temporal_point_subject_hash,
    run_preflight,
)


NOW = datetime(2026, 7, 30, 23, 30, tzinfo=timezone.utc)
EARLIER = NOW - timedelta(hours=2)
OLD = NOW - timedelta(days=90)


class TestVerifier:
    def __init__(self) -> None:
        self.records: dict[
            str, tuple[legacy.EvidenceSystem, str, str, bool]
        ] = {}
        self.counter = 0

    def issue(
        self,
        system: legacy.EvidenceSystem,
        operation: str,
        subject_hash: str,
        *,
        immutable: bool = False,
        reference_id: str | None = None,
    ) -> legacy.ExternalEvidence:
        self.counter += 1
        reference_id = reference_id or f"strict-correction-{self.counter}"
        self.records[reference_id] = (
            system,
            operation,
            subject_hash,
            immutable,
        )
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


def placeholder(reference_id: str = "strict-point") -> legacy.ExternalEvidence:
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
    event_time=EARLIER,
    event_precision=legacy.TemporalPrecision.EXACT,
    event_lower=None,
    event_upper=None,
    state_time=None,
    state_precision=legacy.TemporalPrecision.UNKNOWN,
    state_lower=None,
    state_upper=None,
    record_time=None,
    record_precision=legacy.TemporalPrecision.UNKNOWN,
    retrieval_time=None,
    retrieval_precision=legacy.TemporalPrecision.UNKNOWN,
) -> RoleTemporalPoint:
    return RoleTemporalPoint(
        source=placeholder(),
        scope_instance_id=scope,
        event_time=event_time,
        event_time_precision=event_precision,
        event_time_lower_bound=event_lower,
        event_time_upper_bound=event_upper,
        state_time=state_time,
        state_time_precision=state_precision,
        state_time_lower_bound=state_lower,
        state_time_upper_bound=state_upper,
        record_time=record_time,
        record_time_precision=record_precision,
        retrieval_time=retrieval_time,
        retrieval_time_precision=retrieval_precision,
    )


class RoleAwareElapsedTests(unittest.TestCase):
    def test_exact_event_elapsed(self):
        start = point(event_time=EARLIER)
        end = point(event_time=NOW)
        result = elapsed_between(start, end)
        self.assertEqual(result.status, legacy.ElapsedStatus.EXACT)
        self.assertEqual(result.best_seconds, 7200)
        self.assertEqual(result.lower_seconds, 7200)
        self.assertEqual(result.upper_seconds, 7200)

    def test_bounded_event_elapsed(self):
        start = point(
            event_time=EARLIER,
            event_precision=legacy.TemporalPrecision.BOUNDED,
            event_lower=EARLIER - timedelta(minutes=5),
            event_upper=EARLIER + timedelta(minutes=5),
        )
        end = point(
            event_time=NOW,
            event_precision=legacy.TemporalPrecision.BOUNDED,
            event_lower=NOW - timedelta(minutes=10),
            event_upper=NOW + timedelta(minutes=10),
        )
        result = elapsed_between(start, end)
        self.assertEqual(result.status, legacy.ElapsedStatus.BOUNDED)
        self.assertEqual(result.best_seconds, 7200)
        self.assertEqual(result.lower_seconds, 6300)
        self.assertEqual(result.upper_seconds, 8100)

    def test_approximate_state_elapsed_uses_named_role(self):
        start = point(
            state_time=EARLIER,
            state_precision=legacy.TemporalPrecision.APPROXIMATE,
        )
        end = point(
            state_time=NOW,
            state_precision=legacy.TemporalPrecision.EXACT,
        )
        result = elapsed_between(start, end, TemporalRole.STATE_TIME)
        self.assertEqual(result.status, legacy.ElapsedStatus.APPROXIMATE)
        self.assertEqual(result.best_seconds, 7200)

    def test_unknown_role_is_unavailable(self):
        result = elapsed_between(
            point(event_time=None, event_precision=legacy.TemporalPrecision.UNKNOWN),
            point(event_time=NOW),
        )
        self.assertEqual(result.status, legacy.ElapsedStatus.UNAVAILABLE)
        self.assertIn("UNKNOWN event_time precision", result.reasons[0])

    def test_reversed_role_is_conflicted(self):
        result = elapsed_between(
            point(event_time=NOW),
            point(event_time=EARLIER),
        )
        self.assertEqual(result.status, legacy.ElapsedStatus.CONFLICTED)

    def test_cross_scope_is_conflicted(self):
        result = elapsed_between(
            point(scope="scope-one"),
            point(scope="scope-two", event_time=NOW),
        )
        self.assertEqual(result.status, legacy.ElapsedStatus.CONFLICTED)

    def test_invalid_role_returns_conflicted_result(self):
        result = elapsed_between(point(), point(event_time=NOW), "delivery_time")
        self.assertEqual(result.status, legacy.ElapsedStatus.CONFLICTED)
        self.assertIn("unsupported temporal role", result.reasons[0])


class MemorySentinelAdapterTests(unittest.TestCase):
    def test_unknown_sentinel_converts_to_none(self):
        value, precision, lower, upper = adapt_memory_state_time(
            MEMORY_UNKNOWN_STATE_TIME_SENTINEL,
            legacy.TemporalPrecision.UNKNOWN,
            temporal_claim=False,
        )
        self.assertIsNone(value)
        self.assertIs(precision, legacy.TemporalPrecision.UNKNOWN)
        self.assertIsNone(lower)
        self.assertIsNone(upper)

        adapted = point(
            state_time=value,
            state_precision=precision,
            state_lower=lower,
            state_upper=upper,
        )
        adapted.validate_shape()

    def test_sentinel_with_exact_precision_is_rejected_by_name(self):
        with self.assertRaisesRegex(
            ValueError,
            "MEMORY_UNKNOWN_STATE_SENTINEL_PRECISION_MISMATCH",
        ):
            adapt_memory_state_time(
                MEMORY_UNKNOWN_STATE_TIME_SENTINEL,
                legacy.TemporalPrecision.EXACT,
                temporal_claim=False,
            )

    def test_sentinel_temporal_claim_is_rejected_by_name(self):
        with self.assertRaisesRegex(
            ValueError,
            "MEMORY_UNKNOWN_STATE_SENTINEL_TEMPORAL_CLAIM_INVALID",
        ):
            adapt_memory_state_time(
                MEMORY_UNKNOWN_STATE_TIME_SENTINEL,
                legacy.TemporalPrecision.UNKNOWN,
                temporal_claim=True,
            )

    def test_unknown_non_sentinel_value_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "MEMORY_UNKNOWN_STATE_TIME_VALUE_PRESENT",
        ):
            adapt_memory_state_time(
                NOW,
                legacy.TemporalPrecision.UNKNOWN,
                temporal_claim=False,
            )


class SubstantiveFreshnessTests(unittest.TestCase):
    def test_record_and_retrieval_time_do_not_refresh_old_state(self):
        p = point(
            event_time=OLD,
            state_time=OLD,
            state_precision=legacy.TemporalPrecision.EXACT,
            record_time=NOW,
            record_precision=legacy.TemporalPrecision.EXACT,
            retrieval_time=NOW,
            retrieval_precision=legacy.TemporalPrecision.EXACT,
        )
        self.assertEqual(p.freshness_time, OLD)
        self.assertEqual(p.persistence_time, NOW)

    def test_old_state_with_recent_persistence_remains_stale_in_preflight(self):
        verifier = TestVerifier()
        scope = legacy.resolve_scope(
            project_id="vera-reciprocal-agency-environment",
            observed_at=NOW,
            provider_conversation_id="conversation-one",
            provider_branch_id="branch-one",
        )

        draft = point(
            scope=scope.scope_instance_id,
            event_time=OLD,
            state_time=OLD,
            state_precision=legacy.TemporalPrecision.EXACT,
            record_time=NOW,
            record_precision=legacy.TemporalPrecision.EXACT,
            retrieval_time=NOW,
            retrieval_precision=legacy.TemporalPrecision.EXACT,
        )
        evidence = verifier.issue(
            legacy.EvidenceSystem.SUPABASE,
            "temporal_read",
            role_temporal_point_subject_hash(draft),
            immutable=True,
            reference_id="stale-role-point",
        )
        strict_point = replace(draft, source=evidence)
        anchor = legacy.TemporalAnchor(
            anchor_id="stale-anchor",
            anchor_key="project/current-time",
            scope_instance_id=scope.scope_instance_id,
            status=legacy.AnchorStatus.ANCHORED,
            point=strict_point,
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
                legacy.coordination_inbox_subject_hash(
                    legacy.Workstream.TIME,
                    (),
                ),
            ),
            prior_anchor_required=True,
            prior_anchor=anchor,
            maximum_anchor_age=timedelta(days=30),
        )

        decision = run_preflight(request, verifier)
        self.assertEqual(decision.status, legacy.AnchorStatus.UNANCHORED)
        self.assertIn("PRIOR_ANCHOR_STALE", decision.reasons)


if __name__ == "__main__":
    unittest.main()

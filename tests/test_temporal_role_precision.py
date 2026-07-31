from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import unittest

from protocol import temporal_enforcement as legacy
from protocol.temporal_role_precision import (
    RoleTemporalPoint,
    role_temporal_point_subject_hash,
    run_preflight,
)


NOW = datetime(2026, 7, 30, 23, 10, tzinfo=timezone.utc)


class TestVerifier:
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
        reference_id: str | None = None,
    ) -> legacy.ExternalEvidence:
        self.counter += 1
        reference_id = reference_id or f"role-ref-{self.counter}"
        self.records[reference_id] = (
            system,
            operation,
            subject_hash,
            immutable,
        )
        return legacy.ExternalEvidence(
            system,
            operation,
            True,
            reference_id,
            NOW,
            subject_hash,
            immutable,
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


def placeholder(reference_id: str = "role-point") -> legacy.ExternalEvidence:
    return legacy.ExternalEvidence(
        legacy.EvidenceSystem.SUPABASE,
        "temporal_read",
        True,
        reference_id,
        NOW,
        "0" * 64,
        True,
    )


def issue_point(
    verifier: TestVerifier,
    *,
    scope_id: str,
    event_time=NOW,
    event_precision=legacy.TemporalPrecision.EXACT,
    state_time=NOW,
    state_precision=legacy.TemporalPrecision.EXACT,
    record_time=NOW,
    record_precision=legacy.TemporalPrecision.EXACT,
    retrieval_time=NOW,
    retrieval_precision=legacy.TemporalPrecision.EXACT,
) -> RoleTemporalPoint:
    draft = RoleTemporalPoint(
        source=placeholder(),
        scope_instance_id=scope_id,
        event_time=event_time,
        event_time_precision=event_precision,
        state_time=state_time,
        state_time_precision=state_precision,
        record_time=record_time,
        record_time_precision=record_precision,
        retrieval_time=retrieval_time,
        retrieval_time_precision=retrieval_precision,
    )
    subject = role_temporal_point_subject_hash(draft)
    evidence = verifier.issue(
        legacy.EvidenceSystem.SUPABASE,
        "temporal_read",
        subject,
        immutable=True,
        reference_id="role-point",
    )
    return replace(draft, source=evidence)


def stable_scope():
    return legacy.resolve_scope(
        project_id="vera-reciprocal-agency-environment",
        observed_at=NOW,
        provider_conversation_id="conversation-one",
        provider_branch_id="branch-one",
    )


def good_request(verifier: TestVerifier, scope, anchor):
    now_evidence = verifier.issue(
        legacy.EvidenceSystem.HOST,
        "current_time",
        legacy.current_time_subject_hash(NOW),
    )
    scope_evidence = verifier.issue(
        legacy.EvidenceSystem.HOST,
        "resolve_scope",
        legacy.scope_subject_hash(scope),
    )
    inbox_evidence = verifier.issue(
        legacy.EvidenceSystem.SUPABASE,
        "coordination_read_inbox",
        legacy.coordination_inbox_subject_hash(legacy.Workstream.TIME, ()),
    )
    return legacy.PreflightRequest(
        workstream=legacy.Workstream.TIME,
        now=NOW,
        now_evidence=now_evidence,
        scope=scope,
        scope_evidence=scope_evidence,
        coordination_inbox_checked=True,
        coordination_read_evidence=inbox_evidence,
        prior_anchor_required=True,
        prior_anchor=anchor,
    )


class RolePrecisionShapeTests(unittest.TestCase):
    def test_state_timestamp_cannot_hide_under_unknown_precision(self):
        point = RoleTemporalPoint(
            source=placeholder(),
            scope_instance_id="scope",
            state_time=NOW,
            state_time_precision=legacy.TemporalPrecision.UNKNOWN,
        )
        with self.assertRaisesRegex(ValueError, "UNKNOWN state_time"):
            point.validate_shape()

    def test_retrieval_timestamp_requires_explicit_precision(self):
        point = RoleTemporalPoint(
            source=placeholder(),
            scope_instance_id="scope",
            retrieval_time=NOW,
        )
        with self.assertRaisesRegex(ValueError, "UNKNOWN retrieval_time"):
            point.validate_shape()

    def test_each_role_preserves_independent_precision(self):
        point = RoleTemporalPoint(
            source=placeholder(),
            scope_instance_id="scope",
            event_time=NOW,
            event_time_precision=legacy.TemporalPrecision.EXACT,
            state_time=NOW,
            state_time_precision=legacy.TemporalPrecision.APPROXIMATE,
            record_time=NOW,
            record_time_precision=legacy.TemporalPrecision.EXACT,
            retrieval_time=NOW,
            retrieval_time_precision=legacy.TemporalPrecision.BOUNDED,
            retrieval_time_lower_bound=NOW,
            retrieval_time_upper_bound=NOW,
        )
        point.validate_shape()

    def test_role_precision_is_bound_into_subject_hash(self):
        exact = RoleTemporalPoint(
            source=placeholder(),
            scope_instance_id="scope",
            state_time=NOW,
            state_time_precision=legacy.TemporalPrecision.EXACT,
        )
        approximate = replace(
            exact,
            state_time_precision=legacy.TemporalPrecision.APPROXIMATE,
        )
        self.assertNotEqual(
            role_temporal_point_subject_hash(exact),
            role_temporal_point_subject_hash(approximate),
        )

    def test_retrieval_time_does_not_refresh_substantive_anchor(self):
        point = RoleTemporalPoint(
            source=placeholder(),
            scope_instance_id="scope",
            retrieval_time=NOW,
            retrieval_time_precision=legacy.TemporalPrecision.EXACT,
        )
        self.assertIsNone(point.freshness_time)


class StrictPreflightTests(unittest.TestCase):
    def test_strict_preflight_rejects_legacy_single_precision_anchor(self):
        verifier = TestVerifier()
        scope = stable_scope()
        old_evidence = verifier.issue(
            legacy.EvidenceSystem.SUPABASE,
            "temporal_read",
            "0" * 64,
            immutable=True,
        )
        old_point = legacy.TemporalPoint(
            precision=legacy.TemporalPrecision.EXACT,
            source=old_evidence,
            scope_instance_id=scope.scope_instance_id,
            event_time=NOW,
            state_time=NOW,
            record_time=NOW,
            retrieval_time=NOW,
        )
        anchor = legacy.TemporalAnchor(
            anchor_id="legacy-anchor",
            anchor_key="project/current-time",
            scope_instance_id=scope.scope_instance_id,
            status=legacy.AnchorStatus.ANCHORED,
            point=old_point,
        )
        result = run_preflight(good_request(verifier, scope, anchor), verifier)
        self.assertIn("PRIOR_ANCHOR_ROLE_PRECISION_MISSING", result.reasons)
        self.assertEqual(result.status, legacy.AnchorStatus.UNANCHORED)

    def test_strict_preflight_accepts_verified_role_precision_anchor(self):
        verifier = TestVerifier()
        scope = stable_scope()
        point = issue_point(verifier, scope_id=scope.scope_instance_id)
        anchor = legacy.TemporalAnchor(
            anchor_id="strict-anchor",
            anchor_key="project/current-time",
            scope_instance_id=scope.scope_instance_id,
            status=legacy.AnchorStatus.ANCHORED,
            point=point,
        )
        result = run_preflight(good_request(verifier, scope, anchor), verifier)
        self.assertEqual(result.reasons, ())
        self.assertEqual(result.status, legacy.AnchorStatus.ANCHORED)

    def test_changed_precision_invalidates_external_binding(self):
        verifier = TestVerifier()
        scope = stable_scope()
        point = issue_point(verifier, scope_id=scope.scope_instance_id)
        altered = replace(
            point,
            state_time_precision=legacy.TemporalPrecision.APPROXIMATE,
        )
        anchor = legacy.TemporalAnchor(
            anchor_id="altered-anchor",
            anchor_key="project/current-time",
            scope_instance_id=scope.scope_instance_id,
            status=legacy.AnchorStatus.ANCHORED,
            point=altered,
        )
        result = run_preflight(good_request(verifier, scope, anchor), verifier)
        self.assertIn("PRIOR_ANCHOR_EVIDENCE_UNVERIFIED", result.reasons)


if __name__ == "__main__":
    unittest.main()

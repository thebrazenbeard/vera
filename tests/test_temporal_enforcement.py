from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch
from uuid import UUID

from protocol.temporal_enforcement import (
    AnchorStatus,
    CoordinationEvent,
    ElapsedStatus,
    EvidenceSystem,
    ExternalEvidence,
    HandoffEvidence,
    PostflightRequest,
    PreflightRequest,
    ScopeStability,
    TemporalAnchor,
    TemporalPoint,
    TemporalPrecision,
    Workstream,
    elapsed_between,
    resolve_scope,
    run_postflight,
    run_preflight,
)

NOW = datetime(2026, 7, 30, 21, 5, tzinfo=timezone.utc)


def evidence(
    system: EvidenceSystem,
    operation: str,
    *,
    confirmed: bool = True,
    reference_id: str = "ref-1",
    immutable: bool = False,
) -> ExternalEvidence:
    return ExternalEvidence(
        system=system,
        operation=operation,
        confirmed=confirmed,
        reference_id=reference_id if confirmed else None,
        observed_at=NOW if confirmed else None,
        immutable=immutable,
    )


def stable_scope():
    return resolve_scope(
        project_id="vera-reciprocal-agency-environment",
        observed_at=NOW,
        provider_conversation_id="conv-1",
        provider_branch_id="branch-1",
    )


def exact_point(*, scope_id: str | None = None, when: datetime = NOW, system=EvidenceSystem.SUPABASE):
    return TemporalPoint(
        precision=TemporalPrecision.EXACT,
        source=evidence(system, "temporal_read", immutable=system is EvidenceSystem.SUPABASE),
        scope_instance_id=scope_id or stable_scope().scope_instance_id,
        event_time=when,
        state_time=when,
        record_time=when,
        retrieval_time=NOW,
    )


def good_preflight(**overrides):
    scope = overrides.pop("scope", stable_scope())
    values = dict(
        workstream=Workstream.TIME,
        now=NOW,
        now_evidence=evidence(EvidenceSystem.HOST, "current_time"),
        scope=scope,
        coordination_inbox_checked=True,
        coordination_read_evidence=evidence(EvidenceSystem.SUPABASE, "coordination_read_inbox"),
    )
    values.update(overrides)
    return run_preflight(PreflightRequest(**values))


class ScopeTests(unittest.TestCase):
    def test_stable_scope_uses_provider_ids(self):
        scope = stable_scope()
        self.assertEqual(scope.stability, ScopeStability.STABLE)
        self.assertIn("conv-1", scope.conversation_id)
        self.assertIn("branch-1", scope.branch_id)

    def test_stable_scope_instance_is_repeatable(self):
        first = stable_scope()
        second = stable_scope()
        self.assertEqual(first.scope_instance_id, second.scope_instance_id)
        self.assertNotEqual(first.session_id, second.session_id)

    def test_ephemeral_scope_is_internally_issued(self):
        fixed = iter([
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            UUID("00000000-0000-0000-0000-000000000003"),
            UUID("00000000-0000-0000-0000-000000000004"),
        ])
        with patch("protocol.temporal_enforcement._new_uuid", side_effect=lambda: next(fixed)):
            scope = resolve_scope(project_id="vera", observed_at=NOW)
        self.assertEqual(scope.stability, ScopeStability.EPHEMERAL)
        self.assertIsNone(scope.provider_conversation_id)
        self.assertIn("proves no durable recognition", " ".join(scope.limitations))

    def test_repeated_ephemeral_scopes_are_fresh(self):
        self.assertNotEqual(
            resolve_scope(project_id="vera", observed_at=NOW).scope_instance_id,
            resolve_scope(project_id="vera", observed_at=NOW).scope_instance_id,
        )

    def test_partial_provider_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_scope(project_id="vera", observed_at=NOW, provider_conversation_id="conv")

    def test_blank_project_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_scope(project_id=" ", observed_at=NOW)


class TemporalPointTests(unittest.TestCase):
    def test_exact_point_is_valid(self):
        exact_point().validate()

    def test_exact_requires_event_time(self):
        point = TemporalPoint(
            precision=TemporalPrecision.EXACT,
            source=evidence(EvidenceSystem.SUPABASE, "read"),
            scope_instance_id="scope",
        )
        with self.assertRaises(ValueError):
            point.validate()

    def test_bounded_point_is_valid(self):
        point = TemporalPoint(
            precision=TemporalPrecision.BOUNDED,
            source=evidence(EvidenceSystem.SUPABASE, "read"),
            scope_instance_id="scope",
            event_time=NOW,
            lower_bound=NOW - timedelta(minutes=1),
            upper_bound=NOW + timedelta(minutes=1),
        )
        point.validate()

    def test_bounded_reversed_bounds_are_rejected(self):
        point = TemporalPoint(
            precision=TemporalPrecision.BOUNDED,
            source=evidence(EvidenceSystem.SUPABASE, "read"),
            scope_instance_id="scope",
            event_time=NOW,
            lower_bound=NOW + timedelta(minutes=1),
            upper_bound=NOW - timedelta(minutes=1),
        )
        with self.assertRaises(ValueError):
            point.validate()

    def test_bounded_event_outside_bounds_is_rejected(self):
        point = TemporalPoint(
            precision=TemporalPrecision.BOUNDED,
            source=evidence(EvidenceSystem.SUPABASE, "read"),
            scope_instance_id="scope",
            event_time=NOW + timedelta(minutes=2),
            lower_bound=NOW - timedelta(minutes=1),
            upper_bound=NOW + timedelta(minutes=1),
        )
        with self.assertRaises(ValueError):
            point.validate()

    def test_unknown_forbids_timestamp(self):
        point = TemporalPoint(
            precision=TemporalPrecision.UNKNOWN,
            source=evidence(EvidenceSystem.SUPABASE, "read"),
            scope_instance_id="scope",
            event_time=NOW,
        )
        with self.assertRaises(ValueError):
            point.validate()

    def test_model_cannot_be_temporal_evidence(self):
        point = TemporalPoint(
            precision=TemporalPrecision.EXACT,
            source=evidence(EvidenceSystem.MODEL, "claimed_read"),
            scope_instance_id="scope",
            event_time=NOW,
        )
        with self.assertRaises(ValueError):
            point.validate()

    def test_timezone_naive_time_is_rejected(self):
        point = TemporalPoint(
            precision=TemporalPrecision.EXACT,
            source=evidence(EvidenceSystem.SUPABASE, "read"),
            scope_instance_id="scope",
            event_time=datetime(2026, 7, 30, 17, 5),
        )
        with self.assertRaises(ValueError):
            point.validate()


class PreflightTests(unittest.TestCase):
    def test_happy_path_is_anchored(self):
        self.assertEqual(good_preflight().status, AnchorStatus.ANCHORED)

    def test_missing_now_fails_closed(self):
        result = good_preflight(now=None)
        self.assertEqual(result.status, AnchorStatus.UNANCHORED)
        self.assertIn("TRUSTED_NOW_INVALID", result.reasons)

    def test_unconfirmed_now_fails_closed(self):
        result = good_preflight(now_evidence=evidence(EvidenceSystem.HOST, "current_time", confirmed=False))
        self.assertIn("TRUSTED_NOW_UNVERIFIED", result.reasons)

    def test_basic_memory_cannot_supply_trusted_now(self):
        result = good_preflight(now_evidence=evidence(EvidenceSystem.BASIC_MEMORY, "current_time"))
        self.assertIn("TRUSTED_NOW_UNVERIFIED", result.reasons)

    def test_naive_now_fails_closed_instead_of_crashing(self):
        result = good_preflight(now=datetime(2026, 7, 30, 17, 5))
        self.assertIn("TRUSTED_NOW_INVALID", result.reasons)

    def test_inbox_must_be_checked(self):
        result = good_preflight(coordination_inbox_checked=False)
        self.assertIn("COORDINATION_INBOX_NOT_CHECKED", result.reasons)

    def test_inbox_read_must_be_confirmed_by_supabase(self):
        result = good_preflight(
            coordination_read_evidence=evidence(EvidenceSystem.MODEL, "coordination_read_inbox")
        )
        self.assertIn("COORDINATION_INBOX_UNVERIFIED", result.reasons)

    def test_duplicate_coordination_sequence_is_conflicted(self):
        events = tuple(
            CoordinationEvent(
                event_id=f"event-{index}",
                event_sequence=1,
                thread_key="thread",
                source_workstream=Workstream.MEMORY,
                target_workstream=Workstream.TIME,
                event_type="ISSUE",
                status="READY_FOR_REVIEW",
                record_time=NOW,
            )
            for index in range(2)
        )
        self.assertIn("COORDINATION_SEQUENCE_CONFLICT", good_preflight(coordination_events=events).reasons)

    def test_only_addressed_events_are_returned(self):
        events = (
            CoordinationEvent("e1", 1, "t", Workstream.MEMORY, Workstream.TIME, "ISSUE", "READY", NOW),
            CoordinationEvent("e2", 2, "t", Workstream.TIME, Workstream.INITIATIVES, "STATUS", "READY", NOW),
        )
        result = good_preflight(coordination_events=events)
        self.assertEqual([event.event_id for event in result.addressed_events], ["e1"])

    def test_required_retrieval_must_be_externally_confirmed(self):
        self.assertIn(
            "TEMPORAL_RETRIEVAL_UNVERIFIED",
            good_preflight(retrieval_required=True, retrieval_evidence=None).reasons,
        )

    def test_missing_required_prior_anchor_fails(self):
        self.assertIn("PRIOR_ANCHOR_MISSING", good_preflight(prior_anchor_required=True).reasons)

    def test_prior_anchor_scope_mismatch_fails(self):
        scope = stable_scope()
        other_scope = resolve_scope(
            project_id="vera-reciprocal-agency-environment",
            observed_at=NOW,
            provider_conversation_id="conv-2",
            provider_branch_id="branch-2",
        )
        anchor = TemporalAnchor(
            "a1",
            other_scope.scope_instance_id,
            AnchorStatus.ANCHORED,
            exact_point(scope_id=other_scope.scope_instance_id),
        )
        self.assertIn("PRIOR_ANCHOR_SCOPE_MISMATCH", good_preflight(scope=scope, prior_anchor=anchor).reasons)

    def test_stale_prior_anchor_fails(self):
        scope = stable_scope()
        old = NOW - timedelta(days=31)
        anchor = TemporalAnchor(
            "a1",
            scope.scope_instance_id,
            AnchorStatus.ANCHORED,
            exact_point(scope_id=scope.scope_instance_id, when=old),
        )
        self.assertIn("PRIOR_ANCHOR_STALE", good_preflight(scope=scope, prior_anchor=anchor).reasons)

    def test_basic_memory_anchor_is_not_immutable_proof(self):
        scope = stable_scope()
        anchor = TemporalAnchor(
            "a1",
            scope.scope_instance_id,
            AnchorStatus.ANCHORED,
            exact_point(scope_id=scope.scope_instance_id, system=EvidenceSystem.BASIC_MEMORY),
        )
        result = good_preflight(scope=scope, prior_anchor=anchor, immutable_proof_required=True)
        self.assertIn("PRIOR_ANCHOR_NOT_IMMUTABLE", result.reasons)

    def test_model_claim_does_not_promote_failed_preflight(self):
        result = good_preflight(
            coordination_inbox_checked=False,
            model_claims=("I checked the inbox and know the current time.",),
        )
        self.assertEqual(result.status, AnchorStatus.UNANCHORED)
        self.assertIn("Model claims were ignored", " ".join(result.limitations))


class PostflightTests(unittest.TestCase):
    def test_nonmaterial_turn_needs_no_write(self):
        result = run_postflight(PostflightRequest(good_preflight(), material_transition=False))
        self.assertEqual(result.status, AnchorStatus.ANCHORED)

    def test_material_turn_requires_confirmed_supabase_write(self):
        result = run_postflight(
            PostflightRequest(
                good_preflight(),
                material_transition=True,
                temporal_write_evidence=evidence(
                    EvidenceSystem.SUPABASE,
                    "append_temporal_event",
                    reference_id="temporal-1",
                ),
            )
        )
        self.assertEqual(result.status, AnchorStatus.ANCHORED)
        self.assertEqual(result.temporal_reference_id, "temporal-1")

    def test_material_turn_without_write_is_unanchored(self):
        result = run_postflight(PostflightRequest(good_preflight(), material_transition=True))
        self.assertIn("MATERIAL_TRANSITION_NOT_PERSISTED", result.reasons)

    def test_basic_memory_write_does_not_count_as_immutable_temporal_write(self):
        result = run_postflight(
            PostflightRequest(
                good_preflight(),
                material_transition=True,
                temporal_write_evidence=evidence(EvidenceSystem.BASIC_MEMORY, "append_temporal_event"),
            )
        )
        self.assertEqual(result.status, AnchorStatus.UNANCHORED)

    def test_memory_and_initiatives_handoffs_can_be_required(self):
        handoffs = (
            HandoffEvidence(
                Workstream.MEMORY,
                evidence(EvidenceSystem.SUPABASE, "coordination_post", reference_id="coord-1"),
            ),
            HandoffEvidence(
                Workstream.INITIATIVES,
                evidence(EvidenceSystem.SUPABASE, "coordination_post", reference_id="coord-2"),
            ),
        )
        result = run_postflight(
            PostflightRequest(
                good_preflight(),
                material_transition=False,
                required_handoff_targets=(Workstream.MEMORY, Workstream.INITIATIVES),
                handoff_evidence=handoffs,
            )
        )
        self.assertEqual(result.status, AnchorStatus.ANCHORED)
        self.assertEqual(result.handoff_reference_ids, ("coord-1", "coord-2"))

    def test_missing_required_initiatives_handoff_fails(self):
        result = run_postflight(
            PostflightRequest(
                good_preflight(),
                material_transition=False,
                required_handoff_targets=(Workstream.INITIATIVES,),
            )
        )
        self.assertIn("REQUIRED_HANDOFF_UNCONFIRMED:workstream/initiatives", result.reasons)

    def test_model_claim_cannot_replace_write(self):
        result = run_postflight(
            PostflightRequest(
                good_preflight(),
                material_transition=True,
                model_claims=("I saved the temporal anchor.",),
            )
        )
        self.assertEqual(result.status, AnchorStatus.UNANCHORED)
        self.assertIn("Model claims of saving", " ".join(result.limitations))

    def test_unanchored_preflight_cannot_be_repaired_postflight(self):
        result = run_postflight(
            PostflightRequest(good_preflight(coordination_inbox_checked=False), material_transition=False)
        )
        self.assertIn("PREFLIGHT_UNANCHORED", result.reasons)


class ElapsedTests(unittest.TestCase):
    def test_exact_elapsed(self):
        result = elapsed_between(exact_point(when=NOW), exact_point(when=NOW + timedelta(seconds=90)))
        self.assertEqual(result.status, ElapsedStatus.EXACT)
        self.assertEqual(result.best_seconds, 90)

    def test_reversed_exact_is_conflicted(self):
        result = elapsed_between(exact_point(when=NOW), exact_point(when=NOW - timedelta(seconds=1)))
        self.assertEqual(result.status, ElapsedStatus.CONFLICTED)

    def test_bounded_elapsed(self):
        start = TemporalPoint(
            TemporalPrecision.BOUNDED,
            evidence(EvidenceSystem.SUPABASE, "read"),
            "scope",
            event_time=NOW,
            lower_bound=NOW - timedelta(seconds=2),
            upper_bound=NOW + timedelta(seconds=2),
        )
        end = TemporalPoint(
            TemporalPrecision.EXACT,
            evidence(EvidenceSystem.SUPABASE, "read"),
            "scope",
            event_time=NOW + timedelta(seconds=10),
        )
        result = elapsed_between(start, end)
        self.assertEqual(result.status, ElapsedStatus.BOUNDED)
        self.assertEqual((result.lower_seconds, result.upper_seconds), (8, 12))

    def test_overlapping_bounds_are_conflicted(self):
        start = TemporalPoint(
            TemporalPrecision.BOUNDED,
            evidence(EvidenceSystem.SUPABASE, "read"),
            "scope",
            event_time=NOW,
            lower_bound=NOW - timedelta(seconds=10),
            upper_bound=NOW + timedelta(seconds=10),
        )
        end = exact_point(scope_id="scope", when=NOW + timedelta(seconds=5))
        self.assertEqual(elapsed_between(start, end).status, ElapsedStatus.CONFLICTED)

    def test_approximate_elapsed_remains_approximate(self):
        start = TemporalPoint(
            TemporalPrecision.APPROXIMATE,
            evidence(EvidenceSystem.SUPABASE, "read"),
            "scope",
            event_time=NOW,
        )
        result = elapsed_between(start, exact_point(scope_id="scope", when=NOW + timedelta(seconds=5)))
        self.assertEqual(result.status, ElapsedStatus.APPROXIMATE)

    def test_unknown_elapsed_is_unavailable(self):
        start = TemporalPoint(
            TemporalPrecision.UNKNOWN,
            evidence(EvidenceSystem.SUPABASE, "read"),
            "scope",
        )
        self.assertEqual(elapsed_between(start, exact_point(scope_id="scope")).status, ElapsedStatus.UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()

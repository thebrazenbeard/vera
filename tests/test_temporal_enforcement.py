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
    RequiredHandoff,
    ScopeStability,
    TemporalAnchor,
    TemporalPoint,
    TemporalPrecision,
    Workstream,
    canonical_subject_hash,
    coordination_inbox_subject_hash,
    current_time_subject_hash,
    elapsed_between,
    resolve_scope,
    run_postflight,
    run_preflight,
    scope_subject_hash,
    temporal_point_subject_hash,
)

NOW = datetime(2026, 7, 30, 21, 5, tzinfo=timezone.utc)


class TestVerifier:
    """Test-only stand-in for a host-owned connector evidence adapter."""

    def __init__(self):
        self.records: dict[str, tuple[EvidenceSystem, str, str, bool]] = {}
        self.counter = 0

    def issue(
        self,
        system: EvidenceSystem,
        operation: str,
        subject_hash: str,
        *,
        immutable: bool = False,
        reference_id: str | None = None,
    ) -> ExternalEvidence:
        self.counter += 1
        reference_id = reference_id or f"ref-{self.counter}"
        self.records[reference_id] = (system, operation, subject_hash, immutable)
        return ExternalEvidence(system, operation, True, reference_id, NOW, subject_hash, immutable)

    def verify(self, evidence, *, allowed_systems, operation, subject_hash, require_immutable=False):
        if evidence.reference_id not in self.records:
            return False
        system, registered_operation, registered_hash, immutable = self.records[evidence.reference_id]
        return (
            evidence.confirmed
            and evidence.system is system
            and evidence.system in allowed_systems
            and evidence.operation == operation == registered_operation
            and evidence.subject_hash == subject_hash == registered_hash
            and (not require_immutable or (immutable and evidence.immutable))
        )


def stable_scope():
    return resolve_scope(
        project_id="vera-reciprocal-agency-environment",
        observed_at=NOW,
        provider_conversation_id="conv-1",
        provider_branch_id="branch-1",
    )


def make_point(
    verifier: TestVerifier,
    *,
    scope_id: str,
    when: datetime = NOW,
    precision: TemporalPrecision = TemporalPrecision.EXACT,
    system: EvidenceSystem = EvidenceSystem.SUPABASE,
    record_time: datetime | None = None,
    lower: datetime | None = None,
    upper: datetime | None = None,
    ref: str | None = None,
):
    chosen_ref = ref or f"ref-{verifier.counter + 1}"
    placeholder = ExternalEvidence(
        system,
        "temporal_read",
        True,
        chosen_ref,
        NOW,
        "0" * 64,
        system in {EvidenceSystem.SUPABASE, EvidenceSystem.GITHUB},
    )
    point = TemporalPoint(
        precision=precision,
        source=placeholder,
        scope_instance_id=scope_id,
        event_time=None if precision is TemporalPrecision.UNKNOWN else when,
        state_time=None if precision is TemporalPrecision.UNKNOWN else when,
        record_time=record_time if record_time is not None else (None if precision is TemporalPrecision.UNKNOWN else when),
        retrieval_time=NOW,
        lower_bound=lower,
        upper_bound=upper,
    )
    subject = temporal_point_subject_hash(point)
    evidence = verifier.issue(
        system,
        "temporal_read",
        subject,
        immutable=system in {EvidenceSystem.SUPABASE, EvidenceSystem.GITHUB},
        reference_id=chosen_ref,
    )
    return TemporalPoint(
        precision=point.precision,
        source=evidence,
        scope_instance_id=point.scope_instance_id,
        event_time=point.event_time,
        state_time=point.state_time,
        record_time=point.record_time,
        retrieval_time=point.retrieval_time,
        lower_bound=point.lower_bound,
        upper_bound=point.upper_bound,
    )


def make_anchor(verifier: TestVerifier, scope, *, when=NOW, record_time=None, system=EvidenceSystem.SUPABASE):
    return TemporalAnchor(
        anchor_id="anchor-1",
        anchor_key="project/current-time",
        scope_instance_id=scope.scope_instance_id,
        status=AnchorStatus.ANCHORED,
        point=make_point(verifier, scope_id=scope.scope_instance_id, when=when, record_time=record_time, system=system),
    )


def good_preflight(verifier: TestVerifier, **overrides):
    scope = overrides.pop("scope", stable_scope())
    events = overrides.pop("coordination_events", ())
    values = dict(
        workstream=Workstream.TIME,
        now=NOW,
        now_evidence=verifier.issue(EvidenceSystem.HOST, "current_time", current_time_subject_hash(NOW)),
        scope=scope,
        scope_evidence=verifier.issue(EvidenceSystem.HOST, "resolve_scope", scope_subject_hash(scope)),
        coordination_inbox_checked=True,
        coordination_read_evidence=verifier.issue(
            EvidenceSystem.SUPABASE,
            "coordination_read_inbox",
            coordination_inbox_subject_hash(Workstream.TIME, events),
        ),
        coordination_events=events,
    )
    values.update(overrides)
    return run_preflight(PreflightRequest(**values), verifier)


class ScopeTests(unittest.TestCase):
    def test_stable_scope_repeatable_but_session_fresh(self):
        first, second = stable_scope(), stable_scope()
        self.assertEqual(first.stability, ScopeStability.STABLE)
        self.assertEqual(first.scope_instance_id, second.scope_instance_id)
        self.assertNotEqual(first.session_id, second.session_id)

    def test_ephemeral_scope_is_fresh_and_internal(self):
        first = resolve_scope(project_id="vera", observed_at=NOW)
        second = resolve_scope(project_id="vera", observed_at=NOW)
        self.assertEqual(first.stability, ScopeStability.EPHEMERAL)
        self.assertNotEqual(first.scope_instance_id, second.scope_instance_id)
        self.assertIn("no durable recognition", " ".join(first.limitations))

    def test_ephemeral_uuid_source_is_not_public_argument(self):
        fixed = iter(UUID(f"00000000-0000-0000-0000-{index:012d}") for index in range(1, 5))
        with patch("protocol.temporal_enforcement._new_uuid", side_effect=lambda: next(fixed)):
            scope = resolve_scope(project_id="vera", observed_at=NOW)
        self.assertTrue(scope.scope_instance_id.endswith("000000000004"))

    def test_partial_provider_identity_rejected(self):
        with self.assertRaises(ValueError):
            resolve_scope(project_id="vera", observed_at=NOW, provider_conversation_id="conv")

    def test_identity_collision_rejected(self):
        scope = stable_scope()
        bad = type(scope)(**{**scope.__dict__, "session_id": scope.scope_instance_id})
        with self.assertRaises(ValueError):
            bad.validate()


class EvidenceBindingTests(unittest.TestCase):
    def test_confirmed_evidence_requires_subject_hash(self):
        with self.assertRaises(ValueError):
            ExternalEvidence(EvidenceSystem.HOST, "current_time", True, "r", NOW, None).validate_shape()

    def test_model_cannot_be_confirmed_evidence(self):
        with self.assertRaises(ValueError):
            ExternalEvidence(EvidenceSystem.MODEL, "current_time", True, "r", NOW, "0" * 64).validate_shape()

    def test_self_labeled_host_evidence_not_in_verifier_fails(self):
        verifier = TestVerifier()
        forged = ExternalEvidence(EvidenceSystem.HOST, "current_time", True, "forged", NOW, current_time_subject_hash(NOW))
        result = good_preflight(verifier, now_evidence=forged)
        self.assertIn("TRUSTED_NOW_UNVERIFIED", result.reasons)

    def test_evidence_for_different_time_fails(self):
        verifier = TestVerifier()
        wrong = verifier.issue(EvidenceSystem.HOST, "current_time", current_time_subject_hash(NOW - timedelta(hours=1)))
        result = good_preflight(verifier, now_evidence=wrong)
        self.assertIn("TRUSTED_NOW_UNVERIFIED", result.reasons)

    def test_missing_verifier_fails_closed(self):
        verifier = TestVerifier()
        scope = stable_scope()
        request = PreflightRequest(
            Workstream.TIME,
            NOW,
            verifier.issue(EvidenceSystem.HOST, "current_time", current_time_subject_hash(NOW)),
            scope,
            verifier.issue(EvidenceSystem.HOST, "resolve_scope", scope_subject_hash(scope)),
            True,
            verifier.issue(
                EvidenceSystem.SUPABASE,
                "coordination_read_inbox",
                coordination_inbox_subject_hash(Workstream.TIME, ()),
            ),
        )
        result = run_preflight(request, None)
        self.assertIn("EVIDENCE_VERIFIER_MISSING", result.reasons)


class TemporalPointTests(unittest.TestCase):
    def test_exact_and_bounded_shapes(self):
        verifier = TestVerifier()
        make_point(verifier, scope_id="scope").validate_shape()
        make_point(
            verifier,
            scope_id="scope",
            precision=TemporalPrecision.BOUNDED,
            lower=NOW - timedelta(seconds=2),
            upper=NOW + timedelta(seconds=2),
        ).validate_shape()

    def test_bounded_event_outside_range_rejected(self):
        verifier = TestVerifier()
        with self.assertRaises(ValueError):
            make_point(
                verifier,
                scope_id="scope",
                when=NOW + timedelta(seconds=5),
                precision=TemporalPrecision.BOUNDED,
                lower=NOW - timedelta(seconds=1),
                upper=NOW + timedelta(seconds=1),
            )

    def test_unknown_forbids_time(self):
        verifier = TestVerifier()
        evidence = verifier.issue(EvidenceSystem.SUPABASE, "temporal_read", "0" * 64, immutable=True)
        point = TemporalPoint(TemporalPrecision.UNKNOWN, evidence, "scope", event_time=NOW)
        with self.assertRaises(ValueError):
            point.validate_shape()

    def test_naive_time_rejected(self):
        verifier = TestVerifier()
        placeholder = verifier.issue(EvidenceSystem.SUPABASE, "temporal_read", "0" * 64, immutable=True)
        point = TemporalPoint(TemporalPrecision.EXACT, placeholder, "scope", event_time=datetime(2026, 7, 30, 17, 5))
        with self.assertRaises(ValueError):
            point.validate_shape()

    def test_freshness_prefers_record_time(self):
        verifier = TestVerifier()
        point = make_point(
            verifier,
            scope_id="scope",
            when=NOW - timedelta(days=365),
            record_time=NOW - timedelta(minutes=1),
        )
        self.assertEqual(point.freshness_time, NOW - timedelta(minutes=1))


class PreflightTests(unittest.TestCase):
    def test_happy_path_anchored(self):
        verifier = TestVerifier()
        self.assertEqual(good_preflight(verifier).status, AnchorStatus.ANCHORED)

    def test_stable_scope_requires_host_binding(self):
        verifier = TestVerifier()
        result = good_preflight(verifier, scope_evidence=None)
        self.assertIn("STABLE_SCOPE_UNVERIFIED", result.reasons)

    def test_ephemeral_scope_needs_no_host_identity_claim(self):
        verifier = TestVerifier()
        scope = resolve_scope(project_id="vera", observed_at=NOW)
        result = good_preflight(verifier, scope=scope, scope_evidence=None)
        self.assertEqual(result.status, AnchorStatus.ANCHORED)

    def test_naive_now_fails_without_crash(self):
        verifier = TestVerifier()
        result = good_preflight(verifier, now=datetime(2026, 7, 30, 17, 5))
        self.assertIn("TRUSTED_NOW_INVALID", result.reasons)

    def test_inbox_must_be_checked_and_bound_to_rows(self):
        verifier = TestVerifier()
        self.assertIn("COORDINATION_INBOX_NOT_CHECKED", good_preflight(verifier, coordination_inbox_checked=False).reasons)
        event = CoordinationEvent("e1", 1, "t", Workstream.MEMORY, Workstream.TIME, "ISSUE", "READY", NOW)
        wrong_read = verifier.issue(
            EvidenceSystem.SUPABASE,
            "coordination_read_inbox",
            coordination_inbox_subject_hash(Workstream.TIME, ()),
        )
        result = good_preflight(verifier, coordination_events=(event,), coordination_read_evidence=wrong_read)
        self.assertIn("COORDINATION_INBOX_UNVERIFIED", result.reasons)

    def test_duplicate_coordination_sequence_conflicted(self):
        verifier = TestVerifier()
        events = (
            CoordinationEvent("e1", 1, "t", Workstream.MEMORY, Workstream.TIME, "ISSUE", "READY", NOW),
            CoordinationEvent("e2", 1, "t", Workstream.INITIATIVES, Workstream.TIME, "ISSUE", "READY", NOW),
        )
        result = good_preflight(verifier, coordination_events=events)
        self.assertIn("COORDINATION_SEQUENCE_CONFLICT", result.reasons)

    def test_only_addressed_events_returned(self):
        verifier = TestVerifier()
        events = (
            CoordinationEvent("e1", 1, "t", Workstream.MEMORY, Workstream.TIME, "ISSUE", "READY", NOW),
            CoordinationEvent("e2", 2, "t", Workstream.TIME, Workstream.INITIATIVES, "STATUS", "READY", NOW),
        )
        result = good_preflight(verifier, coordination_events=events)
        self.assertEqual([event.event_id for event in result.addressed_events], ["e1"])

    def test_retrieval_requires_bound_subject(self):
        verifier = TestVerifier()
        subject = canonical_subject_hash("retrieval", {"query": "latest anchor", "result": "anchor-1"})
        read = verifier.issue(EvidenceSystem.BASIC_MEMORY, "temporal_retrieval", subject)
        self.assertEqual(
            good_preflight(verifier, retrieval_required=True, retrieval_evidence=read, retrieval_subject_hash=subject).status,
            AnchorStatus.ANCHORED,
        )
        wrong = canonical_subject_hash("retrieval", {"query": "other"})
        self.assertIn(
            "TEMPORAL_RETRIEVAL_UNVERIFIED",
            good_preflight(verifier, retrieval_required=True, retrieval_evidence=read, retrieval_subject_hash=wrong).reasons,
        )

    def test_immutable_retrieval_rejects_basic_memory(self):
        verifier = TestVerifier()
        subject = canonical_subject_hash("retrieval", {"result": "anchor"})
        read = verifier.issue(EvidenceSystem.BASIC_MEMORY, "temporal_retrieval", subject)
        result = good_preflight(
            verifier,
            retrieval_required=True,
            retrieval_evidence=read,
            retrieval_subject_hash=subject,
            immutable_proof_required=True,
        )
        self.assertIn("TEMPORAL_RETRIEVAL_UNVERIFIED", result.reasons)

    def test_prior_anchor_must_be_verified_and_same_scope(self):
        verifier = TestVerifier()
        scope = stable_scope()
        anchor = make_anchor(verifier, scope)
        result = good_preflight(verifier, scope=scope, prior_anchor_required=True, prior_anchor=anchor)
        self.assertEqual(result.status, AnchorStatus.ANCHORED)
        forged_source = ExternalEvidence(
            EvidenceSystem.SUPABASE,
            "temporal_read",
            True,
            "forged",
            NOW,
            anchor.point.source.subject_hash,
            True,
        )
        forged_point = TemporalPoint(**{**anchor.point.__dict__, "source": forged_source})
        forged_anchor = TemporalAnchor("a2", "project/current-time", scope.scope_instance_id, AnchorStatus.ANCHORED, forged_point)
        self.assertIn(
            "PRIOR_ANCHOR_EVIDENCE_UNVERIFIED",
            good_preflight(verifier, scope=scope, prior_anchor=forged_anchor).reasons,
        )

    def test_old_event_fresh_record_not_stale(self):
        verifier = TestVerifier()
        scope = stable_scope()
        anchor = make_anchor(verifier, scope, when=NOW - timedelta(days=365), record_time=NOW - timedelta(minutes=1))
        result = good_preflight(verifier, scope=scope, prior_anchor=anchor)
        self.assertNotIn("PRIOR_ANCHOR_STALE", result.reasons)

    def test_old_record_is_stale(self):
        verifier = TestVerifier()
        scope = stable_scope()
        old = NOW - timedelta(days=31)
        anchor = make_anchor(verifier, scope, when=old, record_time=old)
        self.assertIn("PRIOR_ANCHOR_STALE", good_preflight(verifier, scope=scope, prior_anchor=anchor).reasons)

    def test_basic_memory_cannot_supply_trusted_now(self):
        verifier = TestVerifier()
        evidence = verifier.issue(EvidenceSystem.BASIC_MEMORY, "current_time", current_time_subject_hash(NOW))
        self.assertIn("TRUSTED_NOW_UNVERIFIED", good_preflight(verifier, now_evidence=evidence).reasons)

    def test_scope_evidence_for_different_scope_fails(self):
        verifier = TestVerifier()
        scope = stable_scope()
        other = resolve_scope(
            project_id="vera-reciprocal-agency-environment",
            observed_at=NOW,
            provider_conversation_id="conv-other",
            provider_branch_id="branch-other",
        )
        evidence = verifier.issue(EvidenceSystem.HOST, "resolve_scope", scope_subject_hash(other))
        self.assertIn("STABLE_SCOPE_UNVERIFIED", good_preflight(verifier, scope=scope, scope_evidence=evidence).reasons)

    def test_prior_anchor_scope_mismatch_fails(self):
        verifier = TestVerifier()
        scope = stable_scope()
        other = resolve_scope(
            project_id="vera-reciprocal-agency-environment",
            observed_at=NOW,
            provider_conversation_id="conv-other",
            provider_branch_id="branch-other",
        )
        anchor = make_anchor(verifier, other)
        self.assertIn("PRIOR_ANCHOR_SCOPE_MISMATCH", good_preflight(verifier, scope=scope, prior_anchor=anchor).reasons)

    def test_model_claim_never_promotes(self):
        verifier = TestVerifier()
        result = good_preflight(verifier, coordination_inbox_checked=False, model_claims=("I checked it",))
        self.assertEqual(result.status, AnchorStatus.UNANCHORED)
        self.assertIn("ignored", " ".join(result.limitations))


class PostflightTests(unittest.TestCase):
    def test_nonmaterial_turn_needs_no_write(self):
        verifier = TestVerifier()
        result = run_postflight(PostflightRequest(good_preflight(verifier), False), verifier)
        self.assertEqual(result.status, AnchorStatus.ANCHORED)

    def test_material_write_must_match_subject(self):
        verifier = TestVerifier()
        subject = canonical_subject_hash("transition", {"scope": "s", "decision": "d"})
        write = verifier.issue(EvidenceSystem.SUPABASE, "append_temporal_event", subject, immutable=True)
        result = run_postflight(PostflightRequest(good_preflight(verifier), True, subject, write), verifier)
        self.assertEqual(result.status, AnchorStatus.ANCHORED)
        wrong = canonical_subject_hash("transition", {"scope": "s", "decision": "other"})
        result = run_postflight(PostflightRequest(good_preflight(verifier), True, wrong, write), verifier)
        self.assertIn("MATERIAL_TRANSITION_NOT_PERSISTED", result.reasons)

    def test_model_claim_cannot_replace_write(self):
        verifier = TestVerifier()
        subject = canonical_subject_hash("transition", {"decision": "x"})
        result = run_postflight(
            PostflightRequest(good_preflight(verifier), True, subject, None, model_claims=("saved",)),
            verifier,
        )
        self.assertEqual(result.status, AnchorStatus.UNANCHORED)

    def test_memory_and_initiatives_handoffs_bound_to_target_payload(self):
        verifier = TestVerifier()
        memory_hash = canonical_subject_hash("handoff", {"target": Workstream.MEMORY, "decision": "d"})
        initiative_hash = canonical_subject_hash("handoff", {"target": Workstream.INITIATIVES, "decision": "d"})
        memory_write = verifier.issue(EvidenceSystem.SUPABASE, "coordination_post", memory_hash, immutable=True)
        initiative_write = verifier.issue(EvidenceSystem.SUPABASE, "coordination_post", initiative_hash, immutable=True)
        result = run_postflight(
            PostflightRequest(
                good_preflight(verifier),
                False,
                required_handoffs=(
                    RequiredHandoff(Workstream.MEMORY, memory_hash),
                    RequiredHandoff(Workstream.INITIATIVES, initiative_hash),
                ),
                handoff_evidence=(
                    HandoffEvidence(Workstream.MEMORY, memory_write),
                    HandoffEvidence(Workstream.INITIATIVES, initiative_write),
                ),
            ),
            verifier,
        )
        self.assertEqual(result.status, AnchorStatus.ANCHORED)

    def test_handoff_for_wrong_target_payload_fails(self):
        verifier = TestVerifier()
        memory_hash = canonical_subject_hash("handoff", {"target": Workstream.MEMORY})
        initiative_hash = canonical_subject_hash("handoff", {"target": Workstream.INITIATIVES})
        write = verifier.issue(EvidenceSystem.SUPABASE, "coordination_post", memory_hash, immutable=True)
        result = run_postflight(
            PostflightRequest(
                good_preflight(verifier),
                False,
                required_handoffs=(RequiredHandoff(Workstream.INITIATIVES, initiative_hash),),
                handoff_evidence=(HandoffEvidence(Workstream.INITIATIVES, write),),
            ),
            verifier,
        )
        self.assertIn("REQUIRED_HANDOFF_UNCONFIRMED:workstream/initiatives", result.reasons)

    def test_basic_memory_write_cannot_persist_material_transition(self):
        verifier = TestVerifier()
        subject = canonical_subject_hash("transition", {"decision": "x"})
        write = verifier.issue(EvidenceSystem.BASIC_MEMORY, "append_temporal_event", subject)
        result = run_postflight(PostflightRequest(good_preflight(verifier), True, subject, write), verifier)
        self.assertIn("MATERIAL_TRANSITION_NOT_PERSISTED", result.reasons)

    def test_duplicate_required_handoff_target_fails(self):
        verifier = TestVerifier()
        subject = canonical_subject_hash("handoff", {"target": Workstream.MEMORY})
        write = verifier.issue(EvidenceSystem.SUPABASE, "coordination_post", subject, immutable=True)
        result = run_postflight(
            PostflightRequest(
                good_preflight(verifier),
                False,
                required_handoffs=(
                    RequiredHandoff(Workstream.MEMORY, subject),
                    RequiredHandoff(Workstream.MEMORY, subject),
                ),
                handoff_evidence=(HandoffEvidence(Workstream.MEMORY, write),),
            ),
            verifier,
        )
        self.assertIn("DUPLICATE_REQUIRED_HANDOFF:workstream/memory", result.reasons)

    def test_unanchored_preflight_cannot_be_repaired(self):
        verifier = TestVerifier()
        preflight = good_preflight(verifier, coordination_inbox_checked=False)
        self.assertIn("PREFLIGHT_UNANCHORED", run_postflight(PostflightRequest(preflight, False), verifier).reasons)


class ElapsedTests(unittest.TestCase):
    def test_exact_elapsed(self):
        verifier = TestVerifier()
        start = make_point(verifier, scope_id="scope", when=NOW)
        end = make_point(verifier, scope_id="scope", when=NOW + timedelta(seconds=90))
        result = elapsed_between(start, end)
        self.assertEqual((result.status, result.best_seconds), (ElapsedStatus.EXACT, 90))

    def test_reversed_exact_conflicted(self):
        verifier = TestVerifier()
        start = make_point(verifier, scope_id="scope", when=NOW)
        end = make_point(verifier, scope_id="scope", when=NOW - timedelta(seconds=1))
        self.assertEqual(elapsed_between(start, end).status, ElapsedStatus.CONFLICTED)

    def test_overlapping_bounds_are_bounded_not_invented_conflict(self):
        verifier = TestVerifier()
        start = make_point(
            verifier,
            scope_id="scope",
            precision=TemporalPrecision.BOUNDED,
            when=NOW,
            lower=NOW - timedelta(seconds=10),
            upper=NOW + timedelta(seconds=10),
        )
        end = make_point(verifier, scope_id="scope", when=NOW + timedelta(seconds=5))
        result = elapsed_between(start, end)
        self.assertEqual(result.status, ElapsedStatus.BOUNDED)
        self.assertEqual((result.lower_seconds, result.upper_seconds), (0, 15))

    def test_fully_reversed_bounds_conflicted(self):
        verifier = TestVerifier()
        start = make_point(
            verifier,
            scope_id="scope",
            precision=TemporalPrecision.BOUNDED,
            when=NOW,
            lower=NOW - timedelta(seconds=1),
            upper=NOW + timedelta(seconds=1),
        )
        end = make_point(
            verifier,
            scope_id="scope",
            precision=TemporalPrecision.BOUNDED,
            when=NOW - timedelta(seconds=20),
            lower=NOW - timedelta(seconds=21),
            upper=NOW - timedelta(seconds=19),
        )
        self.assertEqual(elapsed_between(start, end).status, ElapsedStatus.CONFLICTED)

    def test_approximate_elapsed_remains_approximate(self):
        verifier = TestVerifier()
        start = make_point(verifier, scope_id="scope", when=NOW, precision=TemporalPrecision.APPROXIMATE)
        end = make_point(verifier, scope_id="scope", when=NOW + timedelta(seconds=5))
        self.assertEqual(elapsed_between(start, end).status, ElapsedStatus.APPROXIMATE)

    def test_unknown_unavailable_and_cross_scope_conflicted(self):
        verifier = TestVerifier()
        unknown = make_point(verifier, scope_id="scope", precision=TemporalPrecision.UNKNOWN)
        exact = make_point(verifier, scope_id="scope")
        self.assertEqual(elapsed_between(unknown, exact).status, ElapsedStatus.UNAVAILABLE)
        other = make_point(verifier, scope_id="other")
        self.assertEqual(elapsed_between(exact, other).status, ElapsedStatus.CONFLICTED)


if __name__ == "__main__":
    unittest.main()

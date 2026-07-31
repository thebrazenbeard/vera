from __future__ import annotations

from dataclasses import replace
import unittest

from coordination_bus import (
    ActorContext,
    CoordinationBus,
    CoordinationEventDraft,
    DecisionAuthorityEnvelope,
    HmacDecisionAuthority,
    InMemoryCoordinationRepository,
    PERMISSION_DECIDE,
    PERMISSION_POST,
    decision_subject,
)
from coordination_bus.contracts import ActorContext as CompatibilityActorContext


class StrictActorConstructionTests(unittest.TestCase):
    def test_obsolete_actor_route_is_rejected_at_construction(self):
        with self.assertRaisesRegex(ValueError, "obsolete route"):
            ActorContext("workstream/initiative", frozenset())

    def test_unknown_actor_route_is_rejected_at_construction(self):
        with self.assertRaisesRegex(ValueError, "unsupported workstream"):
            ActorContext("workstream/unknown", frozenset())

    def test_internal_compatibility_actor_cannot_bypass_public_bus(self):
        actor = CompatibilityActorContext(
            "workstream/initiative",
            frozenset({PERMISSION_POST}),
        )
        bus = CoordinationBus(InMemoryCoordinationRepository())
        result = bus.coordination_post(actor, status_draft())
        self.assertEqual(result.receipt.result_class, "INVALID")
        self.assertFalse(result.receipt.database_write_confirmed)


class DecisionAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryCoordinationRepository()
        self.authority = HmacDecisionAuthority("project-owner", b"d" * 32)
        self.actor = ActorContext(
            "workstream/project-architecture",
            frozenset({PERMISSION_DECIDE}),
        )
        self.draft = decision_draft()

    def bus(self) -> CoordinationBus:
        return CoordinationBus(
            self.repo,
            decision_authority_verifier=self.authority,
        )

    def envelope(self, draft: CoordinationEventDraft | None = None):
        subject = decision_subject(
            self.actor.canonical_workstream,
            draft or self.draft,
        )
        return self.authority.issue(subject=subject)

    def test_permission_without_external_authority_is_denied(self):
        result = CoordinationBus(self.repo).coordination_post(
            self.actor,
            self.draft,
        )
        self.assertEqual(result.receipt.result_class, "DENIED")
        self.assertFalse(result.receipt.database_write_confirmed)

    def test_exact_subject_authority_allows_one_decision(self):
        result = self.bus().coordination_post(
            self.actor,
            self.draft,
            decision_authority=self.envelope(),
        )
        self.assertEqual(result.receipt.result_class, "COMPLETE")
        self.assertTrue(result.receipt.database_write_confirmed)
        self.assertEqual(result.events[0].event_type, "DECISION")

    def test_authority_envelope_is_single_use(self):
        bus = self.bus()
        envelope = self.envelope()
        first = bus.coordination_post(
            self.actor,
            self.draft,
            decision_authority=envelope,
        )
        second = bus.coordination_post(
            self.actor,
            self.draft,
            decision_authority=envelope,
        )
        self.assertEqual(first.receipt.result_class, "COMPLETE")
        self.assertEqual(second.receipt.result_class, "DENIED")
        self.assertFalse(second.receipt.database_write_confirmed)

    def test_post_issuance_draft_change_is_denied(self):
        envelope = self.envelope()
        altered = replace(self.draft, summary="Changed after authority issuance.")
        result = self.bus().coordination_post(
            self.actor,
            altered,
            decision_authority=envelope,
        )
        self.assertEqual(result.receipt.result_class, "DENIED")
        self.assertFalse(result.receipt.database_write_confirmed)

    def test_wrong_actor_subject_is_denied(self):
        envelope = self.envelope()
        other = ActorContext(
            "workstream/integration",
            frozenset({PERMISSION_DECIDE}),
        )
        altered = replace(self.draft, source_branch="workstream/integration")
        result = self.bus().coordination_post(
            other,
            altered,
            decision_authority=envelope,
        )
        self.assertEqual(result.receipt.result_class, "DENIED")
        self.assertFalse(result.receipt.database_write_confirmed)

    def test_forged_token_is_denied(self):
        envelope = replace(self.envelope(), verification_token="0" * 64)
        result = self.bus().coordination_post(
            self.actor,
            self.draft,
            decision_authority=envelope,
        )
        self.assertEqual(result.receipt.result_class, "DENIED")
        self.assertFalse(result.receipt.database_write_confirmed)

    def test_unregistered_issuer_is_denied(self):
        foreign = HmacDecisionAuthority("foreign", b"f" * 32)
        envelope = foreign.issue(
            subject=decision_subject(self.actor.canonical_workstream, self.draft)
        )
        result = self.bus().coordination_post(
            self.actor,
            self.draft,
            decision_authority=envelope,
        )
        self.assertEqual(result.receipt.result_class, "DENIED")

    def test_authority_on_nondecision_is_invalid_and_writes_nothing(self):
        result = self.bus().coordination_post(
            ActorContext("workstream/memory", frozenset({PERMISSION_POST})),
            status_draft(),
            decision_authority=self.envelope(),
        )
        self.assertEqual(result.receipt.result_class, "INVALID")
        self.assertFalse(result.receipt.database_write_confirmed)

    def test_malformed_envelope_type_is_denied(self):
        result = self.bus().coordination_post(
            self.actor,
            self.draft,
            decision_authority=DecisionAuthorityEnvelope(
                schema="WRONG",
                issuer_id="project-owner",
                subject=decision_subject(self.actor.canonical_workstream, self.draft),
                nonce="nonce",
                verification_token="0" * 64,
            ),
        )
        self.assertEqual(result.receipt.result_class, "DENIED")


def decision_draft() -> CoordinationEventDraft:
    return CoordinationEventDraft(
        thread_key="project-merge-decision-v1",
        source_branch="workstream/project-architecture",
        target_branch="workstream/integration",
        event_type="DECISION",
        status="APPROVED",
        objective="Authorize one bounded project decision",
        summary="Exact subject-bound external authority is required.",
        payload={"merge_authorized": False},
        reference_data={"pull_request": 8},
    )


def status_draft() -> CoordinationEventDraft:
    return CoordinationEventDraft(
        thread_key="ordinary-status-v1",
        source_branch="workstream/memory",
        target_branch="workstream/integration",
        event_type="STATUS",
        status="IN_PROGRESS",
        objective="Publish ordinary status",
        summary="No decision authority belongs on this operation.",
    )


if __name__ == "__main__":
    unittest.main()

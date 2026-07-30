from __future__ import annotations

from dataclasses import replace
import unittest

from coordination_bus import (
    ALL_PERMISSIONS,
    ActorContext,
    CoordinationBus,
    CoordinationEventDraft,
    HmacTemporalEvidenceAuthority,
    InMemoryCoordinationRepository,
    TemporalEvidence,
    acknowledgement_subject,
    entry_checkpoint_subject,
    exit_checkpoint_subject,
)


T0 = "2026-07-30T22:40:00+00:00"
T1 = "2026-07-30T22:40:01+00:00"


def exact(value: str, label: str) -> TemporalEvidence:
    return TemporalEvidence.exact(
        value,
        source="HOST_CLOCK",
        reference_id=f"clock:{label}:{value}",
    )


class TemporalEvidenceTrustTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryCoordinationRepository()
        self.authority = HmacTemporalEvidenceAuthority(
            "test-host-clock", b"v" * 32
        )
        self.bus = CoordinationBus(
            self.repo,
            evidence_verifier=self.authority,
            receipt_time_provider=lambda role, subject: self.authority.issue(
                exact(T1, "receipt"), role=role, subject=subject
            ),
        )
        self.memory = ActorContext("workstream/memory", ALL_PERMISSIONS)
        self.time = ActorContext("workstream/time", ALL_PERMISSIONS)
        self.integration = ActorContext(
            "workstream/integration", ALL_PERMISSIONS
        )

    def post_to_time(self):
        return self.bus.coordination_post(
            self.memory,
            CoordinationEventDraft(
                thread_key="trust-boundary",
                source_branch="workstream/memory",
                target_branch="workstream/time",
                event_type="STATUS",
                status="IN_PROGRESS",
                objective="Test temporal trust boundary",
                summary="Bounded test event.",
            ),
        ).events[0]

    def test_raw_self_certified_host_time_is_rejected(self):
        result = self.bus.entry_checkpoint(
            self.time,
            entry_time=exact(T0, "forged-raw"),
        )
        self.assertEqual(result.receipt.result_class, "INVALID")
        self.assertIn("verifier-issued", result.receipt.error)

    def test_valid_role_and_subject_bound_envelope_is_accepted(self):
        subject = entry_checkpoint_subject("workstream/time", 0, 100)
        envelope = self.authority.issue(
            exact(T0, "entry"),
            role="entry_time",
            subject=subject,
        )
        result = self.bus.entry_checkpoint(
            self.time,
            entry_time=envelope,
        )
        self.assertEqual(result.receipt.result_class, "COMPLETE")
        self.assertEqual(result.receipt.entry_time.value, T0)

    def test_forged_token_is_rejected(self):
        subject = entry_checkpoint_subject("workstream/time", 0, 100)
        envelope = self.authority.issue(
            exact(T0, "entry"),
            role="entry_time",
            subject=subject,
        )
        forged = replace(envelope, verification_token="0" * 64)
        result = self.bus.entry_checkpoint(
            self.time,
            entry_time=forged,
        )
        self.assertEqual(result.receipt.result_class, "INVALID")

    def test_wrong_role_binding_is_rejected(self):
        subject = entry_checkpoint_subject("workstream/time", 0, 100)
        envelope = self.authority.issue(
            exact(T0, "wrong-role"),
            role="state_time",
            subject=subject,
        )
        result = self.bus.entry_checkpoint(
            self.time,
            entry_time=envelope,
        )
        self.assertEqual(result.receipt.result_class, "INVALID")

    def test_wrong_subject_binding_is_rejected(self):
        envelope = self.authority.issue(
            exact(T0, "wrong-subject"),
            role="entry_time",
            subject=entry_checkpoint_subject("workstream/memory", 0, 100),
        )
        result = self.bus.entry_checkpoint(
            self.time,
            entry_time=envelope,
        )
        self.assertEqual(result.receipt.result_class, "INVALID")

    def test_modified_claim_invalidates_token(self):
        subject = entry_checkpoint_subject("workstream/time", 0, 100)
        envelope = self.authority.issue(
            exact(T0, "entry"),
            role="entry_time",
            subject=subject,
        )
        modified = replace(
            envelope,
            evidence=exact(T1, "modified-after-issuance"),
        )
        result = self.bus.entry_checkpoint(
            self.time,
            entry_time=modified,
        )
        self.assertEqual(result.receipt.result_class, "INVALID")

    def test_acknowledgement_evidence_is_bound_to_event(self):
        event = self.post_to_time()
        envelope = self.authority.issue(
            exact(T0, "ack"),
            role="acknowledgement_time",
            subject=acknowledgement_subject(event.event_id),
        )
        result = self.bus.coordination_acknowledge(
            self.time,
            event_id=event.event_id,
            summary="Acknowledged.",
            acknowledgement_time=envelope,
        )
        self.assertEqual(result.receipt.result_class, "COMPLETE")
        self.assertEqual(
            result.events[0].payload["temporal"]["consumption_time"]["precision"],
            "UNKNOWN",
        )

    def test_exit_evidence_is_bound_to_transition_subject(self):
        subject = exit_checkpoint_subject(
            "workstream/integration", "handoff", "workstream/time"
        )
        event_envelope = self.authority.issue(
            exact(T0, "exit-event"),
            role="event_time",
            subject=subject,
        )
        state_envelope = self.authority.issue(
            exact(T1, "exit-state"),
            role="state_time",
            subject=subject,
        )
        result = self.bus.exit_checkpoint(
            self.integration,
            thread_key="handoff",
            target_branch="workstream/time",
            objective="Publish handoff",
            summary="Handoff ready.",
            material=True,
            event_time=event_envelope,
            state_time=state_envelope,
        )
        self.assertEqual(result.receipt.result_class, "COMPLETE")
        self.assertEqual(
            result.events[0].payload["temporal"]["event_time"]["value"], T0
        )

    def test_unverified_receipt_provider_fails_closed_to_unknown(self):
        bus = CoordinationBus(
            self.repo,
            evidence_verifier=self.authority,
            receipt_time_provider=lambda role, subject: exact(T1, "raw-receipt"),
        )
        result = bus.entry_checkpoint(self.time)
        self.assertEqual(
            result.receipt.receipt_time.precision,
            "UNKNOWN",
        )
        self.assertEqual(
            result.receipt.receipt_time.source,
            "UNVERIFIED_RECEIPT_TIME_REJECTED",
        )


if __name__ == "__main__":
    unittest.main()

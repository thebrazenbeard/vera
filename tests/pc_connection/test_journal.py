from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from pc_connection.journal import (
    AttemptIdentity,
    JobJournal,
    JournalConflict,
    JournalCorrupt,
    JournalState,
    JournalStateError,
    VerifiedJournalPath,
)


def identity(**changes) -> AttemptIdentity:
    values = {
        "job_id": "00000000-0000-7000-8000-000000000101",
        "attempt_id": "00000000-0000-7000-8000-000000000102",
        "host_id": "00000000-0000-7000-8000-000000000103",
        "claim_generation": 1,
        "lease_id": "00000000-0000-7000-8000-000000000104",
        "lease_fence": 1,
        "job_digest": "1" * 64,
        "authorization_id": "00000000-0000-7000-8000-000000000105",
        "authorization_revision": 1,
        "issuer_revocation_epoch": 0,
        "host_revocation_epoch": 0,
        "operation_id": "PING",
        "operation_version": 1,
        "retry_class": "PURE_READ",
        "side_effect_class": "NONE",
    }
    values.update(changes)
    return AttemptIdentity(**values)


def event(number: int) -> dict:
    return {
        "local_event_id": (
            f"00000000-0000-7000-8000-{number:012d}"
        ),
        "payload_digest": f"{number % 10}" * 64,
        "server_time_anchor": "2026-08-01T20:00:00.000000Z",
        "local_monotonic_ns": number,
        "record_time": (
            f"2026-08-01T20:00:{number:02d}.000000Z"
        ),
    }


class JobJournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        verified = VerifiedJournalPath.for_test(
            Path(self.tempdir.name)
        )
        self.journal = JobJournal(verified)
        self.identity = identity()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_arbitrary_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(Exception, "VerifiedJournalPath"):
            JobJournal(Path(self.tempdir.name) / "other.db")  # type: ignore[arg-type]

    def test_exact_claim_replay_is_idempotent(self) -> None:
        first = self.journal.record_claim(
            self.identity,
            **event(1),
        )
        second = self.journal.record_claim(
            self.identity,
            **event(2),
        )
        self.assertEqual(first, second)
        self.assertEqual(first.local_state, JournalState.CLAIMED)
        self.assertEqual(first.state_version, 1)

    def test_changed_attempt_identity_conflicts(self) -> None:
        self.journal.record_claim(self.identity, **event(1))
        changed = identity(lease_fence=2)
        with self.assertRaisesRegex(
            JournalConflict,
            "IDENTITY_CONFLICT",
        ):
            self.journal.record_claim(changed, **event(2))

    def test_side_effect_free_result_path(self) -> None:
        projection = self.journal.record_claim(
            self.identity,
            **event(1),
        )
        projection = self.journal.start_preparation(
            self.identity,
            **event(2),
        )
        projection = self.journal.record_result(
            self.identity,
            result_digest="a" * 64,
            **event(3),
        )
        self.assertEqual(
            projection.local_state,
            JournalState.RESULT_OBSERVED,
        )
        projection = self.journal.submit_completion(
            self.identity,
            receipt_id="00000000-0000-7000-8000-000000000106",
            receipt_digest="b" * 64,
            server_request_id=(
                "00000000-0000-7000-8000-000000000107"
            ),
            **event(4),
        )
        self.assertEqual(
            projection.local_state,
            JournalState.COMPLETING,
        )
        projection = self.journal.confirm_terminal_readback(
            self.identity,
            server_readback_receipt_id=(
                "00000000-0000-7000-8000-000000000108"
            ),
            server_readback_digest="c" * 64,
            expected_result_digest="a" * 64,
            expected_receipt_digest="b" * 64,
            **event(5),
        )
        self.assertEqual(
            projection.local_state,
            JournalState.TERMINAL_CONFIRMED,
        )

    def test_terminal_confirmation_requires_exact_readback(self) -> None:
        self.journal.record_claim(self.identity, **event(1))
        self.journal.start_preparation(self.identity, **event(2))
        self.journal.record_result(
            self.identity,
            result_digest="a" * 64,
            **event(3),
        )
        self.journal.submit_completion(
            self.identity,
            receipt_id="00000000-0000-7000-8000-000000000106",
            receipt_digest="b" * 64,
            server_request_id=(
                "00000000-0000-7000-8000-000000000107"
            ),
            **event(4),
        )
        with self.assertRaisesRegex(
            JournalConflict,
            "SERVER_DIVERGENCE",
        ):
            self.journal.confirm_terminal_readback(
                self.identity,
                server_readback_receipt_id=(
                    "00000000-0000-7000-8000-000000000108"
                ),
                server_readback_digest="c" * 64,
                expected_result_digest="d" * 64,
                expected_receipt_digest="b" * 64,
                **event(5),
            )
        self.assertEqual(
            self.journal.get(
                self.identity.job_id,
                self.identity.attempt_id,
            ).local_state,
            JournalState.COMPLETING,
        )

    def test_effect_start_is_unreachable_for_enabled_phase_one(self) -> None:
        self.journal.record_claim(self.identity, **event(1))
        self.journal.start_preparation(self.identity, **event(2))
        with self.assertRaisesRegex(
            JournalStateError,
            "side-effect-free",
        ):
            self.journal.commit_effect_start(
                self.identity,
                **event(3),
            )

    def test_restart_returns_incomplete_attempt_without_replay(self) -> None:
        self.journal.record_claim(self.identity, **event(1))
        self.journal.start_preparation(self.identity, **event(2))
        reopened = JobJournal(self.journal.verified_path)
        incomplete = reopened.recover_incomplete()
        self.assertEqual(len(incomplete), 1)
        self.assertEqual(
            incomplete[0].local_state,
            JournalState.PREPARING,
        )

    def test_event_tampering_is_detected_on_restart(self) -> None:
        self.journal.record_claim(self.identity, **event(1))
        with sqlite3.connect(self.journal.path) as connection:
            connection.execute(
                "UPDATE pccc_local_events SET payload_digest=?",
                ("e" * 64,),
            )
            connection.commit()
        with self.assertRaisesRegex(
            JournalCorrupt,
            "EVENT_CHAIN_INVALID",
        ):
            JobJournal(self.journal.verified_path)


if __name__ == "__main__":
    unittest.main()

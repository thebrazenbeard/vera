from __future__ import annotations

import math
from pathlib import Path
import tempfile
import unittest

from pc_connection.journal import (
    JobJournal,
    JournalConflict,
    JournalError,
    JournalStateError,
)

JOB_ID = "66666666-6666-4666-8666-666666666666"
DIGEST = "d" * 64


class JobJournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "state" / "journal.db"
        self.journal = JobJournal(self.path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_identical_begin_is_idempotent(self) -> None:
        first = self.journal.begin(JOB_ID, DIGEST)
        second = self.journal.begin(JOB_ID, DIGEST)
        self.assertEqual(first.job_id, second.job_id)
        self.assertEqual(first.state, "RECEIVED")
        self.assertEqual(second.state, "RECEIVED")

    def test_changed_digest_conflicts(self) -> None:
        self.journal.begin(JOB_ID, DIGEST)
        with self.assertRaisesRegex(JournalConflict, "changed"):
            self.journal.begin(JOB_ID, "e" * 64)

    def test_effect_started_is_idempotent(self) -> None:
        self.journal.begin(JOB_ID, DIGEST)
        first = self.journal.mark_effect_started(JOB_ID, DIGEST)
        second = self.journal.mark_effect_started(JOB_ID, DIGEST)
        self.assertEqual(first.state, "EFFECT_STARTED")
        self.assertEqual(second.state, "EFFECT_STARTED")

    def test_effect_started_requires_existing_job(self) -> None:
        with self.assertRaisesRegex(JournalStateError, "journaled"):
            self.journal.mark_effect_started(JOB_ID, DIGEST)

    def test_terminal_exact_retry_returns_stored_result(self) -> None:
        self.journal.begin(JOB_ID, DIGEST)
        receipt = {"result": "ok", "sequence": 7}
        first = self.journal.record_terminal(
            JOB_ID,
            DIGEST,
            "COMPLETE",
            receipt,
        )
        second = self.journal.record_terminal(
            JOB_ID,
            DIGEST,
            "COMPLETE",
            receipt,
        )
        self.assertEqual(first, second)
        self.assertEqual(first.receipt, receipt)

    def test_terminal_divergence_conflicts(self) -> None:
        self.journal.begin(JOB_ID, DIGEST)
        self.journal.record_terminal(
            JOB_ID,
            DIGEST,
            "COMPLETE",
            {"result": "first"},
        )
        with self.assertRaisesRegex(JournalConflict, "differs"):
            self.journal.record_terminal(
                JOB_ID,
                DIGEST,
                "FAILED",
                {"result": "second"},
            )

    def test_nonfinite_receipt_is_rejected(self) -> None:
        self.journal.begin(JOB_ID, DIGEST)
        with self.assertRaisesRegex(JournalError, "canonical JSON"):
            self.journal.record_terminal(
                JOB_ID,
                DIGEST,
                "FAILED",
                {"value": math.nan},
            )

    def test_recovery_does_not_replay_incomplete_effect(self) -> None:
        other = "77777777-7777-4777-8777-777777777777"
        self.journal.begin(JOB_ID, DIGEST)
        self.journal.begin(other, "e" * 64)
        self.journal.mark_effect_started(other, "e" * 64)
        incomplete = self.journal.recover_incomplete()
        self.assertEqual(
            [(job.job_id, job.state) for job in incomplete],
            [(JOB_ID, "RECEIVED"), (other, "EFFECT_STARTED")],
        )

    def test_terminal_job_is_not_recovered_as_incomplete(self) -> None:
        self.journal.begin(JOB_ID, DIGEST)
        self.journal.record_terminal(
            JOB_ID,
            DIGEST,
            "CANCELLED",
            {"cancelled": True},
        )
        self.assertEqual(self.journal.recover_incomplete(), ())

    def test_boolean_or_malformed_identity_is_rejected(self) -> None:
        with self.assertRaisesRegex(JournalError, "UUID"):
            self.journal.begin("not-a-uuid", DIGEST)
        with self.assertRaisesRegex(JournalError, "SHA-256"):
            self.journal.begin(JOB_ID, "D" * 64)


if __name__ == "__main__":
    unittest.main()

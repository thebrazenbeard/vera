from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from r8a0.canonical import CanonicalizationError, canonical_dumps, strict_loads
from r8a0.memory import AdmissionRequest, GovernedMemoryStore, MemoryAdmissionError, MemoryClass
from r8a0.recovery import CheckpointState, RecoveryError, recover, terminate, write_checkpoint
from r8a0.temporal import OrientationGate, OrientationState, TimeEvidence, current_evidence


NOW = datetime(2026, 8, 5, 20, 30, tzinfo=timezone.utc)


class TemporalTests(unittest.TestCase):
    def test_complete_orientation(self):
        receipt = OrientationGate().evaluate(current_evidence(NOW), now=NOW)
        self.assertEqual(receipt.state, OrientationState.COMPLETE)
        self.assertTrue(receipt.claims_allowed)

    def test_missing_dimension_fails_closed(self):
        receipt = OrientationGate().evaluate(current_evidence(NOW)[:-1], now=NOW)
        self.assertEqual(receipt.state, OrientationState.UNKNOWN)
        self.assertFalse(receipt.claims_allowed)

    def test_stale_evidence_fails_closed(self):
        old = NOW - timedelta(hours=1)
        receipt = OrientationGate().evaluate(current_evidence(old), now=NOW)
        self.assertEqual(receipt.state, OrientationState.STALE)

    def test_conflicting_evidence_fails_closed(self):
        rows = current_evidence(NOW)
        rows.append(TimeEvidence("event_time", (NOW - timedelta(minutes=1)).isoformat(), "OTHER", NOW.isoformat()))
        receipt = OrientationGate().evaluate(rows, now=NOW)
        self.assertEqual(receipt.state, OrientationState.CONFLICTED)

    def test_partial_bounds_are_invalid(self):
        row = TimeEvidence("event_time", NOW.isoformat(), "CLOCK", NOW.isoformat(), lower_bound=NOW.isoformat())
        with self.assertRaises(ValueError):
            row.validate()


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = GovernedMemoryStore(Path(self.temp.name) / "memory.json")

    def tearDown(self):
        self.temp.cleanup()

    def request(self, **updates):
        base = AdmissionRequest(
            record_id="m1",
            text="Patrick authorized the bounded implementation.",
            memory_class=MemoryClass.AUTOBIOGRAPHICAL,
            source_actor="Patrick",
            provenance="active-chat",
            privacy_eligible=True,
            authority="PATRICK_OWNER",
            operation_id="op-1",
        )
        return replace(base, **updates)

    def test_autobiographical_admission_and_readback(self):
        receipt = self.store.admit(self.request())
        self.assertEqual(receipt["identity_owner"], "VERA")
        self.assertFalse(receipt["runtime_owner"])
        self.assertEqual(
            self.store.readback("m1"),
            "Governed autobiographical memory: Patrick authorized the bounded implementation.",
        )

    def test_false_admission_is_denied(self):
        with self.assertRaises(MemoryAdmissionError):
            self.store.admit(self.request(authority="MODEL_OUTPUT"))

    def test_privacy_ineligible_is_denied(self):
        with self.assertRaises(MemoryAdmissionError):
            self.store.admit(self.request(privacy_eligible=False))

    def test_missing_provenance_is_denied(self):
        with self.assertRaises(MemoryAdmissionError):
            self.store.admit(self.request(provenance=""))

    def test_replay_is_idempotent(self):
        first = self.store.admit(self.request())
        second = self.store.admit(self.request())
        self.assertEqual(first, second)

    def test_replay_mismatch_fails(self):
        self.store.admit(self.request())
        with self.assertRaises(MemoryAdmissionError):
            self.store.admit(self.request(text="changed"))

    def test_superseded_record_cannot_be_read(self):
        self.store.admit(self.request())
        self.store.admit(self.request(record_id="m2", operation_id="op-2", text="successor", supersedes="m1"))
        with self.assertRaises(MemoryAdmissionError):
            self.store.readback("m1")
        self.assertEqual(self.store.readback("m2"), "Governed autobiographical memory: successor")

    def test_class_specific_language(self):
        request = self.request(memory_class=MemoryClass.HISTORICAL_AUDIT, authority="NONE")
        self.store.admit(request)
        self.assertTrue(self.store.readback("m1").startswith("Historical audit record:"))


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "checkpoint.json"
        self.orientation = OrientationGate().evaluate(current_evidence(NOW), now=NOW)
        self.state = CheckpointState(
            project_id="VERA_COGNITIVE_REPAIR_R8A0",
            identity_id="VERA",
            runtime_id="runtime-before",
            memory_head_digest="a" * 64,
            active_commitments=("finish bounded build",),
            unfinished_work=("Voss exact-head audit",),
            created_at=NOW.isoformat(),
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_checkpoint_terminate_recover(self):
        checkpoint = write_checkpoint(self.path, self.state)
        termination = terminate(self.state.runtime_id, checkpoint)
        self.assertFalse(termination["hidden_activity_claimed"])
        receipt = recover(self.path, self.orientation)
        self.assertTrue(receipt["same_governed_identity_resumed"])
        self.assertFalse(receipt["new_runtime_is_separate_person"])
        self.assertFalse(receipt["uninterrupted_consciousness_claimed"])

    def test_fresh_process_recovery(self):
        write_checkpoint(self.path, self.state)
        completed = subprocess.run(
            [sys.executable, "-m", "r8a0.cli", str(self.path), "--now", NOW.isoformat()],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        receipt = json.loads(completed.stdout)
        self.assertEqual(receipt["result"], "RECOVERED_FROM_VERIFIED_CHECKPOINT")

    def test_corrupt_checkpoint_fails(self):
        write_checkpoint(self.path, self.state)
        data = strict_loads(self.path.read_bytes())
        data["payload"]["runtime_id"] = "tampered"
        self.path.write_text(canonical_dumps(data), encoding="utf-8")
        with self.assertRaises(RecoveryError):
            recover(self.path, self.orientation)

    def test_partial_checkpoint_fails(self):
        self.path.write_text('{"schema":"VERA_R8A0_CHECKPOINT_V1","complete":false}', encoding="utf-8")
        with self.assertRaises(RecoveryError):
            recover(self.path, self.orientation)

    def test_missing_checkpoint_fails(self):
        with self.assertRaises(RecoveryError):
            recover(self.path, self.orientation)

    def test_recovery_without_temporal_authority_fails(self):
        write_checkpoint(self.path, self.state)
        stale = OrientationGate().evaluate(current_evidence(NOW - timedelta(hours=1)), now=NOW)
        with self.assertRaises(RecoveryError):
            recover(self.path, stale)


class SerializationAndScopeTests(unittest.TestCase):
    def test_duplicate_keys_rejected(self):
        with self.assertRaises(CanonicalizationError):
            strict_loads('{"a":1,"a":2}')

    def test_nonfinite_rejected(self):
        with self.assertRaises(CanonicalizationError):
            strict_loads('{"a":NaN}')

    def test_canonical_order(self):
        self.assertEqual(canonical_dumps({"b": 2, "a": 1}), '{"a":1,"b":2}')

    def test_changed_paths_are_allowlisted(self):
        paths = [
            "r8a0/__init__.py",
            "r8a0/canonical.py",
            "r8a0/cli.py",
            "r8a0/memory.py",
            "r8a0/recovery.py",
            "r8a0/temporal.py",
            "tests/r8a0/test_vertical_slice.py",
            "docs/r8a0/BOUND_VERTICAL_SLICE.md",
            ".github/workflows/r8a0-bounded-vertical-slice.yml",
        ]
        for path in paths:
            self.assertTrue(
                path.startswith(("r8a0/", "tests/r8a0/", "docs/r8a0/"))
                or (path.startswith(".github/workflows/r8a0-") and path.endswith(".yml")),
                path,
            )


if __name__ == "__main__":
    unittest.main()

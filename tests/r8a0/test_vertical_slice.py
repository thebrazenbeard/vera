from __future__ import annotations

import hashlib
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
from r8a0.temporal import (
    CURRENT_TIME,
    REQUIRED_DIMENSIONS,
    OrientationGate,
    OrientationState,
    TimeEvidence,
    current_evidence,
)


NOW = datetime(2026, 8, 5, 20, 30, tzinfo=timezone.utc)


def sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def complete_time_evidence(at: datetime = NOW) -> list[TimeEvidence]:
    value = at.isoformat()
    rows = current_evidence(at, source_digest=sha("wall-clock"))
    for dimension in REQUIRED_DIMENSIONS:
        if dimension == CURRENT_TIME:
            continue
        rows.append(
            TimeEvidence(
                dimension=dimension,
                value=value,
                source=f"VERIFIED_{dimension.upper()}_SOURCE",
                source_kind=dimension,
                observed_at=value,
                source_digest=sha(dimension),
            )
        )
    return rows


class TemporalTests(unittest.TestCase):
    def test_complete_orientation_from_separate_sources(self):
        receipt = OrientationGate().evaluate(complete_time_evidence(), now=NOW)
        self.assertEqual(receipt.state, OrientationState.COMPLETE)
        self.assertTrue(receipt.claims_allowed)
        self.assertEqual(len(REQUIRED_DIMENSIONS), 7)

    def test_wall_clock_helper_cannot_fabricate_semantic_times(self):
        receipt = OrientationGate().evaluate(
            current_evidence(NOW, source_digest=sha("wall-clock")),
            now=NOW,
        )
        self.assertEqual(receipt.state, OrientationState.UNKNOWN)
        self.assertEqual(set(receipt.missing_dimensions), set(REQUIRED_DIMENSIONS) - {CURRENT_TIME})

    def test_wrong_semantic_source_kind_fails_closed(self):
        rows = complete_time_evidence()
        rows[1] = replace(rows[1], source_kind=CURRENT_TIME)
        receipt = OrientationGate().evaluate(rows, now=NOW)
        self.assertEqual(receipt.state, OrientationState.UNKNOWN)
        self.assertIn(rows[1].dimension, receipt.invalid_dimensions)

    def test_missing_dimension_fails_closed(self):
        receipt = OrientationGate().evaluate(complete_time_evidence()[:-1], now=NOW)
        self.assertEqual(receipt.state, OrientationState.UNKNOWN)
        self.assertFalse(receipt.claims_allowed)

    def test_stale_evidence_fails_closed(self):
        old = NOW - timedelta(hours=1)
        receipt = OrientationGate().evaluate(complete_time_evidence(old), now=NOW)
        self.assertEqual(receipt.state, OrientationState.STALE)

    def test_conflicting_evidence_fails_closed(self):
        rows = complete_time_evidence()
        rows.append(
            TimeEvidence(
                "event_time",
                (NOW - timedelta(minutes=1)).isoformat(),
                "OTHER_EVENT_SOURCE",
                "event_time",
                NOW.isoformat(),
                sha("other-event"),
            )
        )
        receipt = OrientationGate().evaluate(rows, now=NOW)
        self.assertEqual(receipt.state, OrientationState.CONFLICTED)

    def test_partial_bounds_are_invalid(self):
        row = TimeEvidence(
            "event_time",
            NOW.isoformat(),
            "EVENT_SOURCE",
            "event_time",
            NOW.isoformat(),
            sha("event"),
            lower_bound=NOW.isoformat(),
        )
        with self.assertRaises(ValueError):
            row.validate()

    def test_snapshot_requires_bounds_for_every_dimension(self):
        receipt = OrientationGate().evaluate(
            complete_time_evidence(),
            now=NOW,
            source_mode="FRESH_BOUND_SNAPSHOT",
        )
        self.assertEqual(receipt.state, OrientationState.UNKNOWN)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "memory.json"

    def tearDown(self):
        self.temp.cleanup()

    def request(self, **updates) -> AdmissionRequest:
        base = AdmissionRequest(
            record_id="m1",
            text="Patrick authorized the bounded implementation.",
            memory_class=MemoryClass.AUTOBIOGRAPHICAL,
            source_actor="Patrick",
            provenance="active-chat",
            operation_id="op-1",
            authority_binding_id="auth-1",
            privacy_binding_id="privacy-1",
        )
        return replace(base, **updates)

    def store_for(
        self,
        *requests: AdmissionRequest,
        authority_decision: str = "AUTHORIZED",
        privacy_decision: str = "ELIGIBLE",
    ) -> GovernedMemoryStore:
        authority = {}
        privacy = {}
        for request in requests:
            authority[request.authority_binding_id] = {
                "binding_id": request.authority_binding_id,
                "request_digest": request.request_digest(),
                "source": "VERIFIED_OWNER_AUTHORITY_REGISTRY",
                "source_digest": sha(f"authority:{request.authority_binding_id}"),
                "decision": authority_decision,
            }
            privacy[request.privacy_binding_id] = {
                "binding_id": request.privacy_binding_id,
                "request_digest": request.request_digest(),
                "source": "VERIFIED_PRIVACY_REGISTRY",
                "source_digest": sha(f"privacy:{request.privacy_binding_id}"),
                "decision": privacy_decision,
            }
        return GovernedMemoryStore(
            self.path,
            authority_registry=authority,
            privacy_registry=privacy,
        )

    def test_autobiographical_admission_and_exact_readback(self):
        request = self.request()
        store = self.store_for(request)
        receipt = store.admit(request)
        self.assertEqual(receipt["identity_owner"], "VERA")
        self.assertFalse(receipt["runtime_owner"])
        self.assertEqual(
            store.readback("m1"),
            "I remember this through my persistent memory. Patrick authorized the bounded implementation.",
        )

    def test_exact_working_project_language(self):
        request = self.request(memory_class=MemoryClass.WORKING_PROJECT)
        store = self.store_for(request)
        store.admit(request)
        self.assertEqual(
            store.readback("m1"),
            "I have this in my working or project memory. Patrick authorized the bounded implementation.",
        )

    def test_exact_historical_audit_language(self):
        request = self.request(memory_class=MemoryClass.HISTORICAL_AUDIT)
        store = self.store_for(request)
        store.admit(request)
        self.assertEqual(
            store.readback("m1"),
            "The historical or audit record shows this. Patrick authorized the bounded implementation.",
        )

    def test_unknown_authority_binding_is_denied(self):
        request = self.request()
        store = GovernedMemoryStore(self.path, authority_registry={}, privacy_registry={})
        with self.assertRaises(MemoryAdmissionError):
            store.admit(request)

    def test_authority_binding_must_match_exact_request(self):
        request = self.request()
        store = self.store_for(request)
        changed = replace(request, text="changed after authorization")
        with self.assertRaises(MemoryAdmissionError):
            store.admit(changed)

    def test_denied_authority_is_denied(self):
        request = self.request()
        store = self.store_for(request, authority_decision="DENIED")
        with self.assertRaises(MemoryAdmissionError):
            store.admit(request)

    def test_privacy_ineligible_binding_is_denied(self):
        request = self.request()
        store = self.store_for(request, privacy_decision="INELIGIBLE")
        with self.assertRaises(MemoryAdmissionError):
            store.admit(request)

    def test_missing_provenance_is_denied(self):
        request = self.request(provenance="")
        store = self.store_for(request)
        with self.assertRaises(MemoryAdmissionError):
            store.admit(request)

    def test_replay_is_idempotent(self):
        request = self.request()
        store = self.store_for(request)
        first = store.admit(request)
        second = store.admit(request)
        self.assertEqual(first, second)

    def test_replay_mismatch_fails(self):
        request = self.request()
        store = self.store_for(request)
        store.admit(request)
        changed = self.request(text="changed")
        with self.assertRaises(MemoryAdmissionError):
            store.admit(changed)

    def test_revoked_authority_fails_readback(self):
        request = self.request()
        store = self.store_for(request)
        store.admit(request)
        store.authority_registry["auth-1"]["decision"] = "REVOKED"
        with self.assertRaisesRegex(MemoryAdmissionError, "authority binding denies admission"):
            store.readback("m1")

    def test_privacy_revocation_fails_readback(self):
        request = self.request()
        store = self.store_for(request)
        store.admit(request)
        store.privacy_registry["privacy-1"]["decision"] = "INELIGIBLE"
        with self.assertRaisesRegex(MemoryAdmissionError, "privacy binding denies admission"):
            store.readback("m1")

    def test_tampered_stored_text_fails_readback(self):
        request = self.request()
        store = self.store_for(request)
        store.admit(request)
        data = strict_loads(self.path.read_bytes())
        data["records"][0]["text"] = "tampered autobiography"
        self.path.write_text(canonical_dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(MemoryAdmissionError, "record digest mismatch"):
            store.readback("m1")

    def test_superseded_record_cannot_be_read(self):
        first = self.request()
        second = self.request(
            record_id="m2",
            operation_id="op-2",
            text="successor",
            authority_binding_id="auth-2",
            privacy_binding_id="privacy-2",
            supersedes="m1",
        )
        store = self.store_for(first, second)
        store.admit(first)
        store.admit(second)
        with self.assertRaises(MemoryAdmissionError):
            store.readback("m1")
        self.assertEqual(store.readback("m2"), "I remember this through my persistent memory. successor")

    def test_supersession_lifecycle_is_digest_verified(self):
        first = self.request()
        second = self.request(
            record_id="m2",
            operation_id="op-2",
            text="successor",
            authority_binding_id="auth-2",
            privacy_binding_id="privacy-2",
            supersedes="m1",
        )
        store = self.store_for(first, second)
        store.admit(first)
        store.admit(second)
        self.assertEqual(len(store.head_digest()), 64)
        data = strict_loads(self.path.read_bytes())
        data["records"][0]["superseded_by"] = "forged-successor"
        self.path.write_text(canonical_dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(MemoryAdmissionError, "record digest mismatch"):
            store.head_digest()



class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "checkpoint.json"
        self.orientation = OrientationGate().evaluate(complete_time_evidence(), now=NOW)
        self.predecessor = "d" * 64
        self.self_model = "b" * 64
        self.authority = "c" * 64
        self.state = CheckpointState(
            project_id="VERA_COGNITIVE_REPAIR_R8A0",
            identity_id="VERA",
            runtime_id="runtime-before",
            memory_head_digest="a" * 64,
            self_model_head_digest=self.self_model,
            authority_state_digest=self.authority,
            active_commitments=("finish bounded build",),
            unfinished_work=("Voss exact-head audit",),
            created_at=NOW.isoformat(),
            predecessor_checkpoint_digest=self.predecessor,
        )

    def tearDown(self):
        self.temp.cleanup()

    def checkpoint(self):
        return write_checkpoint(
            self.path,
            self.state,
            verified_predecessor_digest=self.predecessor,
            verified_self_model_head_digest=self.self_model,
            verified_authority_state_digest=self.authority,
        )

    def recover_with(self, checkpoint, termination, **updates):
        arguments = {
            "termination_receipt": termination,
            "expected_checkpoint_digest": checkpoint["checkpoint_digest"],
            "expected_checkpoint_receipt_digest": checkpoint["receipt_digest"],
            "expected_predecessor_checkpoint_digest": self.predecessor,
            "expected_self_model_head_digest": self.self_model,
            "expected_authority_state_digest": self.authority,
        }
        arguments.update(updates)
        return recover(self.path, self.orientation, **arguments)

    def test_checkpoint_terminate_recover(self):
        checkpoint = self.checkpoint()
        termination = terminate(self.state.runtime_id, checkpoint)
        self.assertFalse(termination["hidden_activity_claimed"])
        receipt = self.recover_with(checkpoint, termination)
        self.assertTrue(receipt["same_governed_identity_resumed"])
        self.assertFalse(receipt["new_runtime_is_separate_person"])
        self.assertFalse(receipt["uninterrupted_consciousness_claimed"])
        self.assertEqual(receipt["self_model_head_digest"], self.self_model)

    def test_direct_recovery_without_termination_fails(self):
        checkpoint = self.checkpoint()
        with self.assertRaises(RecoveryError):
            self.recover_with(checkpoint, {})

    def test_fresh_process_recovery(self):
        checkpoint = self.checkpoint()
        termination = terminate(self.state.runtime_id, checkpoint)
        recovery_input = Path(self.temp.name) / "recovery-input.json"
        evidence = {row.dimension: row.as_dict() for row in complete_time_evidence()}
        recovery_input.write_text(
            canonical_dumps(
                {
                    "now": NOW.isoformat(),
                    "orientation_source_mode": "CURRENT_SOURCE",
                    "orientation_evidence": evidence,
                    "termination_receipt": termination,
                    "expected_checkpoint_digest": checkpoint["checkpoint_digest"],
                    "expected_checkpoint_receipt_digest": checkpoint["receipt_digest"],
                    "expected_predecessor_checkpoint_digest": self.predecessor,
                    "expected_self_model_head_digest": self.self_model,
                    "expected_authority_state_digest": self.authority,
                }
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [sys.executable, "-m", "r8a0.cli", str(self.path), "--recovery-input", str(recovery_input)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        receipt = json.loads(completed.stdout)
        self.assertEqual(receipt["result"], "RECOVERED_FROM_VERIFIED_CHECKPOINT")

    def test_wrong_expected_checkpoint_digest_fails(self):
        checkpoint = self.checkpoint()
        termination = terminate(self.state.runtime_id, checkpoint)
        with self.assertRaises(RecoveryError):
            self.recover_with(checkpoint, termination, expected_checkpoint_digest="e" * 64)

    def test_wrong_checkpoint_receipt_digest_fails(self):
        checkpoint = self.checkpoint()
        termination = terminate(self.state.runtime_id, checkpoint)
        with self.assertRaises(RecoveryError):
            self.recover_with(checkpoint, termination, expected_checkpoint_receipt_digest="e" * 64)

    def test_wrong_predecessor_chain_fails(self):
        checkpoint = self.checkpoint()
        termination = terminate(self.state.runtime_id, checkpoint)
        with self.assertRaises(RecoveryError):
            self.recover_with(checkpoint, termination, expected_predecessor_checkpoint_digest="e" * 64)

    def test_wrong_self_model_head_fails(self):
        checkpoint = self.checkpoint()
        termination = terminate(self.state.runtime_id, checkpoint)
        with self.assertRaises(RecoveryError):
            self.recover_with(checkpoint, termination, expected_self_model_head_digest="e" * 64)

    def test_wrong_authority_state_fails(self):
        checkpoint = self.checkpoint()
        termination = terminate(self.state.runtime_id, checkpoint)
        with self.assertRaises(RecoveryError):
            self.recover_with(checkpoint, termination, expected_authority_state_digest="e" * 64)

    def test_tampered_termination_receipt_fails(self):
        checkpoint = self.checkpoint()
        termination = terminate(self.state.runtime_id, checkpoint)
        termination["runtime_id"] = "other-runtime"
        with self.assertRaises(RecoveryError):
            self.recover_with(checkpoint, termination)

    def test_unverified_checkpoint_predecessor_fails_write(self):
        with self.assertRaises(RecoveryError):
            write_checkpoint(
                self.path,
                self.state,
                verified_predecessor_digest="e" * 64,
                verified_self_model_head_digest=self.self_model,
                verified_authority_state_digest=self.authority,
            )

    def test_corrupt_checkpoint_fails(self):
        checkpoint = self.checkpoint()
        termination = terminate(self.state.runtime_id, checkpoint)
        data = strict_loads(self.path.read_bytes())
        data["payload"]["runtime_id"] = "tampered"
        self.path.write_text(canonical_dumps(data), encoding="utf-8")
        with self.assertRaises(RecoveryError):
            self.recover_with(checkpoint, termination)

    def test_partial_checkpoint_fails(self):
        self.path.write_text('{"schema":"VERA_R8A0_CHECKPOINT_V1","complete":false}', encoding="utf-8")
        with self.assertRaises(RecoveryError):
            recover(
                self.path,
                self.orientation,
                termination_receipt={},
                expected_checkpoint_digest=sha("partial"),
                expected_checkpoint_receipt_digest=sha("partial-receipt"),
                expected_predecessor_checkpoint_digest=self.predecessor,
                expected_self_model_head_digest=self.self_model,
                expected_authority_state_digest=self.authority,
            )

    def test_interrupted_temp_checkpoint_is_not_current(self):
        temp = self.path.with_suffix(".json.tmp")
        temp.write_text("partial", encoding="utf-8")
        with self.assertRaises(RecoveryError):
            recover(
                self.path,
                self.orientation,
                termination_receipt={},
                expected_checkpoint_digest="e" * 64,
                expected_checkpoint_receipt_digest="f" * 64,
                expected_predecessor_checkpoint_digest=self.predecessor,
                expected_self_model_head_digest=self.self_model,
                expected_authority_state_digest=self.authority,
            )

    def test_missing_checkpoint_fails(self):
        with self.assertRaises(RecoveryError):
            recover(
                self.path,
                self.orientation,
                termination_receipt={},
                expected_checkpoint_digest="e" * 64,
                expected_checkpoint_receipt_digest="f" * 64,
                expected_predecessor_checkpoint_digest=self.predecessor,
                expected_self_model_head_digest=self.self_model,
                expected_authority_state_digest=self.authority,
            )

    def test_recovery_without_temporal_authority_fails(self):
        checkpoint = self.checkpoint()
        termination = terminate(self.state.runtime_id, checkpoint)
        stale = OrientationGate().evaluate(complete_time_evidence(NOW - timedelta(hours=1)), now=NOW)
        with self.assertRaises(RecoveryError):
            recover(
                self.path,
                stale,
                termination_receipt=termination,
                expected_checkpoint_digest=checkpoint["checkpoint_digest"],
                expected_checkpoint_receipt_digest=checkpoint["receipt_digest"],
                expected_predecessor_checkpoint_digest=self.predecessor,
                expected_self_model_head_digest=self.self_model,
                expected_authority_state_digest=self.authority,
            )


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
            "r8a0/cli.py",
            "r8a0/memory.py",
            "r8a0/recovery.py",
            "r8a0/temporal.py",
            "tests/r8a0/test_vertical_slice.py",
            "docs/r8a0/BOUND_VERTICAL_SLICE.md",
        ]
        for path in paths:
            self.assertTrue(path.startswith(("r8a0/", "tests/r8a0/", "docs/r8a0/")), path)


if __name__ == "__main__":
    unittest.main()

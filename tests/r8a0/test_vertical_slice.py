from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from r8a0.canonical import canonical_bytes, canonical_dumps, canonical_sha256, strict_loads
from r8a0.lifecycle import LifecycleRegistry, LifecycleRegistryError
from r8a0.recovery import (
    CheckpointState,
    RecoveryError,
    checkpoint_state_from_mapping,
    recover,
    write_checkpoint,
    write_exit_attestation,
    write_termination_intent,
)
from r8a0.temporal import (
    CLAIM_DIMENSIONS,
    CURRENT_TIME,
    REQUIRED_DIMENSIONS,
    ClaimScope,
    OrientationGate,
    OrientationState,
    TimeEvidence,
)

PROJECT = "VERA_COGNITIVE_REPAIR_R8A0"
IDENTITY = "VERA"
NOW = datetime.now(timezone.utc).replace(microsecond=0)
N_HEX = "cf0074096a67475691b2477fc4b78d06fdf87608580aaea9f21cc6820e6b27678571e744d86e58e8dfe74c4f6b4f51fc0ded6e678ca71a73d32b0c3c1e32b5743dcd549e1aa340f5676e77f9e0d7456db24c611009f0e15a250d2e1333bb5534436a67d6a8d8bfca19b1ae81870852a36e760eab8485fd078ef5592c860cba2f"
D_HEX = "403de0c5274b841d3ebc386a53afaf49d339efcfa91b2f97b876ebb8632728247d8a9afe87b8bf490e6be707e2c2cc2bd05ab65fd68be9aeb6836e999db9990c3a5a0a516c784e127c9723e343ef2b00d7dc3723e38b03dd8badf659f48ca6800663b2cc2cf24efc0600ae04f6090fc2a77b0fdca92ba205dcba23e04c43b8b1"
DER = bytes.fromhex("3031300d060960864801650304020105000420")


def sha(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def public_key(key_id: str = "test") -> dict[str, object]:
    return {"key_id": key_id, "n_hex": N_HEX, "e": 65537}


def sign(payload: object) -> str:
    modulus = int(N_HEX, 16)
    private = int(D_HEX, 16)
    width = (modulus.bit_length() + 7) // 8
    tail = DER + hashlib.sha256(canonical_bytes(payload)).digest()
    encoded = b"\x00\x01" + b"\xff" * (width - len(tail) - 3) + b"\x00" + tail
    return format(pow(int.from_bytes(encoded, "big"), private, modulus), "x")


def signed(body: dict[str, object], issuer: str) -> dict[str, object]:
    material = dict(body) | {"issuer": issuer, "key_id": "test"}
    return material | {"signature": sign(material)}


def time_rows(at: datetime, *, dimensions=REQUIRED_DIMENSIONS, bounded: bool = False):
    lower = (at - timedelta(minutes=1)).isoformat() if bounded else None
    upper = (at + timedelta(minutes=1)).isoformat() if bounded else None
    rows = []
    for dimension in dimensions:
        source = "clock" if dimension == CURRENT_TIME else dimension
        body = {
            "dimension": dimension,
            "value": at.isoformat(),
            "source": source,
            "source_kind": dimension,
            "observed_at": at.isoformat(),
            "source_digest": sha(dimension),
            "source_key_id": "test",
            "lower_bound": lower,
            "upper_bound": upper,
        }
        rows.append(TimeEvidence(**body, source_signature=sign(body)))
    return rows


def temporal_keys(dimensions=REQUIRED_DIMENSIONS):
    return {
        "clock" if dimension == CURRENT_TIME else dimension: public_key()
        for dimension in dimensions
    }


def state_attestations(state: CheckpointState, observed_at: datetime):
    roots = {
        "predecessor_checkpoint": state.predecessor_checkpoint_digest,
        "memory_head": state.memory_head_digest,
        "self_model_head": state.self_model_head_digest,
        "authority_state": state.authority_state_digest,
    }
    return {
        kind: signed(
            {
                "schema": "VERA_R8A0_STATE_ROOT_ATTESTATION_V1",
                "kind": kind,
                "project_id": state.project_id,
                "identity_id": state.identity_id,
                "digest": digest,
                "generation": 1,
                "observed_at": observed_at.isoformat(),
            },
            "state-issuer",
        )
        for kind, digest in roots.items()
    }


class TemporalScopeTests(unittest.TestCase):
    def test_structured_claim_scope_is_exact_and_receipt_bound(self):
        required = CLAIM_DIMENSIONS["event_timestamp"]
        rows = time_rows(NOW, dimensions=required, bounded=True)
        gate = OrientationGate(trusted_source_keys=temporal_keys(required))
        scope = {"scope_id": "event-check", "claims": ["event_timestamp"]}
        receipt = gate.evaluate(
            rows,
            now=NOW,
            required_dimensions=required,
            degraded_allowed=True,
            claim_scope=scope,
        )
        self.assertEqual(receipt.state, OrientationState.DEGRADED_BOUNDED)
        self.assertTrue(receipt.claims_allowed)
        self.assertEqual(receipt.claim_scope, scope)
        self.assertEqual(
            receipt.claim_scope_digest,
            canonical_sha256(
                {"claim_scope": scope, "required_dimensions": list(required)}
            ),
        )
        self.assertEqual(len(receipt.supporting_evidence_ids), len(required))

        with self.assertRaisesRegex(ValueError, "free-form"):
            gate.evaluate(
                rows,
                now=NOW,
                required_dimensions=required,
                degraded_allowed=True,
                response_scope="anything broad and convenient",
            )
        with self.assertRaisesRegex(ValueError, "unknown claims"):
            gate.evaluate(
                rows,
                now=NOW,
                required_dimensions=required,
                degraded_allowed=True,
                claim_scope={"scope_id": "broad", "claims": ["everything"]},
            )
        with self.assertRaisesRegex(ValueError, "map exactly"):
            gate.evaluate(
                rows,
                now=NOW,
                required_dimensions=(CURRENT_TIME,),
                degraded_allowed=True,
                claim_scope=scope,
            )
        with self.assertRaisesRegex(ValueError, "scope ID"):
            ClaimScope("   ", ("event_timestamp",)).validate()


class CheckpointSchemaTests(unittest.TestCase):
    def valid_mapping(self):
        return {
            "project_id": PROJECT,
            "identity_id": IDENTITY,
            "runtime_id": "runtime-before",
            "runtime_instance_nonce": "instance-1",
            "memory_head_digest": "a" * 64,
            "self_model_head_digest": "b" * 64,
            "authority_state_digest": "c" * 64,
            "active_commitments": ["finish final frozen cycle"],
            "unfinished_work": ["Voss exact-head review"],
            "created_at": NOW.isoformat(),
            "predecessor_checkpoint_digest": "d" * 64,
        }

    def test_strict_types_are_enforced_before_persistence_and_recovery(self):
        self.assertIsInstance(checkpoint_state_from_mapping(self.valid_mapping()), CheckpointState)
        bad = self.valid_mapping()
        bad["active_commitments"] = "not-a-list"
        with self.assertRaisesRegex(RecoveryError, "list of strings"):
            checkpoint_state_from_mapping(bad)
        bad = self.valid_mapping()
        bad["unfinished_work"] = ["valid", 7]
        with self.assertRaisesRegex(RecoveryError, "nonempty strings"):
            checkpoint_state_from_mapping(bad)
        bad = self.valid_mapping()
        bad["runtime_id"] = 42
        with self.assertRaisesRegex(RecoveryError, "nonempty string"):
            checkpoint_state_from_mapping(bad)
        state = checkpoint_state_from_mapping(self.valid_mapping())
        malformed = CheckpointState(
            **{**state.__dict__, "active_commitments": ("valid", 3)}
        )
        with self.assertRaisesRegex(RecoveryError, "nonempty strings"):
            malformed.validate()


class LifecycleTimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.checkpoint = self.root / "checkpoint.json"
        self.checkpoint_receipt = self.root / "checkpoint-receipt.json"
        self.intent = self.root / "termination-intent.json"
        self.exit = self.root / "exit.json"
        self.registry = self.root / "lifecycle.json"
        self.registry_key = b"lifecycle-registry-integrity-key"
        self.state_keys = {"state-issuer": public_key()}
        self.lifecycle_keys = {"lifecycle-issuer": public_key()}
        self.supervisor_keys = {"supervisor-issuer": public_key()}

    def tearDown(self):
        self.temp.cleanup()

    def make_state(self, created_at: datetime) -> CheckpointState:
        return CheckpointState(
            PROJECT,
            IDENTITY,
            "runtime-before",
            "instance-1",
            "a" * 64,
            "b" * 64,
            "c" * 64,
            ("finish final frozen cycle",),
            ("Voss exact-head review",),
            created_at.isoformat(),
            "d" * 64,
        )

    def create_chain(self, base: datetime):
        state = self.make_state(base - timedelta(seconds=1))
        with patch("r8a0.recovery_evidence._utc_now", return_value=base):
            checkpoint = write_checkpoint(
                self.checkpoint,
                state,
                checkpoint_receipt_path=self.checkpoint_receipt,
                state_attestations=state_attestations(state, base),
                trusted_state_keys=self.state_keys,
                lifecycle_issuer="lifecycle-issuer",
                lifecycle_key_id="test",
                lifecycle_signer=sign,
            )
        with patch("r8a0.recovery_evidence._utc_now", return_value=base + timedelta(seconds=1)):
            intent = write_termination_intent(
                checkpoint_receipt_path=self.checkpoint_receipt,
                termination_intent_path=self.intent,
                trusted_lifecycle_keys=self.lifecycle_keys,
                lifecycle_issuer="lifecycle-issuer",
                lifecycle_key_id="test",
                lifecycle_signer=sign,
                process_id=2_147_483_647,
            )
        exit_attestation = write_exit_attestation(
            path=self.exit,
            checkpoint_receipt=checkpoint,
            termination_intent=intent,
            exit_code=0,
            observed_at=(base + timedelta(seconds=2)).isoformat(),
            supervisor_issuer="supervisor-issuer",
            supervisor_key_id="test",
            supervisor_signer=sign,
        )
        return state, checkpoint, intent, exit_attestation

    def recover_chain(self, base, state, checkpoint, intent, exit_attestation):
        registry = LifecycleRegistry(self.registry, self.registry_key)
        with patch("r8a0.recovery_runtime._utc_now", return_value=base + timedelta(seconds=3)):
            return recover(
                self.checkpoint,
                orientation_evidence=time_rows(base + timedelta(seconds=3)),
                orientation_source_mode="CURRENT_SOURCE",
                trusted_temporal_keys=temporal_keys(),
                checkpoint_receipt_path=self.checkpoint_receipt,
                termination_intent_path=self.intent,
                exit_attestation_path=self.exit,
                trusted_lifecycle_keys=self.lifecycle_keys,
                trusted_supervisor_keys=self.supervisor_keys,
                trusted_state_keys=self.state_keys,
                expected_checkpoint_receipt_signature=checkpoint["signature"],
                expected_termination_intent_signature=intent["signature"],
                expected_exit_attestation_signature=exit_attestation["signature"],
                expected_project_id=PROJECT,
                expected_identity_id=IDENTITY,
                expected_predecessor_checkpoint_digest=state.predecessor_checkpoint_digest,
                expected_memory_head_digest=state.memory_head_digest,
                expected_self_model_head_digest=state.self_model_head_digest,
                expected_authority_state_digest=state.authority_state_digest,
                successor_runtime_id="runtime-after",
                lifecycle_registry_path=self.registry,
                lifecycle_registry_key=self.registry_key,
                expected_lifecycle_registry_head=registry.current_head(),
            )

    def test_valid_order_is_bound_and_second_successor_is_rejected(self):
        state, checkpoint, intent, exit_attestation = self.create_chain(NOW)
        receipt = self.recover_chain(NOW, state, checkpoint, intent, exit_attestation)
        self.assertEqual(receipt["result"], "RECOVERED_FROM_VERIFIED_CHECKPOINT")
        self.assertLessEqual(receipt["checkpoint_created_at"], receipt["checkpoint_observed_at"])
        self.assertLessEqual(receipt["checkpoint_observed_at"], receipt["termination_intent_at"])
        self.assertLessEqual(receipt["termination_intent_at"], receipt["exit_observed_at"])
        self.assertLessEqual(receipt["exit_observed_at"], receipt["recovery_evaluated_at"])
        with self.assertRaises(LifecycleRegistryError):
            self.recover_chain(NOW, state, checkpoint, intent, exit_attestation)

    def test_future_stale_and_reordered_lifecycle_are_rejected(self):
        future = self.make_state(NOW + timedelta(minutes=10))
        with patch("r8a0.recovery_evidence._utc_now", return_value=NOW):
            with self.assertRaisesRegex(RecoveryError, "future"):
                write_checkpoint(
                    self.checkpoint,
                    future,
                    checkpoint_receipt_path=self.checkpoint_receipt,
                    state_attestations=state_attestations(future, NOW),
                    trusted_state_keys=self.state_keys,
                    lifecycle_issuer="lifecycle-issuer",
                    lifecycle_key_id="test",
                    lifecycle_signer=sign,
                )

        old = NOW - timedelta(hours=2)
        state, checkpoint, intent, exit_attestation = self.create_chain(old)
        registry = LifecycleRegistry(self.registry, self.registry_key)
        with patch("r8a0.recovery_runtime._utc_now", return_value=NOW):
            with self.assertRaisesRegex(RecoveryError, "stale"):
                recover(
                    self.checkpoint,
                    orientation_evidence=time_rows(NOW),
                    orientation_source_mode="CURRENT_SOURCE",
                    trusted_temporal_keys=temporal_keys(),
                    checkpoint_receipt_path=self.checkpoint_receipt,
                    termination_intent_path=self.intent,
                    exit_attestation_path=self.exit,
                    trusted_lifecycle_keys=self.lifecycle_keys,
                    trusted_supervisor_keys=self.supervisor_keys,
                    trusted_state_keys=self.state_keys,
                    expected_checkpoint_receipt_signature=checkpoint["signature"],
                    expected_termination_intent_signature=intent["signature"],
                    expected_exit_attestation_signature=exit_attestation["signature"],
                    expected_project_id=PROJECT,
                    expected_identity_id=IDENTITY,
                    expected_predecessor_checkpoint_digest=state.predecessor_checkpoint_digest,
                    expected_memory_head_digest=state.memory_head_digest,
                    expected_self_model_head_digest=state.self_model_head_digest,
                    expected_authority_state_digest=state.authority_state_digest,
                    successor_runtime_id="runtime-after",
                    lifecycle_registry_path=self.registry,
                    lifecycle_registry_key=self.registry_key,
                    expected_lifecycle_registry_head=registry.current_head(),
                )

        self.temp.cleanup()
        self.setUp()
        state, checkpoint, intent, exit_attestation = self.create_chain(NOW)
        checkpoint_body = {k: v for k, v in checkpoint.items() if k != "signature"}
        checkpoint_body["checkpoint_observed_at"] = (NOW + timedelta(minutes=2)).isoformat()
        checkpoint = checkpoint_body | {"signature": sign(checkpoint_body)}
        self.checkpoint_receipt.write_text(canonical_dumps(checkpoint), encoding="utf-8")
        intent_body = {k: v for k, v in intent.items() if k != "signature"}
        intent_body["checkpoint_receipt_signature"] = checkpoint["signature"]
        intent = intent_body | {"signature": sign(intent_body)}
        self.intent.write_text(canonical_dumps(intent), encoding="utf-8")
        exit_body = {k: v for k, v in exit_attestation.items() if k != "signature"}
        exit_body["checkpoint_receipt_signature"] = checkpoint["signature"]
        exit_body["termination_intent_signature"] = intent["signature"]
        exit_attestation = exit_body | {"signature": sign(exit_body)}
        self.exit.write_text(canonical_dumps(exit_attestation), encoding="utf-8")
        with self.assertRaisesRegex(RecoveryError, "termination intent predates checkpoint"):
            self.recover_chain(NOW, state, checkpoint, intent, exit_attestation)


class WorkflowTests(unittest.TestCase):
    def test_ci_uses_authorized_lineage_and_exact_acceptance_commands(self):
        workflow = (ROOT / ".github/workflows/r8a0-bounded-vertical-slice.yml").read_text()
        self.assertIn('AUTHORIZED_BASE_SHA: "12dd3cb4e3329324885a827506d4f7e8ac25d41d"', workflow)
        self.assertIn('APPROVED_PARENT_SHA: "c4c16997698460acbf9cddb03a27b1c1128ab223"', workflow)
        self.assertIn('fetch-depth: 0', workflow)
        self.assertIn('git diff --name-only "$AUTHORIZED_BASE_SHA" HEAD', workflow)
        self.assertIn('test "$(git rev-parse HEAD^)" = "$APPROVED_PARENT_SHA"', workflow)
        self.assertIn('test "$DISPATCH_BASE_SHA" = "$AUTHORIZED_BASE_SHA"', workflow)
        self.assertIn('test "$EVENT_BASE_SHA" = "$AUTHORIZED_BASE_SHA"', workflow)
        self.assertNotIn('BASE_SHA="HEAD^"', workflow)
        self.assertIn('python -m compileall -q -f r8a0 tests/r8a0', workflow)
        self.assertIn(
            "PYTHONHASHSEED=0 TERM=xterm python -X dev -m unittest discover -s tests/r8a0 -p 'test_*.py' -v",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()

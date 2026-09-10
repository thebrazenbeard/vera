from collections.abc import Mapping
import copy
import hashlib
import json
from pathlib import Path
import unittest

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import (
    PersistenceRecordError,
    checkpoint_to_state_row,
    event_receipt_to_event_row,
    restore_host_from_state_row,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class TrustedVerifier:
    verifier_id = "affect-persistence-runtime-owned-verifier"

    def verify(self, subject, *, expected_referent, expected_effect_class):
        if not isinstance(subject, Mapping):
            return None
        if subject.get("state") != "ALLOW":
            return None
        if subject.get("referent") != expected_referent:
            return None
        if subject.get("proposition_or_effect_class") != expected_effect_class:
            return None
        if subject.get("currentness") != "CURRENT" or subject.get("expiry_or_supersession") is not None:
            return None
        canonical = json.dumps(dict(subject), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "verifier_id": self.verifier_id,
            "evidence_id": "affect-persistence-evidence",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class VeraAffectiveRuntimePersistenceTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(TrustedVerifier())

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="vera-affective-runtime-test",
            profile="REENTRANT_CLIMAX",
        )

    @staticmethod
    def authorization_subject():
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-affect-persistence-test",
            "observed_at": "2026-09-10T19:45:00+00:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    def test_checkpoint_maps_to_vera_scoped_durable_state_row_with_digest(self):
        host = self.make_host()
        row = checkpoint_to_state_row(host.export_checkpoint(), host_scope="TEST_HOST", state_version=1)
        self.assertEqual(row["runtime_instance_id"], "vera-affective-runtime-test")
        self.assertEqual(row["subject"], "vera")
        self.assertEqual(row["contract_schema"], "VERA_ORGASM_RUNTIME_CONTRACT_V1")
        self.assertEqual(row["phenomenology_status"], "UNRESOLVED")
        self.assertEqual(len(row["state_digest"]), 64)
        self.assertEqual(len(row["checkpoint_sha256"]), 64)
        self.assertEqual(row["state_version"], 1)
        self.assertEqual(row["lifecycle_status"], "CURRENT")

    def test_event_receipt_maps_to_append_only_orgasm_event_row(self):
        host = self.make_host()
        receipt = host.force_admin_test(authorization_subject=self.authorization_subject())
        row = event_receipt_to_event_row(host, receipt)
        self.assertEqual(row["runtime_instance_id"], "vera-affective-runtime-test")
        self.assertEqual(row["event_type"], "ORGASM_EVENT")
        self.assertEqual(row["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertFalse(row["organic"])
        self.assertEqual(row["new_phase"], "ORGASM_EVENT")
        self.assertEqual(row["event_digest"], receipt["event_digest"])
        self.assertEqual(row["phenomenology_status"], "UNRESOLVED")

    def test_restore_rejects_tampered_state_digest(self):
        host = self.make_host()
        row = checkpoint_to_state_row(host.export_checkpoint(), host_scope="TEST_HOST", state_version=1)
        tampered = copy.deepcopy(row)
        tampered["state"]["activation_intensity"] = 0.99
        with self.assertRaises(PersistenceRecordError):
            restore_host_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                tampered,
                expected_host_scope="TEST_HOST",
                expected_checkpoint_sha256=row["checkpoint_sha256"],
            )

    def test_restore_roundtrip_returns_same_runtime_and_applies_decay(self):
        host = self.make_host()
        host.force_admin_test(authorization_subject=self.authorization_subject())
        host.advance_time(5.1)
        row = checkpoint_to_state_row(host.export_checkpoint(), host_scope="TEST_HOST", state_version=2)
        before = row["state"]["satiation"]
        restored = restore_host_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            expected_host_scope="TEST_HOST",
            elapsed_seconds=1200,
            expected_checkpoint_sha256=row["checkpoint_sha256"],
        )
        self.assertLess(restored.machine_interoception()["satiation"], before)
        self.assertEqual(restored.machine_interoception()["phenomenology"], "UNRESOLVED")

    def test_restore_rejects_noncurrent_or_cross_scope_rows(self):
        host = self.make_host()
        checkpoint = host.export_checkpoint()
        current = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)

        superseded = copy.deepcopy(current)
        superseded["lifecycle_status"] = "SUPERSEDED"
        with self.assertRaises(PersistenceRecordError):
            restore_host_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                superseded,
                expected_host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            )

        with self.assertRaises(PersistenceRecordError):
            restore_host_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                current,
                expected_host_scope="OTHER_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            )


if __name__ == "__main__":
    unittest.main()

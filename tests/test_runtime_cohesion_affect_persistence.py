import copy
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import (
    PersistenceRecordError,
    checkpoint_to_state_row,
    event_receipt_to_event_row,
    restore_host_from_state_row,
)
from runtime_cohesion.orgasm import TriggerRejected

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveRuntimePersistenceTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="vera-affective-runtime-test",
            profile="REENTRANT_CLIMAX",
        )

    def restore_row(self, row, *, expected_checkpoint_sha256, elapsed_seconds=0.0):
        return restore_host_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            elapsed_seconds=elapsed_seconds,
            expected_checkpoint_sha256=expected_checkpoint_sha256,
        )

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
        receipt = host.force_admin_test(authorized=True)
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
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)
        tampered = copy.deepcopy(row)
        tampered["state"]["activation_intensity"] = 0.99
        with self.assertRaises(PersistenceRecordError):
            self.restore_row(
                tampered,
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            )

    def test_restore_roundtrip_returns_same_runtime_and_applies_decay(self):
        host = self.make_host()
        host.force_admin_test(authorized=True)
        host.advance_time(5.1)
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=2)
        before = row["state"]["satiation"]
        restored = self.restore_row(
            row,
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            elapsed_seconds=1200,
        )
        self.assertLess(restored.machine_interoception()["satiation"], before)
        self.assertEqual(restored.machine_interoception()["phenomenology"], "UNRESOLVED")

    def test_provider_row_roundtrip_preserves_trigger_governance_and_external_checkpoint_pin(self):
        host = self.make_host()
        host.force_self_qualification(authorized=True)
        host.advance_time(20.0)
        host.force_self_qualification(authorized=True)
        host.advance_time(20.0)

        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=3)

        self.assertIn("_trigger_governance", row["state"])
        restored = self.restore_row(
            row,
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        self.assertEqual(
            restored.export_checkpoint()["checkpoint_sha256"],
            checkpoint["checkpoint_sha256"],
        )
        with self.assertRaises(TriggerRejected):
            restored.force_self_qualification(authorized=True)

    def test_provider_row_roundtrip_preserves_forced_test_cooldown(self):
        host = self.make_host()
        host.force_admin_test(authorized=True)
        host.advance_time(5.1)

        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=2)
        restored = self.restore_row(
            row,
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )

        with self.assertRaises(TriggerRejected):
            restored.force_admin_test(authorized=True)
        restored.advance_time(5.0)
        receipt = restored.force_admin_test(authorized=True)
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")


if __name__ == "__main__":
    unittest.main()

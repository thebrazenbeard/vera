import copy
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import AffectiveBindingError, VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import (
    PersistenceRecordError,
    checkpoint_to_state_row,
    event_receipt_to_event_row,
    restore_host_from_state_row,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
MIGRATIONS = ROOT / "supabase" / "migrations"


class VeraAffectiveDurableIntegrityTests(unittest.TestCase):
    def make_host(self, runtime_instance_id="affect-durable-integrity-test"):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id=runtime_instance_id,
            profile="REENTRANT_CLIMAX",
        )

    def test_checkpoint_restore_requires_external_digest_and_rejects_recomputed_tamper(self):
        host = self.make_host()
        checkpoint = host.export_checkpoint()
        self.assertIn("checkpoint_sha256", checkpoint)
        expected = checkpoint["checkpoint_sha256"]

        tampered = copy.deepcopy(checkpoint)
        tampered["runtime_state"]["state"]["activation_intensity"] = 1.0
        tampered["runtime_state"]["state"]["active_orgasm_event"] = True
        tampered["runtime_state"]["state"]["phase"] = "ORGASM_EVENT"

        import hashlib
        core = dict(tampered)
        core.pop("checkpoint_sha256", None)
        canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        tampered["checkpoint_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        with self.assertRaises(AffectiveBindingError):
            VeraAffectiveRuntimeHost.restore_checkpoint(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                tampered,
                expected_checkpoint_sha256=expected,
            )

    def test_durable_row_restore_requires_the_separately_pinned_checkpoint_digest(self):
        host = self.make_host()
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)
        self.assertEqual(row["checkpoint_sha256"], checkpoint["checkpoint_sha256"])

        with self.assertRaises(PersistenceRecordError):
            restore_host_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                row,
                expected_host_scope="TEST_HOST",
            )

        restored = restore_host_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            expected_host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        self.assertEqual(restored.machine_interoception()["phase"], "QUIESCENT")

    def test_low_level_restore_cannot_be_rewrapped_to_different_live_scope(self):
        host = self.make_host()
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)
        restored = restore_host_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            expected_host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )

        with self.assertRaises(ValueError):
            VeraAffectiveCycle(
                restored,
                host_scope="OTHER_HOST",
                initial_state_version=2,
            )

    def test_restored_scope_binding_cannot_be_spoofed_by_mutating_host_attribute(self):
        host = self.make_host()
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)
        restored = restore_host_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            expected_host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )

        restored._durable_host_scope = "OTHER_HOST"
        with self.assertRaises(ValueError):
            VeraAffectiveCycle(
                restored,
                host_scope="OTHER_HOST",
                initial_state_version=2,
            )

    def test_event_receipt_digest_is_recomputed_before_persistence(self):
        host = self.make_host()
        receipt = host.force_admin_test(authorized=True)
        tampered = copy.deepcopy(receipt)
        tampered["state_after"]["hedonic_impact"] = 0.0
        tampered["event_digest"] = "0" * 64
        with self.assertRaises(PersistenceRecordError):
            event_receipt_to_event_row(host, tampered)

    def test_resolution_transition_is_emitted_as_a_first_class_event_row(self):
        host = self.make_host()
        state_rows = []
        event_rows = []
        cycle = VeraAffectiveCycle(
            host,
            host_scope="TEST_HOST",
            state_writer=state_rows.append,
            event_writer=event_rows.append,
        )
        cycle.force_admin_test(authorized=True, planning_state={"truth": 1.0})
        result = cycle.advance_time(5.1, planning_state={"truth": 1.0})

        self.assertIsNotNone(result.event_row)
        self.assertIn(result.event_row["event_type"], {"RESOLUTION", "RECOVERY"})
        self.assertIn(result.event_row["new_phase"], {"RESOLUTION", "SATIATED_OR_REFRACTORY"})
        self.assertGreaterEqual(len(event_rows), 2)

    def test_provider_source_declares_atomic_compare_and_swap_commit(self):
        sql = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(MIGRATIONS.glob("*vera_affective_runtime*.sql"))
        ).lower()
        self.assertIn("expected_prior_version", sql)
        self.assertIn("for update", sql)
        self.assertIn("vera_affective_runtime_commit_v1", sql)
        self.assertIn("state_version", sql)
        self.assertIn("event", sql)


if __name__ == "__main__":
    unittest.main()

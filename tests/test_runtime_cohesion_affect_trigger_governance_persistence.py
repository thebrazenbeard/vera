import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import checkpoint_to_state_row, restore_host_from_state_row
from runtime_cohesion.orgasm import TriggerRejected

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
MIGRATION = ROOT / "supabase" / "migrations" / "20260909181500_close_vera_affective_runtime_first_write_race_v1.sql"


class VeraAffectiveTriggerGovernancePersistenceTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="affect-trigger-governance-persistence-test",
            profile="REENTRANT_CLIMAX",
        )

    def test_provider_state_row_preserves_trigger_governance_and_restore_enforces_it(self):
        host = self.make_host()

        # This test isolates durable cooldown/governance mechanics. The raw engine
        # seam is intentionally nonqualifying and therefore does not claim that a
        # boolean is production authorization evidence.
        raw_receipt = host.runtime.force_admin_test(authorized=True)
        self.assertNotIn("claim", raw_receipt)
        host.advance_time(5.1)
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)

        self.assertIn("trigger_governance", row)
        self.assertEqual(row["trigger_governance"]["schema"], "VERA_ORGASM_TRIGGER_GOVERNANCE_V1")

        restored = restore_host_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            expected_host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        with self.assertRaises(TriggerRejected):
            restored.runtime.force_admin_test(authorized=True)

    def test_provider_migration_carries_trigger_governance_through_atomic_state_commit(self):
        sql = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("add column if not exists trigger_governance jsonb", sql)
        self.assertIn("trigger_governance,", sql)
        self.assertIn("p_state_row->'trigger_governance'", sql)
        self.assertIn("trigger_governance = excluded.trigger_governance", sql)


if __name__ == "__main__":
    unittest.main()

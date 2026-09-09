import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import (
    PersistenceRecordError,
    checkpoint_to_state_row,
    restore_host_from_state_row,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class LowerRestoreCurrentnessTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="lower-restore-currentness",
            profile="REENTRANT_CLIMAX",
        )

    def restore(self, row):
        return restore_host_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            expected_checkpoint_sha256=row["checkpoint_sha256"],
        )

    def test_exported_lower_restore_rejects_historical_rows(self):
        host = self.make_host()
        row = checkpoint_to_state_row(
            host.export_checkpoint(),
            host_scope="ORIGINAL_HOST",
            state_version=1,
            lifecycle_status="HISTORICAL",
        )
        with self.assertRaises(PersistenceRecordError):
            self.restore(row)

    def test_lower_restore_cannot_be_rebound_to_another_live_host_scope(self):
        host = self.make_host()
        row = checkpoint_to_state_row(
            host.export_checkpoint(),
            host_scope="ORIGINAL_HOST",
            state_version=1,
            lifecycle_status="CURRENT",
        )
        restored = self.restore(row)

        cycle = VeraAffectiveCycle(
            restored,
            host_scope="DIFFERENT_HOST",
            initial_state_version=2,
        )
        result = cycle.advance_time(1.0, planning_state={})
        self.assertEqual(result.state_row["host_scope"], "ORIGINAL_HOST")


if __name__ == "__main__":
    unittest.main()

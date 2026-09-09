import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import checkpoint_to_state_row

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveRestoreHostScopeTests(unittest.TestCase):
    def make_row(self):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="host-scope-restore-test",
            profile="REENTRANT_CLIMAX",
        )
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="ORIGINAL_HOST", state_version=4)
        return checkpoint, row

    def test_restore_cycle_rejects_cross_host_scope_rebinding(self):
        checkpoint, row = self.make_row()
        with self.assertRaises(ValueError):
            VeraAffectiveCycle.restore_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                row,
                host_scope="DIFFERENT_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            )

    def test_restore_cycle_accepts_exact_persisted_host_scope(self):
        checkpoint, row = self.make_row()
        cycle = VeraAffectiveCycle.restore_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            host_scope="ORIGINAL_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        self.assertEqual(cycle.host_scope, "ORIGINAL_HOST")
        self.assertEqual(cycle._next_state_version, 5)


if __name__ == "__main__":
    unittest.main()

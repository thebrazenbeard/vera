import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import checkpoint_to_state_row, restore_host_from_state_row


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class CheckpointScopeBypassTests(unittest.TestCase):
    def make_bound_checkpoint_and_row(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="checkpoint-scope-bypass-test",
        )
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)
        self.assertEqual(row["host_scope"], "TEST_HOST")
        return contract_text, binding, checkpoint, row

    def test_direct_checkpoint_restore_cannot_launder_durable_scope(self):
        contract_text, binding, checkpoint, row = self.make_bound_checkpoint_and_row()
        restored = VeraAffectiveRuntimeHost.restore_checkpoint(
            contract_text,
            binding,
            checkpoint,
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        with self.assertRaisesRegex(ValueError, r"(?i)(scope|durable|checkpoint|live|provider|replay)"):
            VeraAffectiveCycle(
                restored,
                host_scope="OTHER_HOST",
                initial_state_version=row["state_version"] + 1,
            )

    def test_direct_checkpoint_restore_cannot_claim_original_live_scope_without_live_attestation(self):
        contract_text, binding, checkpoint, row = self.make_bound_checkpoint_and_row()
        restored = VeraAffectiveRuntimeHost.restore_checkpoint(
            contract_text,
            binding,
            checkpoint,
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        with self.assertRaisesRegex(ValueError, r"(?i)(current|scope|durable|attestation|replay|provider)"):
            VeraAffectiveCycle(
                restored,
                host_scope=row["host_scope"],
                initial_state_version=row["state_version"] + 1,
            )

    def test_low_level_provider_row_restore_remains_replay_only_even_with_validated_scope_bytes(self):
        contract_text, binding, checkpoint, row = self.make_bound_checkpoint_and_row()
        restored = restore_host_from_state_row(
            contract_text,
            binding,
            row,
            expected_host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        with self.assertRaisesRegex(ValueError, r"(?i)(current|provider|attestation|replay|durable)"):
            VeraAffectiveCycle(
                restored,
                host_scope="TEST_HOST",
                initial_state_version=row["state_version"] + 1,
            )


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import checkpoint_to_state_row
from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class RuntimeRestoreScopeBypassTests(unittest.TestCase):
    def make_bound_material(self, *, runtime_instance_id="runtime-restore-scope-bypass-test"):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        contract = json.loads(contract_text)
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id=runtime_instance_id,
        )
        return contract_text, contract, binding, host

    def make_durable_runtime_bytes(self):
        contract_text, contract, binding, host = self.make_bound_material()
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=1,
        )
        self.assertEqual(row["host_scope"], "TEST_HOST")
        self.assertEqual(row["state_version"], 1)
        return contract_text, contract, binding, host, checkpoint["runtime_state"], row

    def rewrap_raw_restored_runtime(self):
        contract_text, contract, binding, original_host, runtime_state, row = self.make_durable_runtime_bytes()

        # runtime_state bytes are scope-agnostic. The provider row is what binds
        # those bytes to CURRENT lifecycle, durable scope, and generation. A raw
        # runtime restore therefore remains replay/unattested until a separately
        # verified provider-current boundary supplies that provenance.
        restored_runtime = OrgasmRuntime.restore_state(
            contract,
            runtime_state,
            source_revision=str(binding["source_commit"]),
        )
        rewrapped_host = VeraAffectiveRuntimeHost(
            restored_runtime,
            binding=binding,
            contract_blob_sha=original_host.contract_blob_sha,
            contract_sha256=original_host.contract_sha256,
        )
        return contract_text, binding, rewrapped_host, row

    @staticmethod
    def atomic_writer(writes):
        def write(request):
            writes.append(dict(request))
            return {
                "state_version": request["state_version"],
                "checkpoint_sha256": request["checkpoint_sha256"],
                "event_count": len(request["event_rows"]),
            }

        return write

    def assert_unattested_rewrap_rejected(self, claimed_scope):
        _contract_text, _binding, rewrapped_host, row = self.rewrap_raw_restored_runtime()
        writes = []

        with self.assertRaisesRegex(
            ValueError,
            r"(?i)(scope|current|durable|attestation|restore|replay)",
        ):
            cycle = VeraAffectiveCycle(
                rewrapped_host,
                host_scope=claimed_scope,
                initial_state_version=row["state_version"] + 1,
                atomic_commit_writer=self.atomic_writer(writes),
            )
            cycle.process_turn(
                StimulusAppraisal(),
                planning_state={},
            )

        self.assertEqual(
            writes,
            [],
            "unattested raw-restored runtime must be rejected before any atomic provider write is attempted",
        )

    def test_public_runtime_restore_cannot_be_rewrapped_into_other_durable_scope(self):
        self.assert_unattested_rewrap_rejected("OTHER_HOST")

    def test_public_runtime_restore_cannot_claim_original_scope_from_caller_assertion(self):
        self.assert_unattested_rewrap_rejected("TEST_HOST")

    def test_fresh_nonrestored_runtime_can_start_new_atomic_durable_scope(self):
        _contract_text, _contract, _binding, host = self.make_bound_material(
            runtime_instance_id="fresh-runtime-new-durable-scope-test",
        )
        writes = []
        cycle = VeraAffectiveCycle(
            host,
            host_scope="NEW_HOST",
            initial_state_version=1,
            atomic_commit_writer=self.atomic_writer(writes),
        )

        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={},
        )

        self.assertEqual(result.durability_mode, "ATOMIC_DURABLE")
        self.assertEqual(result.state_row["host_scope"], "NEW_HOST")
        self.assertEqual(result.state_row["state_version"], 1)
        self.assertEqual(len(writes), 1)


if __name__ == "__main__":
    unittest.main()

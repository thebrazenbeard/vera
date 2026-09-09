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
    def make_durable_runtime_bytes(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        contract = json.loads(contract_text)
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="runtime-restore-scope-bypass-test",
        )
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=1,
        )
        self.assertEqual(row["host_scope"], "TEST_HOST")
        self.assertEqual(row["state_version"], 1)
        return contract, binding, host, checkpoint["runtime_state"], row

    def test_public_runtime_restore_cannot_be_rewrapped_into_other_durable_scope(self):
        contract, binding, original_host, runtime_state, row = self.make_durable_runtime_bytes()

        # Restore the exact durable runtime bytes through the lower public API,
        # then wrap that runtime in a fresh host object. Host-identity sidecars
        # must not erase the provider scope/currentness provenance that existed
        # for these bytes.
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

        writes = []

        def current_version_atomic_writer(request):
            writes.append(dict(request))
            return {
                "state_version": request["state_version"],
                "checkpoint_sha256": request["checkpoint_sha256"],
                "event_count": len(request["event_rows"]),
            }

        with self.assertRaisesRegex(
            ValueError,
            r"(?i)(scope|current|durable|attestation|restore|replay)",
        ):
            cycle = VeraAffectiveCycle(
                rewrapped_host,
                host_scope="OTHER_HOST",
                initial_state_version=row["state_version"] + 1,
                atomic_commit_writer=current_version_atomic_writer,
            )
            cycle.process_turn(
                StimulusAppraisal(),
                planning_state={},
                elapsed_seconds=0.0,
            )

        self.assertEqual(
            writes,
            [],
            "scope-rewrapped restored runtime must be rejected before any atomic provider write is attempted",
        )


if __name__ == "__main__":
    unittest.main()

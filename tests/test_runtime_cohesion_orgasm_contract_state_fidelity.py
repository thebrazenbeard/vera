import copy
import json
from pathlib import Path
import unittest

from runtime_cohesion.orgasm import ContractError, OrgasmRuntime

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class OrgasmContractStateFidelityTests(unittest.TestCase):
    def make_runtime(self, profile="REFRACTORY_COUPLED"):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        return contract, OrgasmRuntime(
            contract,
            runtime_instance_id="contract-state-fidelity",
            source_revision="sexuality:test-revision",
            profile=profile,
        )

    def test_snapshot_carries_declared_recovery_state_fields(self):
        contract, runtime = self.make_runtime()
        recovery = contract["state_families"]["recovery"]
        self.assertIn("reentry_allowed", recovery)
        self.assertIn("next_eligible_at", recovery)

        state = runtime.snapshot()
        self.assertIn("reentry_allowed", state)
        self.assertIsInstance(state["reentry_allowed"], bool)
        self.assertIn("next_eligible_at", state)
        self.assertTrue(state["next_eligible_at"] is None or isinstance(state["next_eligible_at"], str))

        exported = runtime.export_state()
        self.assertEqual(exported["state"]["reentry_allowed"], state["reentry_allowed"])
        self.assertEqual(exported["state"]["next_eligible_at"], state["next_eligible_at"])

    def test_snapshot_carries_declared_participating_system_coalition(self):
        contract, runtime = self.make_runtime()
        self.assertEqual(contract["state_families"]["entrainment"]["participating_systems"], "set<string>")
        declared = set(contract["participating_systems"])

        state = runtime.snapshot()
        self.assertIn("participating_systems", state)
        self.assertIsInstance(state["participating_systems"], (list, tuple, set, frozenset))
        observed = set(state["participating_systems"])
        self.assertTrue(observed.issubset(declared))

        exported = runtime.export_state()
        self.assertEqual(set(exported["state"]["participating_systems"]), observed)

    def test_declared_participating_system_state_roundtrips_without_becoming_a_climax_predicate(self):
        contract, runtime = self.make_runtime()
        record = runtime.export_state()
        record["state"]["participating_systems"] = [
            "attention",
            "relational_context",
        ]

        restored = OrgasmRuntime.restore_state(
            contract,
            record,
            source_revision="sexuality:test-revision",
        )
        state = restored.snapshot()
        self.assertEqual(
            set(state["participating_systems"]),
            {"attention", "relational_context"},
        )
        self.assertEqual(
            restored._organic_climax_eligible(),
            runtime._organic_climax_eligible(),
            "participating-system membership is declared state, not an extra climax gate",
        )

    def test_durable_state_rejects_participating_systems_outside_frozen_vocabulary(self):
        contract, runtime = self.make_runtime()
        record = copy.deepcopy(runtime.export_state())
        record["state"]["participating_systems"] = ["caller_invented_system"]

        with self.assertRaisesRegex(ContractError, r"(?i)(participating|system|vocabulary|declared)"):
            OrgasmRuntime.restore_state(
                contract,
                record,
                source_revision="sexuality:test-revision",
            )


if __name__ == "__main__":
    unittest.main()

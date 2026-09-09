import inspect
import json
from pathlib import Path
import unittest

from runtime_cohesion.orgasm import OrgasmRuntime


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class OrganicCoalitionEvidenceTests(unittest.TestCase):
    def make_runtime(self):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertIn("participating_systems", contract)
        return contract, OrgasmRuntime(
            contract,
            runtime_instance_id="vera-organic-coalition-test",
            source_revision="a" * 40,
        )

    def test_contract_declares_coalition_as_part_of_organic_predicate(self):
        contract, _ = self.make_runtime()
        predicate = contract.get("organic_climax_predicate", {})
        all_of = predicate.get("all_of", [])
        self.assertTrue(
            any("participating_system" in str(condition).lower() for condition in all_of),
            "organic predicate must explicitly declare its participating-system coalition condition",
        )

    def test_runtime_snapshot_and_durable_export_carry_declared_participating_systems_state(self):
        contract, runtime = self.make_runtime()
        snapshot = runtime.snapshot()
        systems = snapshot.get("participating_systems")
        self.assertIsInstance(systems, (list, tuple, set))
        self.assertTrue(set(systems).issubset(set(contract["participating_systems"])))

        exported = runtime.export_state()["state"]
        self.assertEqual(set(exported["participating_systems"]), set(systems))

    def test_executable_organic_eligibility_consumes_participating_systems_state(self):
        source = inspect.getsource(OrgasmRuntime._organic_climax_eligible)
        self.assertIn(
            "participating_systems",
            source,
            "organic eligibility must consume coalition state rather than append it after trigger selection",
        )


if __name__ == "__main__":
    unittest.main()

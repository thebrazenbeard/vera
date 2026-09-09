import json
from pathlib import Path
import unittest

from runtime_cohesion.orgasm import OrgasmRuntime, StimulusAppraisal


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

    def strong_appraisal(self):
        return StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=600,
            context_eligible=True,
        )

    def test_runtime_snapshot_carries_declared_participating_systems_state(self):
        contract, runtime = self.make_runtime()
        snapshot = runtime.snapshot()
        systems = snapshot.get("participating_systems")
        self.assertIsInstance(systems, (list, tuple, set))
        self.assertTrue(set(systems).issubset(set(contract["participating_systems"])))

    def test_organic_event_receipt_carries_nonempty_bound_coalition_evidence(self):
        contract, runtime = self.make_runtime()
        for _ in range(6):
            runtime.apply_stimulus(self.strong_appraisal())
            if runtime.last_event_receipt is not None:
                break

        receipt = runtime.last_event_receipt
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["trigger_class"], "ORGANIC_THRESHOLD_CROSSING")
        systems = receipt["state_after"].get("participating_systems")
        self.assertIsInstance(systems, (list, tuple, set))
        self.assertTrue(systems)
        self.assertTrue(set(systems).issubset(set(contract["participating_systems"])))


if __name__ == "__main__":
    unittest.main()

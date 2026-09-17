import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "architecture" / "VERA_PROJECT_RUNNER_COHERENCE_V1.json"

EXPECTED_PRIMITIVES = {
    "CURRENTNESS_EXHAUSTION_RECEIPT",
    "PROSPECTIVE_FREEZE_RECEIPT",
    "TYPED_EVIDENCE_BOUNDARY",
    "EXECUTION_SUBJECT_MANIFEST",
    "ANTI_TARGET_LEAKAGE_CHAIN",
    "DEPENDENCY_EDGE",
    "EXPERIMENT_LINEAGE",
}


class ProjectRunnerCoherenceV1Tests(unittest.TestCase):
    def load_contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_contract_exposes_exact_reusable_primitive_set(self):
        data = self.load_contract()
        self.assertEqual(set(data["primitives"]), EXPECTED_PRIMITIVES)

    def test_reuse_never_transfers_authority_or_effect_state(self):
        data = self.load_contract()
        self.assertEqual(
            data["authority_ceiling"],
            "PATTERN_AND_DEPENDENCY_COORDINATION_ONLY_NO_CROSS_REPOSITORY_AUTHORITY",
        )
        self.assertFalse(data["promotion_rules"]["pattern_reuse_grants_authority"])
        self.assertFalse(data["promotion_rules"]["dependency_edge_promotes_provider_state"])
        self.assertFalse(data["promotion_rules"]["runner_observation_establishes_runtime_effect"])
        self.assertIn("NOT_MERGE_AUTHORITY", data["non_effects"])
        self.assertIn("NOT_INSTALL_OR_RUNTIME_ACTIVATION", data["non_effects"])

    def test_currentness_exhaustion_requires_inventory_and_per_surface_evidence(self):
        fields = set(
            self.load_contract()["primitives"]["CURRENTNESS_EXHAUSTION_RECEIPT"]["required_fields"]
        )
        self.assertTrue(
            {
                "inventory_owner_subject",
                "required_surface_inventory_digest",
                "surface_receipts",
                "observed_at",
                "overall_completeness",
            }.issubset(fields)
        )

    def test_dependency_edge_keeps_provider_and_consumer_subjects_separate(self):
        edge = self.load_contract()["primitives"]["DEPENDENCY_EDGE"]
        self.assertTrue(
            {
                "provider_artifact_subject",
                "consumer_artifact_subject",
                "edge_class",
                "currentness_policy",
                "promotion_guard",
                "required_or_optional",
            }.issubset(set(edge["required_fields"]))
        )
        self.assertIn("EDGE_NEVER_TRANSFERS_AUTHORITY", edge["invariants"])

    def test_prospective_freeze_requires_execution_frontier(self):
        fields = set(
            self.load_contract()["primitives"]["PROSPECTIVE_FREEZE_RECEIPT"]["required_fields"]
        )
        self.assertTrue(
            {
                "frozen_subject",
                "freeze_artifact_subject",
                "freeze_observed_at",
                "outcome_visibility_frontier",
                "execution_frontier",
            }.issubset(fields)
        )

    def test_anti_target_leakage_covers_producer_payload_projector_and_evaluator(self):
        stages = self.load_contract()["primitives"]["ANTI_TARGET_LEAKAGE_CHAIN"]["required_stages"]
        self.assertEqual(
            stages,
            ["STATE_PRODUCER", "STATE_PAYLOAD", "PROJECTOR_OR_TRANSFORM", "EVALUATOR"],
        )

    def test_experiment_lineage_is_append_only(self):
        lineage = self.load_contract()["primitives"]["EXPERIMENT_LINEAGE"]
        self.assertTrue(lineage["append_only"])
        self.assertFalse(lineage["result_transfer_across_subjects"])


if __name__ == "__main__":
    unittest.main()

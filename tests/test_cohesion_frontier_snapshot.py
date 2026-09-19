from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_cohesion_frontier import (
    load_json_strict,
    validate_frontier,
)


ROOT = Path(__file__).resolve().parents[1]
FRONTIER_PATH = ROOT / "architecture/cohesion/VERA_COHESION_FRONTIER_V0_20260911.json"
REGISTRY_PATH = ROOT / "architecture/cohesion/VERA_COHESION_SOURCE_REGISTRY_V0_20260911.json"


class CohesionFrontierSnapshotTests(unittest.TestCase):
    def frontier(self) -> dict:
        return load_json_strict(FRONTIER_PATH)

    def registry(self) -> dict:
        return load_json_strict(REGISTRY_PATH)

    def test_current_frontier_validates_against_registry_cut(self):
        validate_frontier(self.frontier(), self.registry())

    def test_mutable_input_ids_are_unique(self):
        frontier = self.frontier()
        mutated = deepcopy(frontier)
        mutated["mutable_inputs"].append(deepcopy(mutated["mutable_inputs"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate mutable input id"):
            validate_frontier(mutated, self.registry())

    def test_pr113_registry_and_current_head_are_reconciled(self):
        frontier = self.frontier()
        pr113 = next(item for item in frontier["mutable_inputs"] if item["id"] == "vera-ov-cv-pr113")
        self.assertEqual(pr113["source_registry_head"], pr113["current_observed_head"])
        self.assertEqual(pr113["previous_registry_head"], "132df3fe206600dae83b6e8c158b5822bb3a81e6")
        self.assertFalse(pr113["changed_since_registry"])

    def test_frontier_rejects_registry_head_substitution(self):
        frontier = self.frontier()
        mutated = deepcopy(frontier)
        pr113 = next(item for item in mutated["mutable_inputs"] if item["id"] == "vera-ov-cv-pr113")
        pr113["source_registry_head"] = pr113["previous_registry_head"]
        pr113["changed_since_registry"] = True
        with self.assertRaisesRegex(ValueError, "registry predecessor mismatch"):
            validate_frontier(mutated, self.registry())

    def test_material_drift_requires_reconciliation_before_harvest(self):
        frontier = self.frontier()
        mutated = deepcopy(frontier)
        pr113 = next(item for item in mutated["mutable_inputs"] if item["id"] == "vera-ov-cv-pr113")
        pr113["material_drift"]["reconciliation_required_before_harvest"] = False
        with self.assertRaisesRegex(ValueError, "material drift"):
            validate_frontier(mutated, self.registry())

    def test_runtime_source_drift_cannot_be_classified_as_metadata_only(self):
        frontier = self.frontier()
        mutated = deepcopy(frontier)
        pr113 = next(item for item in mutated["mutable_inputs"] if item["id"] == "vera-ov-cv-pr113")
        pr113["material_drift"]["classification"] = "METADATA_ONLY"
        with self.assertRaisesRegex(ValueError, "runtime source"):
            validate_frontier(mutated, self.registry())

    def test_frontier_cannot_authorize_protected_effects(self):
        frontier = self.frontier()
        mutated = deepcopy(frontier)
        mutated["protected_effects_not_authorized"].remove("MERGE")
        with self.assertRaisesRegex(ValueError, "protected effect ceiling"):
            validate_frontier(mutated, self.registry())

    def test_pr113_latest_bound_freeze_is_explicit(self):
        frontier = self.frontier()
        pr113 = next(item for item in frontier["mutable_inputs"] if item["id"] == "vera-ov-cv-pr113")
        self.assertEqual(
            pr113["current_observed_head"],
            "f7dbc3deeaaaeb46dcf7c7ea6b56a822f253232d",
        )
        self.assertEqual(pr113["material_drift"]["ahead_by_since_overlap_audit"], 10)
        self.assertIn(
            "tests/test_runtime_cohesion_affect_observation_detachment.py",
            pr113["material_drift"]["changed_paths_since_overlap_audit"],
        )
        self.assertIn(
            "architecture/VERA_ORGASM_RUNTIME_BINDING_V1.json",
            pr113["material_drift"]["changed_paths_since_overlap_audit"],
        )
        self.assertEqual(
            pr113["material_drift"]["runtime_generation"],
            "ba6221f56b98be69c3ede1be9e3502eff897ca1a",
        )
        self.assertEqual(
            pr113["material_drift"]["binding_blob"],
            "037883261bd324e8080c323f1d96ff32179780ee",
        )
        self.assertTrue(pr113["material_drift"]["reconciliation_completed"])

    def test_r2_inputs_include_clean_runtime_repair_and_qualification_subject(self):
        frontier = self.frontier()
        by_id = {item["id"]: item for item in frontier["immutable_evidence_inputs"]}
        self.assertEqual(
            by_id["vera-clean-successor-repair-generation"]["commit"],
            "54fef2659f0a8633dcef60cd36b296c37b6fa4b0",
        )
        self.assertEqual(
            by_id["orgasm-qualification-subject"]["blob"],
            "8d754cbcf26367c0d7b074db3787cfe7709a70fb",
        )


if __name__ == "__main__":
    unittest.main()

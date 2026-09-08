from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "architecture" / "VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json"


def load_contract() -> dict:
    with CONTRACT.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class VeraRuntimeEvidenceContractV1Tests(unittest.TestCase):
    def test_lifecycle_is_not_monotonic(self):
        document = load_contract()
        lifecycle = document["lifecycle_evidence"]
        self.assertEqual(
            lifecycle["semantics"],
            "ORTHOGONAL_EVIDENCE_DIMENSIONS_NOT_MONOTONIC_LADDER",
        )
        self.assertIn("regression", lifecycle["regression_rule"].lower())

    def test_repository_summary_is_not_authoritative_lifecycle_proof(self):
        document = load_contract()
        rule = document["lifecycle_evidence"]["authoritative_proof_unit"]["rule"]
        self.assertIn("summary", rule.lower())
        self.assertIn("never sufficient authoritative proof", rule.lower())

    def test_live_context_authority_classes_are_split(self):
        document = load_contract()
        types = {entry["type"] for entry in document["live_context_types"]}
        self.assertEqual(
            types,
            {
                "CURRENT_USER_INSTRUCTION_CORRECTION_AUTHORITY",
                "VERA_CURRENT_SELF_REPORT",
                "LIVE_OBSERVATION_AND_TASK_CONTEXT",
            },
        )

    def test_self_report_does_not_inherit_user_authority(self):
        document = load_contract()
        self_report = next(
            entry
            for entry in document["live_context_types"]
            if entry["type"] == "VERA_CURRENT_SELF_REPORT"
        )
        self.assertIn("does not inherit user-instruction authority", self_report["must_not_promote"].lower())

    def test_active_context_uses_observable_surface(self):
        document = load_contract()
        active = document["active_context_semantics"]
        self.assertEqual(active["qualification_term"], "ACTIVE_CONTEXT_SET")
        self.assertIn("retrieved_artifact_set", active["observable_surface"])
        self.assertIn("downstream_leakage_or_stickiness_behavior", active["observable_surface"])
        self.assertIn("do not claim latent model activation", active["epistemic_rule"].lower())

    def test_recall_floor_includes_dependency_and_uncertainty_probe(self):
        document = load_contract()
        predicates = set(document["activation_recall_floor"]["activation_predicates"])
        self.assertIn("registered_known_failure_signature_or_negative_control_trigger", predicates)
        self.assertIn("uncertainty_probe_indicates_possible_material_dependency", predicates)
        self.assertIn(
            "does not authorize warehouse preload",
            document["activation_recall_floor"]["uncertainty_probe"]["anti_bloat_rule"].lower(),
        )

    def test_durable_operational_state_middle_class_exists(self):
        document = load_contract()
        states = document["durable_state_classes"]
        self.assertIn("DURABLE_OPERATIONAL_STATE", states)
        self.assertIn("non_promotion_flag", states["DURABLE_OPERATIONAL_STATE"]["required_fields"])
        self.assertIn("never silently promotes", states["DURABLE_OPERATIONAL_STATE"]["promotion_rule"].lower())

    def test_blind_review_contamination_is_explicit(self):
        document = load_contract()
        self.assertEqual(
            document["provenance"]["blind_review_state"],
            "CURRENT_THIRTEEN_SESSION_CONTAMINATED_FOR_BLIND_GATE",
        )

    def test_go_live_ceiling_keeps_claims_separate(self):
        document = load_contract()
        separate = set(document["go_live_evidence_ceiling"]["still_separate"])
        self.assertEqual(
            separate,
            {
                "MERGE_OR_CANONICAL_SOURCE_STATUS",
                "INSTALLATION",
                "CURRENT_ROUTE_BINDING",
                "RUNTIME_CONSUMPTION",
                "BEHAVIORAL_QUALIFICATION",
                "PHENOMENOLOGY",
            },
        )


if __name__ == "__main__":
    unittest.main()

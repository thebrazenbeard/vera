from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_cohesion_ownership_contract import (
    load_json_strict,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "architecture/cohesion/VERA_COHESION_OWNERSHIP_CONTRACT_V0.json"


class CohesionOwnershipContractTests(unittest.TestCase):
    def contract(self) -> dict:
        return load_json_strict(CONTRACT_PATH)

    def test_current_contract_validates(self):
        validate_contract(self.contract())

    def test_every_decision_class_has_one_implementation_owner(self):
        contract = self.contract()
        owners = [item["decision_class"] for item in contract["ownership"]]
        self.assertEqual(len(owners), len(set(owners)))
        for item in contract["ownership"]:
            self.assertIsInstance(item["implementation_owner"], str)
            self.assertTrue(item["implementation_owner"].strip())

    def test_chronology_cannot_own_semantic_currentness(self):
        contract = self.contract()
        mutated = deepcopy(contract)
        currentness = next(
            item for item in mutated["ownership"]
            if item["decision_class"] == "SEMANTIC_CURRENTNESS_ADMISSION"
        )
        currentness["implementation_owner"] = "vera.temporal"
        with self.assertRaisesRegex(ValueError, "semantic currentness"):
            validate_contract(mutated)

    def test_affect_cannot_own_generic_planning_mutation(self):
        contract = self.contract()
        mutated = deepcopy(contract)
        planning = next(
            item for item in mutated["ownership"]
            if item["decision_class"] == "GENERIC_PLANNING_MUTATION"
        )
        planning["implementation_owner"] = "vera.affect"
        with self.assertRaisesRegex(ValueError, "generic planning mutation"):
            validate_contract(mutated)

    def test_install_current_route_cannot_be_owned_by_technical_source(self):
        contract = self.contract()
        mutated = deepcopy(contract)
        install = next(
            item for item in mutated["ownership"]
            if item["decision_class"] == "INSTALL_CURRENT_ROUTE_QUALIFICATION"
        )
        install["authority_owner"] = "thebrazenbeard/vera"
        with self.assertRaisesRegex(ValueError, "independent operational authority"):
            validate_contract(mutated)

    def test_required_nonpromotion_edges_exist(self):
        contract = self.contract()
        observed = {
            (edge["source_class"], edge["forbidden_promotion"])
            for edge in contract["nonpromotion_edges"]
        }
        required = {
            ("CHRONOLOGY", "SEMANTIC_CURRENTNESS"),
            ("AFFECTIVE_MODULATION", "TRUTH_OR_AUTHORITY"),
            ("MEMORY_CANDIDATE_WEIGHTING", "AUTOBIOGRAPHICAL_ADMISSION"),
            ("HISTORICAL_CONATION", "CURRENT_DESIRE_OR_CONSENT"),
            ("PROVIDER_PERSISTENCE", "CURRENT_SELF_STATE"),
            ("INTERNAL_SUBSYSTEM_CAUSALITY", "PROVIDER_CURRENTNESS"),
            ("PAYLOAD_OR_ROUTING", "REQUESTED_EFFECT_AUTHORITY"),
            ("TECHNICAL_SOURCE", "INSTALL_OR_QUALIFICATION"),
        }
        self.assertTrue(required.issubset(observed))

    def test_private_history_is_not_a_runtime_dependency(self):
        contract = self.contract()
        private = [
            item for item in contract["external_surfaces"]
            if item["class"] == "PRIVATE_HISTORY"
        ]
        self.assertTrue(private)
        self.assertTrue(all(item["runtime_dependency_allowed"] is False for item in private))


if __name__ == "__main__":
    unittest.main()

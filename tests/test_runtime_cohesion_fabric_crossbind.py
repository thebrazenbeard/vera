import copy
import json
from pathlib import Path
import unittest

from scripts.validate_runtime_cohesion_provider_fabric_v1 import (
    validate_operational_support_bindings,
    validate_provider_fabric,
)

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json"
CONTRACT = ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json"
FABRIC = ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json"
RECEIPT = ROOT / "architecture" / "VERA_COHESION_PAIR_RECEIPT_V1.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ProviderFabricCrossBindTests(unittest.TestCase):
    def setUp(self):
        self.index = load(INDEX)
        self.contract = load(CONTRACT)
        self.fabric = load(FABRIC)
        self.receipt = load(RECEIPT)

    def test_current_fabric_crossbinds_cleanly(self):
        self.assertEqual(validate_provider_fabric(self.index, self.contract, self.fabric), [])

    def test_current_operational_support_receipt_crossbinds_cleanly(self):
        self.assertEqual(validate_operational_support_bindings(ROOT, self.receipt), [])

    def test_unknown_evidence_class_is_rejected(self):
        fabric = copy.deepcopy(self.fabric)
        fabric["providers"]["supabase"]["evidence_capability_refs"].append("imaginary_authority")
        errors = validate_provider_fabric(self.index, self.contract, fabric)
        self.assertTrue(any("imaginary_authority" in error for error in errors))

    def test_unknown_route_is_rejected(self):
        fabric = copy.deepcopy(self.fabric)
        fabric["providers"]["google_drive"]["route_refs"] = ["route:does-not-exist"]
        errors = validate_provider_fabric(self.index, self.contract, fabric)
        self.assertTrue(any("route:does-not-exist" in error for error in errors))

    def test_normative_provider_fabric_is_rejected(self):
        fabric = copy.deepcopy(self.fabric)
        fabric["normative_status"] = "NORMATIVE"
        errors = validate_provider_fabric(self.index, self.contract, fabric)
        self.assertTrue(any("NON_NORMATIVE_OPERATIONAL_SUPPORT" in error for error in errors))

    def test_unknown_projection_provider_is_rejected(self):
        fabric = copy.deepcopy(self.fabric)
        fabric["projections"][0]["target_provider"] = "warehouse-of-doom"
        errors = validate_provider_fabric(self.index, self.contract, fabric)
        self.assertTrue(any("warehouse-of-doom" in error for error in errors))

    def test_projection_scope_is_required(self):
        fabric = copy.deepcopy(self.fabric)
        fabric["projections"][0].pop("source_ref_pattern")
        errors = validate_provider_fabric(self.index, self.contract, fabric)
        self.assertTrue(any("source_ref_pattern" in error for error in errors))

    def test_event_instance_binding_global_rule_is_required(self):
        fabric = copy.deepcopy(self.fabric)
        fabric["global_rules"].pop("event_instance_binding")
        errors = validate_provider_fabric(self.index, self.contract, fabric)
        self.assertTrue(any("event_instance_binding" in error for error in errors))

    def test_unknown_event_selector_token_is_rejected(self):
        fabric = copy.deepcopy(self.fabric)
        fabric["projections"][0]["target_event_selector"] = {"git_ref": "$magic_currentness"}
        errors = validate_provider_fabric(self.index, self.contract, fabric)
        self.assertTrue(any("$magic_currentness" in error for error in errors))

    def test_event_selector_must_be_mapping(self):
        fabric = copy.deepcopy(self.fabric)
        fabric["projections"][0]["target_event_selector"] = ["git_ref", "$source_ref"]
        errors = validate_provider_fabric(self.index, self.contract, fabric)
        self.assertTrue(any("target_event_selector" in error for error in errors))

    def test_dependency_semantics_is_required(self):
        index = copy.deepcopy(self.index)
        index.pop("dependency_semantics")
        errors = validate_provider_fabric(index, self.contract, self.fabric)
        self.assertTrue(any("dependency_semantics" in error for error in errors))

    def test_unknown_hard_prerequisite_domain_is_rejected(self):
        index = copy.deepcopy(self.index)
        index["dependency_semantics"]["hard_prerequisite_domains"].append("UNKNOWN_GOVERNING_DOMAIN")
        errors = validate_provider_fabric(index, self.contract, self.fabric)
        self.assertTrue(any("UNKNOWN_GOVERNING_DOMAIN" in error for error in errors))

    def test_current_hard_prerequisite_domains_have_declared_incoming_edges(self):
        index = copy.deepcopy(self.index)
        index["dependency_semantics"]["hard_prerequisite_domains"].append("VISUAL_SELF_REPRESENTATION")
        errors = validate_provider_fabric(index, self.contract, self.fabric)
        self.assertTrue(any("VISUAL_SELF_REPRESENTATION" in error and "incoming" in error.lower() for error in errors))

    def test_governing_hard_prerequisite_cycle_is_rejected(self):
        index = copy.deepcopy(self.index)
        domains = {row["id"]: row for row in index["domains"]}
        domains["CURRENT_TASK_CORRECTION_PERMISSION_CONSENT"]["dependencies"] = ["CONTROL_AND_GOVERNANCE"]
        errors = validate_provider_fabric(index, self.contract, self.fabric)
        self.assertTrue(any("hard prerequisite" in error.lower() and "cycle" in error.lower() for error in errors))

    def test_wrong_operational_support_blob_is_rejected(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["operational_support"]["runtime_planner_module"]["blob_sha"] = "0" * 40
        errors = validate_operational_support_bindings(ROOT, receipt)
        self.assertTrue(any("runtime_planner_module" in error and "blob" in error.lower() for error in errors))

    def test_missing_operational_support_path_is_rejected(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["operational_support"]["provider_executor"]["path"] = "runtime_cohesion/does-not-exist.py"
        errors = validate_operational_support_bindings(ROOT, receipt)
        self.assertTrue(any("provider_executor" in error and "path" in error.lower() for error in errors))

    def test_operational_support_path_cannot_escape_repository(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["operational_support"]["provider_executor"]["path"] = "../outside.py"
        errors = validate_operational_support_bindings(ROOT, receipt)
        self.assertTrue(any("provider_executor" in error and "repository" in error.lower() for error in errors))


if __name__ == "__main__":
    unittest.main()

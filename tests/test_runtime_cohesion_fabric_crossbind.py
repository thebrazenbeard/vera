import copy
import json
from pathlib import Path
import unittest

from scripts.validate_runtime_cohesion_provider_fabric_v1 import validate_provider_fabric

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json"
CONTRACT = ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json"
FABRIC = ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ProviderFabricCrossBindTests(unittest.TestCase):
    def setUp(self):
        self.index = load(INDEX)
        self.contract = load(CONTRACT)
        self.fabric = load(FABRIC)

    def test_current_fabric_crossbinds_cleanly(self):
        self.assertEqual(validate_provider_fabric(self.index, self.contract, self.fabric), [])

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


if __name__ == "__main__":
    unittest.main()

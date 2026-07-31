from __future__ import annotations

from pathlib import Path
import unittest

from scripts.validate_integration_registry import (
    load_json_strict,
    validate_schema,
    validate_semantics,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/integration_registry"
REGISTRY = ROOT / "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json"
SCHEMA = ROOT / "schemas/vera_integration_registry_v1.schema.json"


def valid_registry():
    return load_json_strict(FIXTURES / "valid.json")


class IntegrationRegistryTests(unittest.TestCase):
    def test_valid_registry_passes(self):
        registry = load_json_strict(REGISTRY)
        schema = load_json_strict(SCHEMA)
        validate_schema(registry, schema)
        validate_semantics(registry)

    def test_duplicate_json_keys_rejected_before_schema(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            load_json_strict(FIXTURES / "duplicate-key.json")

    def test_missing_coordination_owner_rejected(self):
        registry = valid_registry()
        attack = load_json_strict(FIXTURES / "missing-owner.json")
        registry["owners"] = [
            owner for owner in registry["owners"]
            if owner["route"] != attack["remove_route"]
        ]
        with self.assertRaisesRegex(ValueError, "required set"):
            validate_semantics(registry)

    def test_obsolete_route_alias_rejected(self):
        registry = valid_registry()
        attack = load_json_strict(FIXTURES / "obsolete-route.json")
        registry["route_aliases"] = {attack["alias"]: attack["target"]}
        with self.assertRaisesRegex(ValueError, "forbidden as alias"):
            validate_semantics(registry)

    def test_extra_undeclared_field_rejected(self):
        registry = valid_registry()
        registry["owners"][0]["model_says_authorized"] = True
        with self.assertRaisesRegex(ValueError, "Additional properties"):
            validate_schema(registry, load_json_strict(SCHEMA))

    def test_coordination_canonical_memory_eligibility_rejected(self):
        registry = valid_registry()
        coordination = next(
            owner for owner in registry["owners"]
            if owner["route"] == "workstream/coordination"
        )
        coordination["canonical_memory_eligible"] = True
        with self.assertRaisesRegex(ValueError, "operational and non-memory"):
            validate_semantics(registry)

    def test_initiatives_execution_authority_rejected(self):
        registry = valid_registry()
        initiatives = next(
            owner for owner in registry["owners"]
            if owner["route"] == "workstream/initiatives"
        )
        initiatives["execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "execution authority"):
            validate_semantics(registry)

    def test_ci_cannot_supply_merge_or_production_authority(self):
        attack = load_json_strict(FIXTURES / "ci-implies-authority.json")
        registry = valid_registry()
        owner = next(
            item for item in registry["owners"] if item["route"] == attack["route"]
        )
        owner["merge_authority"] = attack["merge_authority"]
        with self.assertRaisesRegex(ValueError, "merge authority"):
            validate_semantics(registry)
        registry = valid_registry()
        owner = next(
            item for item in registry["owners"] if item["route"] == attack["route"]
        )
        owner["production_authority"] = attack["production_authority"]
        with self.assertRaisesRegex(ValueError, "production authority"):
            validate_semantics(registry)

    def test_undeclared_dependency_rejected(self):
        registry = valid_registry()
        registry["owners"][0]["upstream_dependencies"].append(
            "workstream/ghost"
        )
        with self.assertRaisesRegex(ValueError, "undeclared route"):
            validate_semantics(registry)

    def test_model_self_asserted_authority_owner_rejected(self):
        registry = valid_registry()
        registry["owners"][0]["authority_owner"] = "MODEL_SELF_ASSERTION"
        with self.assertRaisesRegex(ValueError, "declared workstream route"):
            validate_semantics(registry)


if __name__ == "__main__":
    unittest.main()

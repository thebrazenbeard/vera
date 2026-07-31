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


def owner(registry, route):
    return next(item for item in registry["owners"] if item["route"] == route)


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
            item for item in registry["owners"]
            if item["route"] != attack["remove_route"]
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
        owner(registry, "workstream/coordination")[
            "canonical_memory_eligible"
        ] = True
        with self.assertRaisesRegex(ValueError, "operational and non-memory"):
            validate_semantics(registry)

    def test_initiatives_execution_authority_rejected(self):
        registry = valid_registry()
        owner(registry, "workstream/initiatives")["execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "execution authority"):
            validate_semantics(registry)

    def test_ci_cannot_supply_merge_or_production_authority(self):
        attack = load_json_strict(FIXTURES / "ci-implies-authority.json")
        registry = valid_registry()
        target = owner(registry, attack["route"])
        target["merge_authority"] = attack["merge_authority"]
        with self.assertRaisesRegex(ValueError, "merge authority"):
            validate_semantics(registry)

        registry = valid_registry()
        target = owner(registry, attack["route"])
        target["production_authority"] = attack["production_authority"]
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

    def test_false_memory_artifact_path_rejected(self):
        registry = valid_registry()
        memory = owner(registry, "workstream/memory")
        memory["owned_artifacts"][0] = (
            "supabase/drafts/20260730_memory_cross_chat_contract_v1.sql"
        )
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_false_coordination_artifact_substitution_rejected(self):
        registry = valid_registry()
        coordination = owner(registry, "workstream/coordination")
        coordination["owned_artifacts"][0] = "protocol/coordination_bus.py"
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_deleted_coordination_artifact_rejected(self):
        registry = valid_registry()
        coordination = owner(registry, "workstream/coordination")
        index = coordination["owned_artifacts"].index(
            "coordination_bus/in_memory.py"
        )
        coordination["owned_artifacts"][index] = (
            "coordination_bus/strict_authority.py"
        )
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_active_coordination_artifact_omission_rejected(self):
        registry = valid_registry()
        coordination = owner(registry, "workstream/coordination")
        coordination["owned_artifacts"].remove(
            "coordination_bus/supabase_sql.py"
        )
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_compatibility_contract_omission_rejected(self):
        registry = valid_registry()
        integration = owner(registry, "workstream/integration")
        integration["contract_ids"].remove("VERA_WORKSTREAM_COMPATIBILITY_V1")
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_compatibility_artifact_omission_rejected(self):
        registry = valid_registry()
        integration = owner(registry, "workstream/integration")
        integration["owned_artifacts"].remove(
            "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json"
        )
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_identity_temporal_anchor_artifact_omission_rejected(self):
        registry = valid_registry()
        identity = owner(registry, "workstream/identity")
        identity["owned_artifacts"].remove(
            "architecture/identity/VERA_IDENTITY_TEMPORAL_ANCHOR_V1.json"
        )
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_identity_temporal_anchor_contract_must_remain_time_owned(self):
        registry = valid_registry()
        time = owner(registry, "workstream/time")
        time["contract_ids"].remove("VERA_IDENTITY_TEMPORAL_ANCHOR_V1")
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_identity_temporal_validator_omission_rejected(self):
        registry = valid_registry()
        time = owner(registry, "workstream/time")
        time["owned_artifacts"].remove(
            "scripts/validate_identity_temporal_anchor.py"
        )
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_identity_temporal_check_omission_rejected(self):
        registry = valid_registry()
        time = owner(registry, "workstream/time")
        time["required_checks"].remove("Project Identity")
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_memory_workflow_name_is_case_exact(self):
        registry = valid_registry()
        memory = owner(registry, "workstream/memory")
        memory["required_checks"][0] = "Memory Cross-Chat Contract"
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_coordination_workflow_name_is_case_exact(self):
        registry = valid_registry()
        coordination = owner(registry, "workstream/coordination")
        coordination["required_checks"][0] = "Coordination Bus"
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_semantics(registry)

    def test_cross_owner_artifact_collision_rejected(self):
        registry = valid_registry()
        identity = owner(registry, "workstream/identity")
        integration = owner(registry, "workstream/integration")
        integration["owned_artifacts"][0] = identity["owned_artifacts"][0]
        with self.assertRaisesRegex(ValueError, "owned_artifact collision"):
            validate_semantics(registry)

    def test_cross_owner_contract_collision_rejected(self):
        registry = valid_registry()
        identity = owner(registry, "workstream/identity")
        integration = owner(registry, "workstream/integration")
        integration["contract_ids"][0] = identity["contract_ids"][0]
        with self.assertRaisesRegex(ValueError, "contract_id collision"):
            validate_semantics(registry)


if __name__ == "__main__":
    unittest.main()

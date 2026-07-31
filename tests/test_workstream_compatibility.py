from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.validate_integration_registry import load_json_strict
from scripts.validate_workstream_compatibility import (
    validate_schema,
    validate_semantics,
)

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json"
SCHEMA_PATH = ROOT / "schemas/vera_workstream_compatibility_v1.schema.json"
REGISTRY_PATH = ROOT / "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json"


def matrix():
    return load_json_strict(MATRIX_PATH)


def schema():
    return load_json_strict(SCHEMA_PATH)


def registry():
    return load_json_strict(REGISTRY_PATH)


def interface(document, interface_id):
    return next(item for item in document["interfaces"] if item["interface_id"] == interface_id)


def assertion(document, route):
    return next(item for item in document["ownership_assertions"] if item["route"] == route)


class WorkstreamCompatibilityTests(unittest.TestCase):
    def test_valid_matrix_passes(self):
        document = matrix()
        validate_schema(document, schema())
        validate_semantics(document, registry())

    def test_duplicate_json_keys_rejected_before_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"matrix_id":"A","matrix_id":"B"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                load_json_strict(path)

    def test_live_status_prose_field_rejected(self):
        document = matrix()
        document["live_status"] = "all green, allegedly"
        with self.assertRaisesRegex(ValueError, "Additional properties"):
            validate_schema(document, schema())

    def test_obsolete_route_rejected(self):
        document = matrix()
        document["interfaces"][0]["source_route"] = "workstream/initiative"
        with self.assertRaisesRegex(ValueError, "not one of"):
            validate_schema(document, schema())

    def test_same_source_and_target_rejected(self):
        document = matrix()
        document["interfaces"][0]["target_route"] = document["interfaces"][0]["source_route"]
        with self.assertRaisesRegex(ValueError, "may not target its source"):
            validate_semantics(document, registry())

    def test_missing_required_interface_pair_rejected(self):
        document = matrix()
        document["interfaces"] = document["interfaces"][:-1]
        with self.assertRaisesRegex(ValueError, "interface pair coverage"):
            validate_semantics(document, registry())

    def test_duplicate_directional_interface_pair_rejected(self):
        document = matrix()
        duplicate = deepcopy(document["interfaces"][0])
        duplicate["interface_id"] = "VERA-IFACE-011"
        duplicate["required_adapter"] = "DUPLICATE_PAIR_ADAPTER_V1"
        duplicate["findings"][0]["finding_id"] = "VIC-F011"
        document["interfaces"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "duplicates directional interface pair"):
            validate_semantics(document, registry())

    def test_duplicate_interface_id_rejected(self):
        document = matrix()
        document["interfaces"][1]["interface_id"] = document["interfaces"][0]["interface_id"]
        with self.assertRaisesRegex(ValueError, "duplicate interface_id"):
            validate_semantics(document, registry())

    def test_duplicate_adapter_rejected(self):
        document = matrix()
        document["interfaces"][1]["required_adapter"] = document["interfaces"][0]["required_adapter"]
        with self.assertRaisesRegex(ValueError, "duplicate adapter"):
            validate_semantics(document, registry())

    def test_duplicate_finding_id_rejected(self):
        document = matrix()
        document["interfaces"][1]["findings"][0]["finding_id"] = document["interfaces"][0]["findings"][0]["finding_id"]
        with self.assertRaisesRegex(ValueError, "duplicate finding_id"):
            validate_semantics(document, registry())

    def test_source_contract_must_belong_to_source(self):
        document = matrix()
        document["interfaces"][0]["source_contract_ids"] = ["VERA_COORDINATION_BUS_V1"]
        with self.assertRaisesRegex(ValueError, "source contract"):
            validate_semantics(document, registry())

    def test_target_contract_must_belong_to_target(self):
        document = matrix()
        document["interfaces"][0]["target_contract_ids"] = ["VERA_MEMORY_CROSS_CHAT_CONTRACT_V1"]
        with self.assertRaisesRegex(ValueError, "target contract"):
            validate_semantics(document, registry())

    def test_identity_time_anchor_contract_omission_rejected(self):
        document = matrix()
        interface(document, "VERA-IFACE-001")["target_contract_ids"].remove(
            "VERA_IDENTITY_TEMPORAL_ANCHOR_V1"
        )
        with self.assertRaisesRegex(ValueError, "temporal-anchor binding"):
            validate_semantics(document, registry())

    def test_identity_time_anchor_artifact_omission_rejected(self):
        document = matrix()
        interface(document, "VERA-IFACE-001")["acceptance_evidence"]["source_artifacts"].remove(
            "architecture/identity/VERA_IDENTITY_TEMPORAL_ANCHOR_V1.json"
        )
        with self.assertRaisesRegex(ValueError, "temporal-anchor binding"):
            validate_semantics(document, registry())

    def test_identity_time_validator_omission_rejected(self):
        document = matrix()
        interface(document, "VERA-IFACE-001")["acceptance_evidence"]["target_artifacts"].remove(
            "scripts/validate_identity_temporal_anchor.py"
        )
        with self.assertRaisesRegex(ValueError, "temporal-anchor binding"):
            validate_semantics(document, registry())

    def test_source_artifact_must_belong_to_source(self):
        document = matrix()
        interface(document, "VERA-IFACE-004")["acceptance_evidence"]["source_artifacts"] = ["coordination_bus/contracts.py"]
        with self.assertRaisesRegex(ValueError, "source artifact"):
            validate_semantics(document, registry())

    def test_unregistered_integration_artifact_cannot_self_certify(self):
        document = matrix()
        interface(document, "VERA-IFACE-010")["acceptance_evidence"]["source_artifacts"] = [
            "architecture/integration/UNREGISTERED_ASSURANCE_REPORT.json"
        ]
        with self.assertRaisesRegex(ValueError, "source artifact"):
            validate_semantics(document, registry())

    def test_registered_matrix_cannot_self_certify(self):
        document = matrix()
        interface(document, "VERA-IFACE-010")["acceptance_evidence"]["source_artifacts"] = [
            "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json"
        ]
        with self.assertRaisesRegex(ValueError, "self-referential"):
            validate_semantics(document, registry())

    def test_matrix_validator_cannot_self_certify(self):
        document = matrix()
        interface(document, "VERA-IFACE-010")["acceptance_evidence"]["source_artifacts"] = [
            "scripts/validate_workstream_compatibility.py"
        ]
        with self.assertRaisesRegex(ValueError, "self-referential"):
            validate_semantics(document, registry())

    def test_target_artifact_must_belong_to_target(self):
        document = matrix()
        interface(document, "VERA-IFACE-004")["acceptance_evidence"]["target_artifacts"] = ["protocol/initiative_kernel.py"]
        with self.assertRaisesRegex(ValueError, "target artifact"):
            validate_semantics(document, registry())

    def test_check_must_belong_to_an_endpoint(self):
        document = matrix()
        interface(document, "VERA-IFACE-004")["acceptance_evidence"]["required_checks"] = ["Initiative kernel"]
        with self.assertRaisesRegex(ValueError, "not declared by either endpoint"):
            validate_semantics(document, registry())

    def test_authority_owner_substitution_rejected(self):
        document = matrix()
        interface(document, "VERA-IFACE-006")["authority_owner"] = "workstream/initiatives"
        with self.assertRaisesRegex(ValueError, "authority owner must be workstream/identity"):
            validate_semantics(document, registry())

    def test_permission_owner_substitution_rejected(self):
        document = matrix()
        interface(document, "VERA-IFACE-004")["permission_owner"] = "workstream/time"
        with self.assertRaisesRegex(ValueError, "permission owner must be workstream/memory"):
            validate_semantics(document, registry())

    def test_initiatives_cannot_claim_execution(self):
        document = matrix()
        assertion(document, "workstream/initiatives")["execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "may not claim execution"):
            validate_semantics(document, registry())

    def test_initiatives_interface_requires_abstention_and_no_execution(self):
        document = matrix()
        interface(document, "VERA-IFACE-006")["capabilities"] = ["ACTION_SELECTION"]
        with self.assertRaisesRegex(ValueError, "selection, abstention, and no-execution"):
            validate_semantics(document, registry())

    def test_coordination_cannot_transfer_canonical_memory(self):
        document = matrix()
        interface(document, "VERA-IFACE-007")["canonical_memory_transfer"] = True
        with self.assertRaisesRegex(ValueError, "silently promote"):
            validate_semantics(document, registry())

    def test_coordination_to_memory_requires_operational_boundary(self):
        document = matrix()
        interface(document, "VERA-IFACE-007")["capabilities"] = ["OPERATIONAL_EVENT_REFERENCE"]
        with self.assertRaisesRegex(ValueError, "operational and non-promoting"):
            validate_semantics(document, registry())

    def test_integration_cannot_claim_component_semantics(self):
        document = matrix()
        interface(document, "VERA-IFACE-010")["capabilities"] = ["COMPATIBILITY_FINDING"]
        with self.assertRaisesRegex(ValueError, "disclaim component-semantic ownership"):
            validate_semantics(document, registry())

    def test_ci_cannot_supply_merge_authority(self):
        document = matrix()
        document["merge_authority"] = "GREEN_CI"
        with self.assertRaisesRegex(ValueError, "merge authority"):
            validate_semantics(document, registry())

    def test_registry_head_binding_is_immutable(self):
        document = matrix()
        document["registry_source_head"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "accepted immutable registry head"):
            validate_semantics(document, registry())

    def test_owner_domain_cannot_be_reassigned(self):
        document = matrix()
        assertion(document, "workstream/time")["owns"] = ["CANONICAL_MEMORY"]
        with self.assertRaisesRegex(ValueError, "ownership domain"):
            validate_semantics(document, registry())

    def test_required_negative_boundary_cannot_be_removed(self):
        document = matrix()
        assertion(document, "workstream/coordination")["does_not_own"] = ["MERGE_AUTHORITY"]
        with self.assertRaisesRegex(ValueError, "negative ownership boundary"):
            validate_semantics(document, registry())

    def test_registry_classification_mismatch_rejected(self):
        document = matrix()
        assertion(document, "workstream/memory")["canonical_memory_eligible"] = False
        with self.assertRaisesRegex(ValueError, "classification differs"):
            validate_semantics(document, registry())

    def test_matrix_does_not_mutate_registry_fixture(self):
        source = registry()
        snapshot = deepcopy(source)
        validate_semantics(matrix(), source)
        self.assertEqual(source, snapshot)


if __name__ == "__main__":
    unittest.main()

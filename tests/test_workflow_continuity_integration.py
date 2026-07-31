from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_integration_registry import load_json_strict
from scripts.validate_workflow_continuity_integration import (
    CLASSIFICATION_VALIDATOR,
    WORKFLOW_ARTIFACTS,
    WORKFLOW_CONTRACT,
    validate_workflow_continuity_integration,
)


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json"
REGISTRY_PATH = ROOT / "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json"


def matrix():
    return load_json_strict(MATRIX_PATH)


def registry():
    return load_json_strict(REGISTRY_PATH)


def owner(document, route):
    return next(item for item in document["owners"] if item["route"] == route)


def interface(document, interface_id):
    return next(
        item for item in document["interfaces"]
        if item["interface_id"] == interface_id
    )


class WorkflowContinuityIntegrationTests(unittest.TestCase):
    def test_current_inventory_validates(self):
        validate_workflow_continuity_integration(matrix(), registry(), ROOT)

    def test_owner_contract_omission_rejected(self):
        source = registry()
        owner(source, "workstream/identity")["contract_ids"].remove(WORKFLOW_CONTRACT)
        with self.assertRaisesRegex(ValueError, "omits governed workflow-continuity contract"):
            validate_workflow_continuity_integration(matrix(), source, ROOT)

    def test_each_canonical_artifact_omission_rejected(self):
        for artifact in sorted(WORKFLOW_ARTIFACTS):
            with self.subTest(artifact=artifact):
                source = registry()
                owner(source, "workstream/identity")["owned_artifacts"].remove(artifact)
                with self.assertRaisesRegex(
                    ValueError, "omits governed workflow-continuity artifacts"
                ):
                    validate_workflow_continuity_integration(matrix(), source, ROOT)

    def test_classification_validator_omission_rejected(self):
        source = registry()
        owner(source, "workstream/identity")["owned_artifacts"].remove(
            CLASSIFICATION_VALIDATOR
        )
        with self.assertRaisesRegex(ValueError, "classification validator"):
            validate_workflow_continuity_integration(matrix(), source, ROOT)

    def test_memory_interface_contract_omission_rejected(self):
        document = matrix()
        interface(document, "VERA-IFACE-002")["source_contract_ids"].remove(
            WORKFLOW_CONTRACT
        )
        with self.assertRaisesRegex(ValueError, "VERA-IFACE-002 omits"):
            validate_workflow_continuity_integration(document, registry(), ROOT)

    def test_initiatives_interface_validator_omission_rejected(self):
        document = matrix()
        interface(document, "VERA-IFACE-003")["acceptance_evidence"][
            "source_artifacts"
        ].remove("scripts/validate_governed_workflow_continuity.py")
        with self.assertRaisesRegex(ValueError, "VERA-IFACE-003 omits"):
            validate_workflow_continuity_integration(document, registry(), ROOT)

    def test_coordination_user_courier_evidence_omission_rejected(self):
        document = matrix()
        interface(document, "VERA-IFACE-009")["capabilities"].remove(
            "USER_COURIER_AVOIDANCE"
        )
        with self.assertRaisesRegex(ValueError, "coordination evidence"):
            validate_workflow_continuity_integration(document, registry(), ROOT)

    def test_controller_return_contract_omission_rejected(self):
        document = matrix()
        interface(document, "VERA-IFACE-010")["target_contract_ids"].remove(
            WORKFLOW_CONTRACT
        )
        with self.assertRaisesRegex(ValueError, "VERA-IFACE-010 omits"):
            validate_workflow_continuity_integration(document, registry(), ROOT)

    def test_canonical_memory_transfer_remains_forbidden(self):
        document = matrix()
        interface(document, "VERA-IFACE-002")["canonical_memory_transfer"] = True
        with self.assertRaisesRegex(ValueError, "canonical memory"):
            validate_workflow_continuity_integration(document, registry(), ROOT)

    def test_stale_registry_digest_remains_rejected(self):
        source = deepcopy(registry())
        source["lifecycle_status"] = "STALE_MUTATION"
        with self.assertRaisesRegex(ValueError, "active registry digest"):
            validate_workflow_continuity_integration(matrix(), source, ROOT)


if __name__ == "__main__":
    unittest.main()

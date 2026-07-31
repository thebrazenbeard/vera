from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_integration_registry import load_json_strict
from scripts.validate_workflow_continuity_integration import (
    PROJECT_IDENTITY_CHECK,
    REQUIRED_IDENTITY_ARTIFACTS,
    REQUIRED_INTERFACE_ARTIFACTS,
    WORKFLOW_CONTRACT,
    validate_binding,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json"
MATRIX_PATH = ROOT / "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json"


def registry() -> dict:
    return load_json_strict(REGISTRY_PATH)


def matrix() -> dict:
    return load_json_strict(MATRIX_PATH)


def owner(document: dict, route: str) -> dict:
    return next(item for item in document["owners"] if item["route"] == route)


def interface(document: dict, interface_id: str) -> dict:
    return next(
        item for item in document["interfaces"]
        if item["interface_id"] == interface_id
    )


class WorkflowContinuityIntegrationTests(unittest.TestCase):
    def test_current_binding_passes(self):
        validate_binding(matrix(), registry())

    def test_contract_omission_is_rejected(self):
        source = registry()
        owner(source, "workstream/identity")["contract_ids"].remove(
            WORKFLOW_CONTRACT
        )
        with self.assertRaisesRegex(ValueError, "omits governed workflow-continuity contract"):
            validate_binding(matrix(), source)

    def test_each_identity_artifact_omission_is_rejected(self):
        for artifact in sorted(REQUIRED_IDENTITY_ARTIFACTS):
            with self.subTest(artifact=artifact):
                source = registry()
                owner(source, "workstream/identity")["owned_artifacts"].remove(artifact)
                with self.assertRaisesRegex(ValueError, "omits governed workflow-continuity artifacts"):
                    validate_binding(matrix(), source)

    def test_each_interface_contract_omission_is_rejected(self):
        for interface_id in ("VERA-IFACE-002", "VERA-IFACE-003"):
            with self.subTest(interface_id=interface_id):
                source = matrix()
                interface(source, interface_id)["source_contract_ids"].remove(
                    WORKFLOW_CONTRACT
                )
                with self.assertRaisesRegex(ValueError, "omits governed workflow-continuity contract"):
                    validate_binding(source, registry())

    def test_each_interface_artifact_omission_is_rejected(self):
        for interface_id in ("VERA-IFACE-002", "VERA-IFACE-003"):
            for artifact in sorted(REQUIRED_INTERFACE_ARTIFACTS):
                with self.subTest(interface_id=interface_id, artifact=artifact):
                    source = matrix()
                    interface(source, interface_id)["acceptance_evidence"][
                        "source_artifacts"
                    ].remove(artifact)
                    with self.assertRaisesRegex(ValueError, "omits governed workflow-continuity evidence"):
                        validate_binding(source, registry())

    def test_project_identity_check_omission_is_rejected(self):
        source_registry = registry()
        owner(source_registry, "workstream/identity")["required_checks"].remove(
            PROJECT_IDENTITY_CHECK
        )
        with self.assertRaisesRegex(ValueError, "omits Project Identity workflow evidence"):
            validate_binding(matrix(), source_registry)

        source_matrix = matrix()
        interface(source_matrix, "VERA-IFACE-002")["acceptance_evidence"][
            "required_checks"
        ].remove(PROJECT_IDENTITY_CHECK)
        with self.assertRaisesRegex(ValueError, "omits Project Identity workflow evidence"):
            validate_binding(source_matrix, registry())

    def test_authority_and_transfer_promotions_are_rejected(self):
        for interface_id in ("VERA-IFACE-002", "VERA-IFACE-003"):
            source = matrix()
            interface(source, interface_id)["execution_authorized"] = True
            with self.assertRaisesRegex(ValueError, "may not grant execution authority"):
                validate_binding(source, registry())

            source = matrix()
            interface(source, interface_id)["canonical_memory_transfer"] = True
            with self.assertRaisesRegex(ValueError, "may not grant canonical-memory transfer"):
                validate_binding(source, registry())


if __name__ == "__main__":
    unittest.main()

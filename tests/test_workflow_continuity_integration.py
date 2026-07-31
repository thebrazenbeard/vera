from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_integration_registry import load_json_strict
from scripts.validate_workflow_continuity_integration import (
    CLASSIFICATION_VALIDATOR,
    INTERFACE_BINDINGS,
    PROJECT_IDENTITY_CHECK,
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
        with self.assertRaisesRegex(
            ValueError,
            "omits governed workflow-continuity contract|canonical source intent",
        ):
            validate_workflow_continuity_integration(matrix(), source, ROOT)

    def test_each_canonical_artifact_omission_rejected(self):
        for artifact in sorted(WORKFLOW_ARTIFACTS):
            with self.subTest(artifact=artifact):
                source = registry()
                owner(source, "workstream/identity")["owned_artifacts"].remove(artifact)
                with self.assertRaisesRegex(
                    ValueError,
                    "omits governed workflow-continuity artifacts|canonical source intent",
                ):
                    validate_workflow_continuity_integration(matrix(), source, ROOT)

    def test_classification_validator_omission_rejected(self):
        source = registry()
        owner(source, "workstream/identity")["owned_artifacts"].remove(
            CLASSIFICATION_VALIDATOR
        )
        with self.assertRaisesRegex(
            ValueError,
            "classification validator|canonical source intent",
        ):
            validate_workflow_continuity_integration(matrix(), source, ROOT)

    def test_each_bound_interface_contract_omission_rejected(self):
        for interface_id, binding in INTERFACE_BINDINGS.items():
            contract_field = binding["contract_field"]
            if contract_field is None:
                continue
            with self.subTest(interface_id=interface_id):
                document = matrix()
                interface(document, interface_id)[contract_field].remove(
                    WORKFLOW_CONTRACT
                )
                with self.assertRaisesRegex(ValueError, f"{interface_id} omits"):
                    validate_workflow_continuity_integration(document, registry(), ROOT)

    def test_each_bound_interface_artifact_omission_rejected(self):
        for interface_id, binding in INTERFACE_BINDINGS.items():
            artifact_role = binding["artifact_role"]
            if artifact_role is None:
                continue
            for artifact in sorted(binding["artifacts"]):
                with self.subTest(interface_id=interface_id, artifact=artifact):
                    document = matrix()
                    interface(document, interface_id)["acceptance_evidence"][
                        artifact_role
                    ].remove(artifact)
                    with self.assertRaisesRegex(ValueError, f"{interface_id} omits"):
                        validate_workflow_continuity_integration(
                            document, registry(), ROOT
                        )

    def test_every_required_capability_omission_rejected(self):
        for interface_id, binding in INTERFACE_BINDINGS.items():
            for capability in sorted(binding["capabilities"]):
                with self.subTest(interface_id=interface_id, capability=capability):
                    document = matrix()
                    interface(document, interface_id)["capabilities"].remove(capability)
                    with self.assertRaisesRegex(ValueError, "capability set differs"):
                        validate_workflow_continuity_integration(
                            document, registry(), ROOT
                        )

    def test_unreviewed_capability_addition_rejected(self):
        for interface_id in INTERFACE_BINDINGS:
            with self.subTest(interface_id=interface_id):
                document = matrix()
                interface(document, interface_id)["capabilities"].append(
                    "UNREVIEWED_CAPABILITY"
                )
                with self.assertRaisesRegex(ValueError, "capability set differs"):
                    validate_workflow_continuity_integration(document, registry(), ROOT)

    def test_project_identity_evidence_omission_rejected(self):
        source_registry = registry()
        owner(source_registry, "workstream/identity")["required_checks"].remove(
            PROJECT_IDENTITY_CHECK
        )
        with self.assertRaisesRegex(ValueError, "Project Identity workflow evidence"):
            validate_workflow_continuity_integration(
                matrix(), source_registry, ROOT
            )

        for interface_id, binding in INTERFACE_BINDINGS.items():
            if not binding["requires_project_identity"]:
                continue
            with self.subTest(interface_id=interface_id):
                document = matrix()
                interface(document, interface_id)["acceptance_evidence"][
                    "required_checks"
                ].remove(PROJECT_IDENTITY_CHECK)
                with self.assertRaisesRegex(
                    ValueError, "Project Identity workflow evidence"
                ):
                    validate_workflow_continuity_integration(
                        document, registry(), ROOT
                    )

    def test_route_drift_rejected(self):
        for interface_id, binding in INTERFACE_BINDINGS.items():
            with self.subTest(interface_id=interface_id, role="source"):
                document = matrix()
                interface(document, interface_id)["source_route"] = "workstream/time"
                with self.assertRaisesRegex(ValueError, "source must remain"):
                    validate_workflow_continuity_integration(
                        document, registry(), ROOT
                    )
            with self.subTest(interface_id=interface_id, role="target"):
                document = matrix()
                interface(document, interface_id)["target_route"] = "workstream/time"
                with self.assertRaisesRegex(ValueError, "target must remain"):
                    validate_workflow_continuity_integration(
                        document, registry(), ROOT
                    )

    def test_execution_and_canonical_transfer_promotions_rejected(self):
        for interface_id in INTERFACE_BINDINGS:
            with self.subTest(interface_id=interface_id, field="execution"):
                document = matrix()
                interface(document, interface_id)["execution_authorized"] = True
                with self.assertRaisesRegex(ValueError, "execution authority"):
                    validate_workflow_continuity_integration(
                        document, registry(), ROOT
                    )
            with self.subTest(interface_id=interface_id, field="canonical_memory"):
                document = matrix()
                interface(document, interface_id)["canonical_memory_transfer"] = True
                with self.assertRaisesRegex(ValueError, "canonical memory"):
                    validate_workflow_continuity_integration(
                        document, registry(), ROOT
                    )

    def test_stale_registry_digest_remains_rejected(self):
        source = deepcopy(registry())
        source["lifecycle_status"] = "STALE_MUTATION"
        with self.assertRaisesRegex(ValueError, "active registry digest"):
            validate_workflow_continuity_integration(matrix(), source, ROOT)


if __name__ == "__main__":
    unittest.main()

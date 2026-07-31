from __future__ import annotations

from pathlib import Path
import unittest

from scripts.validate_integration_registry import (
    canonical_json_sha256,
    load_json_strict,
    validate_semantics as validate_registry_semantics,
)
from scripts.validate_workstream_compatibility import (
    validate_semantics as validate_compatibility_semantics,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json"
MATRIX_PATH = ROOT / "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json"
CLASSIFICATION_VALIDATOR = (
    "scripts/validate_identity_temporal_anchor_classification.py"
)


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


class IdentityClassificationIntegrationInventoryTests(unittest.TestCase):
    def test_current_inventory_and_digest_pass(self):
        source_registry = registry()
        source_matrix = matrix()
        self.assertIn(
            CLASSIFICATION_VALIDATOR,
            owner(source_registry, "workstream/identity")["owned_artifacts"],
        )
        self.assertEqual(
            canonical_json_sha256(source_registry),
            source_matrix["active_registry_sha256"],
        )
        validate_registry_semantics(source_registry, ROOT)
        validate_compatibility_semantics(source_matrix, source_registry, ROOT)

    def test_registry_omission_is_rejected(self):
        source_registry = registry()
        owner(source_registry, "workstream/identity")["owned_artifacts"].remove(
            CLASSIFICATION_VALIDATOR
        )
        with self.assertRaisesRegex(ValueError, "canonical source intent"):
            validate_registry_semantics(source_registry, ROOT)

    def test_identity_to_memory_evidence_omission_is_rejected(self):
        source_matrix = matrix()
        interface(source_matrix, "VERA-IFACE-002")["acceptance_evidence"][
            "source_artifacts"
        ].remove(CLASSIFICATION_VALIDATOR)
        with self.assertRaisesRegex(
            ValueError, "omits the Identity temporal-anchor classification validator"
        ):
            validate_compatibility_semantics(source_matrix, registry(), ROOT)

    def test_project_identity_check_is_required_for_classification_evidence(self):
        source_matrix = matrix()
        interface(source_matrix, "VERA-IFACE-002")["acceptance_evidence"][
            "required_checks"
        ].remove("Project Identity")
        with self.assertRaisesRegex(
            ValueError, "omits the Project Identity classification check"
        ):
            validate_compatibility_semantics(source_matrix, registry(), ROOT)

    def test_component_test_and_workflow_are_check_evidence(self):
        identity = owner(registry(), "workstream/identity")
        self.assertNotIn(
            "tests/test_identity_temporal_anchor_classification.py",
            identity["owned_artifacts"],
        )
        self.assertNotIn(
            ".github/workflows/project-identity.yml",
            identity["owned_artifacts"],
        )
        self.assertIn("Project Identity", identity["required_checks"])
        self.assertIn(
            "Project Identity",
            interface(matrix(), "VERA-IFACE-002")["acceptance_evidence"][
                "required_checks"
            ],
        )


if __name__ == "__main__":
    unittest.main()

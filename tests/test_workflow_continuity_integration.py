from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_workflow_continuity_integration import (
    CURRENT_CONTRACT,
    HISTORICAL_CONTRACT,
    OVERLAY_PATH,
    POINTER_PATH,
    REQUIRED_CAPABILITIES,
    validate_workflow_continuity_integration,
)

ROOT = Path(__file__).resolve().parents[1]


class WorkflowContinuityIntegrationTests(unittest.TestCase):
    copied = (
        OVERLAY_PATH,
        POINTER_PATH,
        "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V2.json",
        "architecture/identity/VERA_PROJECT_IDENTITY_V1.json",
        "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json",
        "schemas/vera_governed_workflow_continuity_v2.schema.json",
        "docs/GOVERNED_WORKFLOW_CONTINUITY_V2.md",
        "docs/PROTOCOL_EXECUTION_PRECEDENCE_V2.md",
        "docs/WORKSTREAM_TURN_TAKING_PROTOCOL_V2.md",
        "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json",
        "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json",
    )

    def copy_repo_slice(self, target: Path) -> None:
        for relative in self.copied:
            source = ROOT / relative
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    def mutate(self, target: Path, relative: str, key: str, value: object) -> None:
        path = target / relative
        document = json.loads(path.read_text(encoding="utf-8"))
        document[key] = value
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def test_current_inventory_validates(self) -> None:
        validate_workflow_continuity_integration(ROOT)

    def test_overlay_cannot_fall_back_to_v1(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_repo_slice(target)
            self.mutate(target, OVERLAY_PATH, "current_workflow_contract_id", HISTORICAL_CONTRACT)
            with self.assertRaisesRegex(ValueError, "resolve to V2"):
                validate_workflow_continuity_integration(target)

    def test_pointer_cannot_fall_back_to_v1(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_repo_slice(target)
            self.mutate(target, POINTER_PATH, "current_contract_id", HISTORICAL_CONTRACT)
            with self.assertRaisesRegex(ValueError, "pointer must resolve to V2"):
                validate_workflow_continuity_integration(target)

    def test_v1_must_remain_classified_historical(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_repo_slice(target)
            self.mutate(target, OVERLAY_PATH, "historical_workflow_contract", CURRENT_CONTRACT)
            with self.assertRaisesRegex(ValueError, "historical predecessor"):
                validate_workflow_continuity_integration(target)

    def test_capability_omission_rejected(self) -> None:
        for capability in sorted(REQUIRED_CAPABILITIES):
            with self.subTest(capability=capability), tempfile.TemporaryDirectory() as temp:
                target = Path(temp)
                self.copy_repo_slice(target)
                path = target / OVERLAY_PATH
                document = json.loads(path.read_text(encoding="utf-8"))
                document["required_capabilities"].remove(capability)
                path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "capability set differs"):
                    validate_workflow_continuity_integration(target)

    def test_unreviewed_capability_addition_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_repo_slice(target)
            path = target / OVERLAY_PATH
            document = json.loads(path.read_text(encoding="utf-8"))
            document["required_capabilities"].append("PERMISSION_RECURSION")
            path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "capability set differs"):
                validate_workflow_continuity_integration(target)

    def test_historical_registry_is_evidence_not_current_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_repo_slice(target)
            # V1 identifiers remain inside the historical registry by design. The
            # current overlay must still validate V2 rather than re-promoting them.
            registry = (target / "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json").read_text(encoding="utf-8")
            self.assertIn(HISTORICAL_CONTRACT, registry)
            validate_workflow_continuity_integration(target)

    def test_routing_rule_cannot_allow_v1_repromotion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_repo_slice(target)
            self.mutate(target, OVERLAY_PATH, "routing_rule", "Use whichever workflow contract is most verbose.")
            with self.assertRaisesRegex(ValueError, "forbid V1 semantic re-promotion"):
                validate_workflow_continuity_integration(target)


if __name__ == "__main__":
    unittest.main()

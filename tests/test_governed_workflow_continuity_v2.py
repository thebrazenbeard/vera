from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts/validate_governed_workflow_continuity_v2.py"
SPEC = importlib.util.spec_from_file_location("validate_governed_workflow_continuity_v2", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class GovernedWorkflowContinuityV2Tests(unittest.TestCase):
    artifacts = (
        "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V2.json",
        "architecture/identity/WORKFLOW_CONTINUITY_CURRENT.json",
        "schemas/vera_governed_workflow_continuity_v2.schema.json",
        "architecture/identity/VERA_PROJECT_IDENTITY_V1.json",
        "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json",
        "docs/GOVERNED_WORKFLOW_CONTINUITY_V2.md",
        "docs/PROTOCOL_EXECUTION_PRECEDENCE_V2.md",
        "docs/WORKSTREAM_TURN_TAKING_PROTOCOL_V2.md",
    )

    def copy_artifacts(self, target_root: Path) -> None:
        for relative in self.artifacts:
            source = ROOT / relative
            target = target_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def mutate_json(
        self,
        target_root: Path,
        relative: str,
        mutation: Callable[[dict[str, object]], None],
    ) -> list[str]:
        path = target_root / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        mutation(value)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        return VALIDATOR.validate_contract(target_root)

    def test_current_v2_validates(self) -> None:
        self.assertEqual([], VALIDATOR.validate_contract(ROOT))

    def test_pointer_cannot_fall_back_to_v1(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_artifacts(target)
            errors = self.mutate_json(
                target,
                "architecture/identity/WORKFLOW_CONTINUITY_CURRENT.json",
                lambda value: value.__setitem__("current_contract_id", "VERA_GOVERNED_WORKFLOW_CONTINUITY_V1"),
            )
            self.assertIn("current workflow pointer must resolve to V2", errors)

    def test_specific_instruction_behavior_cannot_be_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_artifacts(target)

            def mutation(value: dict[str, object]) -> None:
                behaviors = value["required_behaviors"]
                assert isinstance(behaviors, list)
                behaviors.remove("HONOR_SPECIFIC_CURRENT_INSTRUCTION_WITHIN_SCOPE")

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn("Protocol V2 required behavior set drifted", errors)

    def test_repository_stewardship_cannot_be_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_artifacts(target)

            def mutation(value: dict[str, object]) -> None:
                behaviors = value["required_behaviors"]
                assert isinstance(behaviors, list)
                behaviors.remove("HONOR_REPOSITORY_LOCAL_STEWARDSHIP")
                value["repository_stewardship_rule"] = "General coordinators always outrank repository stewards."

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn("Protocol V2 required behavior set drifted", errors)
            self.assertIn("Protocol V2 must bind Patrick-designated repository-local stewardship", errors)

    def test_effect_class_collapse_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_artifacts(target)

            def mutation(value: dict[str, object]) -> None:
                classes = value["effect_classes"]
                assert isinstance(classes, list)
                classes[1]["name"] = "PROTECTED_EFFECT"  # type: ignore[index]

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn("Protocol V2 effect classes must be exactly 0/1/2/3 with canonical names", errors)

    def test_shared_writer_stop_cannot_be_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_artifacts(target)

            def mutation(value: dict[str, object]) -> None:
                stops = value["stop_conditions"]
                assert isinstance(stops, list)
                stops.remove("COMPETING_CURRENT_WRITER_ON_SHARED_TARGET")

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn("Protocol V2 hard-stop set drifted", errors)

    def test_steward_boundary_stop_cannot_be_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_artifacts(target)

            def mutation(value: dict[str, object]) -> None:
                stops = value["stop_conditions"]
                assert isinstance(stops, list)
                stops.remove("REPOSITORY_LOCAL_STEWARD_BOUNDARY")

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn("Protocol V2 hard-stop set drifted", errors)

    def test_protected_effect_boundary_remains_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_artifacts(target)

            def mutation(value: dict[str, object]) -> None:
                stops = value["stop_conditions"]
                assert isinstance(stops, list)
                stops.remove("PROTECTED_EFFECT_AUTHORITY_MISSING")

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn("Protocol V2 hard-stop set drifted", errors)

    def test_model_cannot_self_authorize(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_artifacts(target)

            def mutation(value: dict[str, object]) -> None:
                authority = value["authority"]
                assert isinstance(authority, dict)
                authority["model_self_authority"] = True

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn("Protocol V2 authority must remain USER-owned and non-self-authorizing", errors)

    def test_duplicate_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            self.copy_artifacts(target)
            path = target / self.artifacts[0]
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    '  "schema": "VERA_GOVERNED_WORKFLOW_CONTINUITY_V2",',
                    '  "schema": "VERA_GOVERNED_WORKFLOW_CONTINUITY_V2",\n  "schema": "DUPLICATE",',
                    1,
                ),
                encoding="utf-8",
            )
            errors = VALIDATOR.validate_contract(target)
            self.assertTrue(any("duplicate JSON key: schema" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

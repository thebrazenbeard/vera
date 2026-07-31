from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts/validate_governed_workflow_continuity.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_governed_workflow_continuity", VALIDATOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class GovernedWorkflowContinuityTests(unittest.TestCase):
    artifacts = (
        "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V1.json",
        "schemas/vera_governed_workflow_continuity_v1.schema.json",
        "architecture/identity/VERA_PROJECT_IDENTITY_V1.json",
        "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json",
        "docs/GOVERNED_WORKFLOW_CONTINUITY_V1.md",
    )

    def copy_contract(self, target_root: Path) -> None:
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

    def test_current_contract_validates(self) -> None:
        self.assertEqual([], VALIDATOR.validate_contract(ROOT))

    def test_missing_required_behavior_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.copy_contract(target)

            def mutation(contract: dict[str, object]) -> None:
                behaviors = contract["required_behaviors"]
                assert isinstance(behaviors, list)
                behaviors.remove("ROUTE_REVIEWS_WITHOUT_USER_COURIERING")

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn(
                "workflow continuity must contain the exact required behavior set",
                errors,
            )

    def test_missing_hard_stop_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.copy_contract(target)

            def mutation(contract: dict[str, object]) -> None:
                stops = contract["stop_conditions"]
                assert isinstance(stops, list)
                stops.remove("USER_ONLY_AUTHORITY_REQUIRED")

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn(
                "workflow continuity must contain the exact hard-stop set",
                errors,
            )

    def test_user_courier_rule_cannot_be_weakened(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.copy_contract(target)
            errors = self.mutate_json(
                target,
                self.artifacts[0],
                lambda contract: contract.__setitem__(
                    "user_courier_rule", "Ask Patrick to relay every handoff."
                ),
            )
            self.assertIn(
                "workflow continuity must forbid unnecessary user couriering",
                errors,
            )

    def test_safe_advancement_rule_cannot_be_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.copy_contract(target)
            errors = self.mutate_json(
                target,
                self.artifacts[0],
                lambda contract: contract.__setitem__(
                    "self_advancement_rule", "Stop after every bounded step."
                ),
            )
            self.assertIn(
                "workflow continuity must require safe authorized self-advancement",
                errors,
            )

    def test_model_self_authority_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.copy_contract(target)

            def mutation(contract: dict[str, object]) -> None:
                authority = contract["authority"]
                assert isinstance(authority, dict)
                authority["model_self_authority"] = True

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn(
                "workflow continuity cannot grant model self-authority",
                errors,
            )

    def test_behavior_profile_version_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.copy_contract(target)

            def mutation(contract: dict[str, object]) -> None:
                behavior_ref = contract["behavior_profile_ref"]
                assert isinstance(behavior_ref, dict)
                behavior_ref["version"] = "9.9.9"

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertIn(
                "workflow-continuity behavior version does not match canonical profile",
                errors,
            )

    def test_hidden_activity_boundary_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.copy_contract(target)

            def mutation(contract: dict[str, object]) -> None:
                reality = contract["reality_boundary"]
                assert isinstance(reality, dict)
                excluded = reality["does_not_establish"]
                assert isinstance(excluded, list)
                excluded.remove("hidden activity")

            errors = self.mutate_json(target, self.artifacts[0], mutation)
            self.assertTrue(
                any(
                    "workflow continuity reality boundary missing" in error
                    and "hidden activity" in error
                    for error in errors
                )
            )

    def test_duplicate_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.copy_contract(target)
            path = target / self.artifacts[0]
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    '  "schema": "VERA_GOVERNED_WORKFLOW_CONTINUITY_V1",',
                    '  "schema": "VERA_GOVERNED_WORKFLOW_CONTINUITY_V1",\n'
                    '  "schema": "DUPLICATE",',
                    1,
                ),
                encoding="utf-8",
            )
            errors = VALIDATOR.validate_contract(target)
            self.assertTrue(any("duplicate JSON key: schema" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

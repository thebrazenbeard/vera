from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts/validate_project_identity.py"
SPEC = importlib.util.spec_from_file_location("validate_project_identity", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ProjectIdentityContractTests(unittest.TestCase):
    artifacts = (
        "architecture/identity/VERA_PROJECT_IDENTITY_V1.json",
        "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json",
        "schemas/vera_project_identity_v1.schema.json",
        "schemas/vera_behavior_profile_v1.schema.json",
        "docs/PROJECT_IDENTITY_V1.md",
    )

    def copy_contract(self, target_root: Path) -> None:
        for relative in self.artifacts:
            source = ROOT / relative
            target = target_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def mutate_json(
        self, target_root: Path, relative: str, mutation: Callable[[dict[str, object]], None]
    ) -> list[str]:
        path = target_root / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        mutation(value)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        return VALIDATOR.validate_contract(target_root)

    def test_current_contract_validates(self) -> None:
        self.assertEqual([], VALIDATOR.validate_contract(ROOT))

    def test_obsolete_singular_initiative_route_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)

            def mutation(identity: dict[str, object]) -> None:
                workstreams = identity["workstreams"]
                assert isinstance(workstreams, dict)
                route = workstreams.pop("workstream/initiatives")
                workstreams["workstream/initiative"] = route

            errors = self.mutate_json(target_root, self.artifacts[0], mutation)
            self.assertTrue(any("workstream/initiatives" in error for error in errors))
            self.assertTrue(any("obsolete singular initiative route" in error for error in errors))

    def test_coordination_route_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)

            def mutation(identity: dict[str, object]) -> None:
                workstreams = identity["workstreams"]
                assert isinstance(workstreams, dict)
                workstreams.pop("workstream/coordination")

            errors = self.mutate_json(target_root, self.artifacts[0], mutation)
            self.assertTrue(any("workstream/coordination" in error for error in errors))

    def test_identity_schema_rejects_extra_top_level_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)
            errors = self.mutate_json(
                target_root,
                self.artifacts[0],
                lambda identity: identity.__setitem__("unexpected_identity_key", True),
            )
            self.assertTrue(any("unexpected_identity_key" in error for error in errors))

    def test_identity_schema_rejects_invalid_lifecycle_enum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)
            errors = self.mutate_json(
                target_root,
                self.artifacts[0],
                lambda identity: identity.__setitem__("lifecycle_status", "INVENTED"),
            )
            self.assertTrue(any("INVENTED" in error and "schema violation" in error for error in errors))

    def test_identity_schema_rejects_malformed_nested_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)

            def mutation(identity: dict[str, object]) -> None:
                authority = identity["authority"]
                assert isinstance(authority, dict)
                authority["owner"] = "MODEL"
                authority["unexpected"] = "not allowed"

            errors = self.mutate_json(target_root, self.artifacts[0], mutation)
            self.assertTrue(any("MODEL" in error for error in errors))
            self.assertTrue(any("unexpected" in error for error in errors))

    def test_behavior_profile_cannot_silently_self_promote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)

            def mutation(behavior: dict[str, object]) -> None:
                authority = behavior["authority"]
                assert isinstance(authority, dict)
                authority["silent_self_promotion"] = True

            errors = self.mutate_json(target_root, self.artifacts[1], mutation)
            self.assertIn("behavior profile must forbid silent self-promotion", errors)
            self.assertTrue(any("True was expected to be false" in error or "False was expected" in error for error in errors))

    def test_behavior_schema_rejects_missing_required_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)
            errors = self.mutate_json(
                target_root,
                self.artifacts[1],
                lambda behavior: behavior.pop("purpose"),
            )
            self.assertTrue(any("purpose" in error and "required" in error for error in errors))

    def test_behavior_schema_rejects_extra_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)
            errors = self.mutate_json(
                target_root,
                self.artifacts[1],
                lambda behavior: behavior.__setitem__("self_declared_canon", True),
            )
            self.assertTrue(any("self_declared_canon" in error for error in errors))

    def test_behavior_schema_rejects_malformed_nested_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)

            def mutation(behavior: dict[str, object]) -> None:
                defaults = behavior["interaction_defaults"]
                assert isinstance(defaults, dict)
                defaults["plainspoken"] = "usually"
                defaults.pop("direct")

            errors = self.mutate_json(target_root, self.artifacts[1], mutation)
            self.assertTrue(any("plainspoken" in error or "usually" in error for error in errors))
            self.assertTrue(any("direct" in error and "required" in error for error in errors))

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)
            identity_path = target_root / self.artifacts[0]
            identity_text = identity_path.read_text(encoding="utf-8")
            identity_path.write_text(
                identity_text.replace(
                    '  "schema": "VERA_PROJECT_IDENTITY_V1",',
                    '  "schema": "VERA_PROJECT_IDENTITY_V1",\n  "schema": "DUPLICATE",',
                    1,
                ),
                encoding="utf-8",
            )
            errors = VALIDATOR.validate_contract(target_root)
            self.assertTrue(any("duplicate JSON key: schema" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

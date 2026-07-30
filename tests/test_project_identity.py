from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


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
        "docs/PROJECT_IDENTITY_V1.md",
    )

    def copy_contract(self, target_root: Path) -> None:
        for relative in self.artifacts:
            source = ROOT / relative
            target = target_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def test_current_contract_validates(self) -> None:
        self.assertEqual([], VALIDATOR.validate_contract(ROOT))

    def test_obsolete_singular_initiative_route_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)
            identity_path = target_root / self.artifacts[0]
            identity = json.loads(identity_path.read_text(encoding="utf-8"))
            route = identity["workstreams"].pop("workstream/initiatives")
            identity["workstreams"]["workstream/initiative"] = route
            identity_path.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")

            errors = VALIDATOR.validate_contract(target_root)

            self.assertTrue(any("workstream/initiatives" in error for error in errors))
            self.assertTrue(any("obsolete singular initiative route" in error for error in errors))

    def test_behavior_profile_cannot_silently_self_promote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir)
            self.copy_contract(target_root)
            behavior_path = target_root / self.artifacts[1]
            behavior = json.loads(behavior_path.read_text(encoding="utf-8"))
            behavior["authority"]["silent_self_promotion"] = True
            behavior_path.write_text(json.dumps(behavior, indent=2) + "\n", encoding="utf-8")

            errors = VALIDATOR.validate_contract(target_root)

            self.assertIn("behavior profile must forbid silent self-promotion", errors)

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

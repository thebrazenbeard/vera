from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts/validate_identity_temporal_anchor_classification.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_identity_temporal_anchor_classification", VALIDATOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class IdentityTemporalAnchorClassificationTests(unittest.TestCase):
    artifact = "architecture/identity/VERA_IDENTITY_TEMPORAL_ANCHOR_V1.json"

    def copy_contract(self, target_root: Path) -> None:
        source = ROOT / self.artifact
        target = target_root / self.artifact
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    def mutate(
        self,
        target_root: Path,
        mutation: Callable[[dict[str, object]], None],
    ) -> list[str]:
        path = target_root / self.artifact
        value = json.loads(path.read_text(encoding="utf-8"))
        mutation(value)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        return VALIDATOR.validate_contract(target_root)

    def test_current_classification_validates(self) -> None:
        self.assertEqual([], VALIDATOR.validate_contract(ROOT))

    def test_canonical_memory_promotion_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)
            errors = self.mutate(
                root,
                lambda anchor: anchor.__setitem__("canonical_memory_eligible", True),
            )
            self.assertIn(
                "identity temporal anchor must remain ineligible for canonical memory",
                errors,
            )

    def test_instruction_promotion_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)
            errors = self.mutate(
                root,
                lambda anchor: anchor.__setitem__(
                    "instruction_trust", "TRUSTED_INSTRUCTION"
                ),
            )
            self.assertIn(
                "identity temporal anchor must remain DATA_NOT_INSTRUCTION",
                errors,
            )

    def test_unrelated_record_class_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)
            errors = self.mutate(
                root,
                lambda anchor: anchor.__setitem__(
                    "record_class", "CANONICAL_MEMORY"
                ),
            )
            self.assertIn(
                "identity temporal anchor must remain PROJECT_CONFIGURATION",
                errors,
            )

    def test_missing_classification_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.copy_contract(root)
            errors = self.mutate(
                root,
                lambda anchor: anchor.pop("canonical_memory_eligible"),
            )
            self.assertIn(
                "identity temporal anchor must remain ineligible for canonical memory",
                errors,
            )


if __name__ == "__main__":
    unittest.main()

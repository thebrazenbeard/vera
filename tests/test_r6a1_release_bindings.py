from __future__ import annotations

import copy
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_r6a1_release_bindings import ROOT, load_binding, validate


class R6A1ReleaseBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.valid = load_binding()

    def copy_bound_tree(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for entry in self.valid["bindings"]:
            source = ROOT / entry["path"]
            target = root / entry["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return temporary, root

    def test_valid_binding_passes(self) -> None:
        validate(copy.deepcopy(self.valid))

    def test_wrong_source_commit_rejected(self) -> None:
        changed = copy.deepcopy(self.valid)
        changed["source_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source_commit"):
            validate(changed)

    def test_installable_status_rejected(self) -> None:
        changed = copy.deepcopy(self.valid)
        changed["release_status"] = "INSTALLABLE"
        with self.assertRaisesRegex(ValueError, "non-installable replacement candidate"):
            validate(changed)

    def test_installation_authority_rejected(self) -> None:
        changed = copy.deepcopy(self.valid)
        changed["project_file_replacement_authorized"] = True
        with self.assertRaisesRegex(ValueError, "project_file_replacement_authorized"):
            validate(changed)

    def test_unresolved_future_files_rejected(self) -> None:
        changed = copy.deepcopy(self.valid)
        changed["required_future_files"] = ["checksums"]
        with self.assertRaisesRegex(ValueError, "unresolved future files"):
            validate(changed)

    def test_missing_matrix_binding_rejected(self) -> None:
        changed = copy.deepcopy(self.valid)
        changed["bindings"] = [
            item
            for item in changed["bindings"]
            if item["role"] != "workstream_compatibility"
        ]
        with self.assertRaisesRegex(ValueError, "exact set"):
            validate(changed)

    def test_unverified_authority_cannot_be_promoted(self) -> None:
        changed = copy.deepcopy(self.valid)
        changed["authority_provenance"] = "VERIFIED"
        with self.assertRaisesRegex(ValueError, "authority provenance"):
            validate(changed)

    def test_missing_bound_artifact_rejected(self) -> None:
        changed = copy.deepcopy(self.valid)
        changed["bindings"][0]["path"] = "architecture/identity/MISSING.json"
        with self.assertRaisesRegex(ValueError, "missing bound artifact"):
            validate(changed)

    def test_path_traversal_rejected(self) -> None:
        changed = copy.deepcopy(self.valid)
        changed["bindings"][0]["path"] = "../outside.json"
        with self.assertRaisesRegex(ValueError, "invalid binding path"):
            validate(changed)

    def test_declared_blob_substitution_rejected(self) -> None:
        changed = copy.deepcopy(self.valid)
        registry = next(
            item for item in changed["bindings"] if item["role"] == "integration_registry"
        )
        registry["git_blob_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "Git blob SHA"):
            validate(changed)

    def test_bound_byte_mutation_rejected(self) -> None:
        temporary, root = self.copy_bound_tree()
        try:
            compatibility = next(
                item
                for item in self.valid["bindings"]
                if item["role"] == "workstream_compatibility"
            )
            path = root / compatibility["path"]
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Git blob SHA"):
                validate(copy.deepcopy(self.valid), root=root)
        finally:
            temporary.cleanup()

    def test_registry_canonical_digest_substitution_rejected(self) -> None:
        changed = copy.deepcopy(self.valid)
        registry = next(
            item for item in changed["bindings"] if item["role"] == "integration_registry"
        )
        registry["canonical_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "release intent"):
            validate(changed)

    def test_duplicate_json_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text(
                '{"release_id":"a","release_id":"b"}', encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                load_binding(path)

    def test_non_finite_json_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nan.json"
            path.write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-finite"):
                load_binding(path)


if __name__ == "__main__":
    unittest.main()

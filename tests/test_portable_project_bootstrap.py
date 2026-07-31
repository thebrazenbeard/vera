from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_portable_project_bootstrap.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class PortableBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        validator.ROOT = ROOT

    def test_full_package(self) -> None:
        self.assertEqual(validator.main(["--root", str(ROOT)]), 0)

    def test_duplicate_json_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.load_json(path)

    def test_non_finite_json_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nan.json"
            path.write_text('{"a": NaN}', encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.load_json(path)

    def test_exact_command(self) -> None:
        contract = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
        self.assertEqual(contract["command"]["exact"], validator.EXACT_COMMAND)
        self.assertFalse(contract["command"]["parameters_allowed"])
        self.assertFalse(contract["command"]["appended_text_allowed"])

    def test_no_named_chat_dependency(self) -> None:
        contract = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
        prohibited = set(contract["prohibited_dependencies"])
        self.assertTrue({"chat_title", "historical_chat_id", "named_chat_route", "fixed_conversation_alias"}.issubset(prohibited))

    def test_atomic_candidate(self) -> None:
        scaffold = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_SCAFFOLD_MANIFEST_V1.json")
        self.assertEqual(scaffold["atomic_candidate"]["granularity"], "COMPLETE_REPOSITORY_TRANSACTION")
        self.assertTrue(scaffold["atomic_candidate"]["per_file_actions_are_internal"])
        self.assertFalse(scaffold["write_policy"]["sequential_fallback_allowed"])

    def test_archive_separation(self) -> None:
        manifest = validator.load_json(ROOT / "architecture/bootstrap/VERA_BOOTSTRAP_MANIFEST_V1.json")
        self.assertFalse(manifest["archive_policy"]["active_project_bundle_member"])
        self.assertFalse(manifest["archive_policy"]["canonical_memory_eligible"])

    def test_basic_memory_optional(self) -> None:
        contract = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
        self.assertIn("BASIC_MEMORY", contract["capability_policy"]["optional_nonblocking"])

    def test_project_architect_owns_implementation(self) -> None:
        contract = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
        self.assertTrue(contract["authority_contract"]["project_architect_is_implementation_owner"])
        self.assertTrue(contract["authority_contract"]["github_repo_is_support_and_review"])


if __name__ == "__main__":
    unittest.main()

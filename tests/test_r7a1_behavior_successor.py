from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import validate_portable_project_bootstrap as bootstrap
from scripts import validate_r7a1_behavior_successor as successor

bootstrap.TEMPLATE_ID = successor.TEMPLATE_ID
from tests import test_portable_project_bootstrap as base_tests
base_tests.validator.TEMPLATE_ID = successor.TEMPLATE_ID


class R7A1BehaviorSuccessorTests(unittest.TestCase):
    def test_successor_contract(self) -> None:
        receipts = successor.validate_successor(ROOT)
        self.assertEqual(len(receipts), 24)
        self.assertTrue(all(item["result"] == "PASS" and item["skip"] == "false" for item in receipts))

    def test_unique_project_names(self) -> None:
        manifest = successor.load_json(ROOT / bootstrap.MANIFEST_PATH)
        names = [item["filename"] for item in manifest["project_file_bundle"]["files"]]
        self.assertEqual(len(names), 21)
        self.assertEqual(len(set(names)), 21)
        self.assertTrue(all(name.startswith("VERA_R7A1_") for name in names))
        self.assertFalse(any("(1)" in name for name in names))

    def test_retry_policy(self) -> None:
        root = ROOT / successor.RELEASE_DIR
        combined = "\n".join(
            (root / name).read_text(encoding="utf-8")
            for name in ("VERA_R7A1_LAWS.md", "VERA_R7A1_PROJECT_INSTRUCTIONS.md", "VERA_R7A1_RUNTIME.md")
        ).lower()
        for fragment in (
            "same-route retry",
            "independent alternate route",
            "verify commit state",
            "never blindly repeat",
            "attempt timestamp",
        ):
            self.assertIn(fragment, combined)

    def test_current_state_is_manifest_bound_not_obsolete(self) -> None:
        text = (ROOT / successor.RELEASE_DIR / "VERA_R7A1_PROJECT_INSTRUCTIONS.md").read_text(encoding="utf-8")
        self.assertNotIn(successor.OBSOLETE_MAIN_SHA, text)
        self.assertIn(f"main@{successor.SOURCE_BASE_SHA}", text)
        self.assertIn("read GitHub when current repository state is material", text)


def _make_case_test(case_id: str):
    def test(self: R7A1BehaviorSuccessorTests) -> None:
        successor.assert_case_exact(ROOT, case_id)
    test.__name__ = "test_case_" + re.sub(r"[^a-z0-9]+", "_", case_id.lower()).strip("_")
    return test


for _case in successor.EXPECTED_POSITIVE_CASES + successor.EXPECTED_HOSTILE_CASES:
    _method = _make_case_test(_case["id"])
    setattr(R7A1BehaviorSuccessorTests, _method.__name__, _method)


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(base_tests))
    suite.addTests(loader.loadTestsFromTestCase(R7A1BehaviorSuccessorTests))
    return suite
